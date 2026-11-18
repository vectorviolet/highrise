"""Browser saves use JSON/localStorage through pygamine's SaveStore; desktop keeps its
SQLite schema. No SQLite import belongs on the browser startup path. The game-specific
store names also isolate Highrise from Chokepoint on localhost.

The browser gives the game no QUIT when a tab closes, so the board is also saved shortly
after every change (`request_autosave`), not only when the player leaves it.
"""

import logging
from math import isfinite

import pygame

from app.game_persistence import GamePersistenceMixin, GameSettings
from pygamine import SaveStore
from pygamine.util.localization import DEFAULT_LANGUAGE, tr
from ui.ui_scale import DEFAULT_UI_SCALE, UI_SCALES
from util import web

logger = logging.getLogger(__name__)

# How long after a board change the save waits, so a burst of changes is one write.
AUTOSAVE_DELAY_MS = 2000
# How often the open board is checked for changes nobody asked a save for (the payouts).
AUTOSAVE_INTERVAL_MS = 10_000


def _int(value: object, default: int, low: int, high: int | None = None) -> int:
    """`value` held to low..high; `default` if it isn't an int (a hand-edited or damaged save)."""
    if type(value) is not int:
        return default
    return max(low, value) if high is None else min(max(value, low), high)


def _number(value: object, default: float) -> float:
    """`value` if it is a finite number, else `default`."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isfinite(value):
            return value
    return default


class WebPersistenceMixin(GamePersistenceMixin):
    web_save_invalid = False  # a stored save that can't be read: kept until New Game
    _autosave_due: int | None = None
    _autosave_check_at: int | None = None
    _last_saved: dict | None = None
    web_storage_ok = (
        True  # False when the browser blocks localStorage (nothing survives a reload)
    )

    def init_database(self) -> None:
        if not web.is_web():
            super().init_database()
            return
        if not hasattr(self, "web_save"):
            self.web_settings = SaveStore("highrise-settings")
            self.web_save = SaveStore("highrise-save")
            self.web_storage_ok = web.storage_available()
            self._web_settings_data = (
                self.web_settings.load()
            )  # read once, kept current
            if not self._web_settings_data and self.web_settings.exists():
                logger.warning(
                    "The stored browser settings are unreadable; using defaults"
                )

    def load_data(self) -> None:
        if not web.is_web():
            super().load_data()
            return
        self.init_database()
        data = self.web_save.load()  # read once: every part below comes from it
        self.web_save_invalid = self.web_save.exists() and not data
        if self.web_save_invalid:
            logger.warning("The stored browser save is unreadable; keeping it")
        self._web_snapshot = data
        # Nothing below can fail halfway: every value is held to a valid one first.
        self.load_game_data(self.get_game_data())
        self.load_buildings()
        self.load_tasks()
        self._last_saved = self._snapshot()
        self._show_storage_notice()

    def _show_storage_notice(self, unsaved: bool = False) -> None:
        """One notice for everything the player should know about storage: an unreadable save
        that is kept, and progress that will not survive a reload (`unsaved`: a refused write)."""
        keys = ["storage.invalid_save"] if self.web_save_invalid else []
        if unsaved or not self.web_storage_ok:
            keys.append("storage.unavailable")
        web.show_notice("\n".join(tr(key) for key in keys))

    def load_settings(self) -> GameSettings:
        if not web.is_web():
            return super().load_settings()
        data = self._web_settings_data
        scale = data.get("ui_scale")
        language = data.get("language")
        return GameSettings(
            language if isinstance(language, str) else DEFAULT_LANGUAGE,
            False,
            scale if scale in UI_SCALES else DEFAULT_UI_SCALE,
            _number(data.get("master_volume"), 1.0),
        )

    def save_language(self, language: str) -> None:
        if web.is_web():
            self._web_settings_data = self.web_settings.update(language=language)
        else:
            super().save_language(language)

    def save_skip_intro(self, skip_intro: bool) -> None:
        if not web.is_web():
            super().save_skip_intro(skip_intro)

    def save_ui_scale(self, ui_scale: int) -> None:
        if web.is_web():
            self._web_settings_data = self.web_settings.update(ui_scale=ui_scale)
        else:
            super().save_ui_scale(ui_scale)

    def get_game_data(self) -> list[tuple] | None:
        if not web.is_web():
            return super().get_game_data()
        data, settings = self._web_snapshot, self._web_settings_data
        return [
            (
                _int(data.get("age"), 0, 0, self.buildings.max_age_number),
                _int(data.get("size"), 2, 2, self.max_size),
                _int(data.get("money"), self.starting_money, 0),
                _number(settings.get("music_volume"), self.default_music_volume),
                _number(settings.get("sfx_volume"), self.default_sfx_volume),
            )
        ]

    def load_buildings(self) -> None:
        if not web.is_web():
            super().load_buildings()
            return
        self.buildings.clear()
        records = self._web_snapshot.get("buildings")
        taken = set()
        for saved in records if isinstance(records, list) else []:
            if not isinstance(saved, dict):
                continue
            row, column, level = (
                saved.get("row"),
                saved.get("column"),
                saved.get("level"),
            )
            if type(row) is not int or type(column) is not int:
                continue
            if type(level) is not int:
                continue
            if (row, column) not in taken and self._restore_building(
                level,
                row,
                column,
                saved.get("door_side"),
                saved.get("booster") is True,
                _number(saved.get("income_fraction"), 0.0),
            ):
                taken.add((row, column))

    def load_tasks(self) -> None:
        if not web.is_web():
            super().load_tasks()
            return
        data = self._web_snapshot
        done = data.get("tasks_done")
        self.tasks.restore(
            {i for i in done if type(i) is int} if isinstance(done, list) else set(),
            data.get("boost_unlocked") is True,
        )

    def save_audio_settings(self) -> None:
        if not web.is_web():
            super().save_audio_settings()
            return
        self._web_settings_data = self.web_settings.update(
            master_volume=self.audio.master_volume(),
            music_volume=self.audio.music_volume(),
            sfx_volume=self.audio.sfx_volume(),
        )

    def save_game(self) -> None:
        if not web.is_web():
            super().save_game()
            return
        if self.web_save_invalid:
            return  # Only an explicit New Game may replace an unreadable stored save.
        self.buildings.finish_pending_merges()
        data = self._snapshot()
        self.web_save.save(data)
        self._autosave_due = None
        self._last_saved = data
        # SaveStore logs a refused write and returns normally: read it back to know.
        self._show_storage_notice(unsaved=self.web_save.load() != data)

    def _snapshot(self) -> dict:
        """What a save holds, from the live game."""
        assert self.tilemap is not None, "tilemap not loaded yet"
        return {
            "age": self.buildings.age_number,
            "size": self.tilemap.row_count,
            "money": self.player.money,
            "tasks_done": sorted(self.tasks.done),
            "boost_unlocked": self.tasks.boost_unlocked,
            "buildings": [
                {
                    "level": b.level,
                    "row": b.tile.row_number,
                    "column": b.tile.column_number,
                    "door_side": b.door_side,
                    "booster": b.is_booster,
                    "income_fraction": b.income_fraction,
                }
                for b in self.buildings
            ],
        }

    def request_autosave(self) -> None:
        """Saves the board in AUTOSAVE_DELAY_MS (a change inside that wait joins it)."""
        if web.is_web() and self._autosave_due is None:
            self._autosave_due = pygame.time.get_ticks() + AUTOSAVE_DELAY_MS

    def autosave_if_due(self) -> None:
        """Called every frame. While the board is open, every AUTOSAVE_INTERVAL_MS also saves what
        changed without a request (the payouts). Waits out a merge in progress instead of
        cutting it short."""
        now = pygame.time.get_ticks()
        if self._autosave_check_at is None:
            self._autosave_check_at = now + AUTOSAVE_INTERVAL_MS
        elif now >= self._autosave_check_at:
            self._autosave_check_at = now + AUTOSAVE_INTERVAL_MS
            if (
                self.panel_manager.current_panel == "game"
                and not self.web_save_invalid
                and not self.buildings.is_busy()
                and self._snapshot() != self._last_saved
            ):
                self._autosave_due = now
        if (
            self._autosave_due is not None
            and now >= self._autosave_due
            and not self.buildings.is_busy()
        ):
            self.save_game()

    def delete_data(self) -> None:
        if not web.is_web():
            super().delete_data()
            return
        self.web_save.delete()
        self._autosave_due = None
        if self.web_save_invalid:
            self.web_save_invalid = False
            self._apply_web_rows()
        self._show_storage_notice()
