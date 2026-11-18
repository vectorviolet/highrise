"""Browser saves use JSON/localStorage; desktop keeps its existing SQLite schema.

No SQLite import belongs on the browser startup path. Each completed save is
one localStorage write, including buildings, fractions and age-task progress.
The game-specific store names also isolate Highrise from Chokepoint on localhost.
"""

from app.game_persistence import GamePersistenceMixin, GameSettings
from app.browser_store import BrowserStore, WriteOutcome
from app.web_save_data import InvalidWebSave, validate_snapshot, volume_or_default
from pygamine.util.localization import DEFAULT_LANGUAGE, tr
from ui.ui_scale import DEFAULT_UI_SCALE, UI_SCALES
from util import web


class WebPersistenceMixin(GamePersistenceMixin):
    def init_database(self) -> None:
        if not web.is_web():
            super().init_database()
            return
        if not hasattr(self, "web_save"):
            self.web_settings = BrowserStore("highrise-settings")
            self.web_save = BrowserStore("highrise-save")
            self.web_save_invalid = False
            self.web_has_progress = False

    def load_data(self) -> None:
        if not web.is_web():
            super().load_data()
            return
        self.init_database()
        try:
            if self.web_save.invalid:
                raise InvalidWebSave("Unreadable browser save")
            snapshot = validate_snapshot(
                self.web_save.load(),
                self.max_size,
                self.max_building_level,
                self.buildings.boosters.max_level,
                self.starting_money,
            )
        except InvalidWebSave:
            self.web_save_invalid = True
            self.show_storage_status()
            if self.tilemap is not None:
                return  # Reject the whole snapshot before changing the live board.
            snapshot = {}  # A fresh menu can still offer an explicit New Game.
        self._web_snapshot = snapshot
        self.web_has_progress = self.web_save.present and not self.web_save_invalid
        self.load_game_data(self.get_game_data())
        self.load_buildings()
        self.load_tasks()
        self.show_storage_status()

    def show_storage_status(self) -> None:
        if not web.is_web() or not hasattr(self, "web_save"):
            return
        messages = []
        if self.web_save_invalid:
            messages.append(tr("storage.invalid_save"))
        for store, kind in (
            (self.web_save, "progress"),
            (self.web_settings, "settings"),
        ):
            if store.outcome != WriteOutcome.DURABLE:
                messages.append(tr(f"storage.{kind}_{store.outcome.value}"))
        web.show_notice("\n".join(messages))

    def load_settings(self) -> GameSettings:
        if not web.is_web():
            return super().load_settings()
        data = self.web_settings.load()
        scale = data.get("ui_scale", DEFAULT_UI_SCALE)
        language = data.get("language", DEFAULT_LANGUAGE)
        return GameSettings(
            language if isinstance(language, str) else DEFAULT_LANGUAGE,
            False,
            scale if scale in UI_SCALES else DEFAULT_UI_SCALE,
            volume_or_default(data.get("master_volume"), 1.0),
        )

    def save_language(self, language: str) -> None:
        if web.is_web():
            self.web_settings.update(language=language)
            self.show_storage_status()
        else:
            super().save_language(language)

    def save_skip_intro(self, skip_intro: bool) -> None:
        if not web.is_web():
            super().save_skip_intro(skip_intro)

    def save_ui_scale(self, ui_scale: int) -> None:
        if web.is_web():
            self.web_settings.update(ui_scale=ui_scale)
            self.show_storage_status()
        else:
            super().save_ui_scale(ui_scale)

    def get_game_data(self) -> list[tuple] | None:
        if not web.is_web():
            return super().get_game_data()
        data = self._web_snapshot
        settings = self.web_settings.load()
        return [
            (
                data.get("age", 0),
                data.get("size", 2),
                data.get("money", self.starting_money),
                volume_or_default(
                    settings.get("music_volume"), self.default_music_volume
                ),
                volume_or_default(settings.get("sfx_volume"), self.default_sfx_volume),
            )
        ]

    def load_buildings(self) -> None:
        if not web.is_web():
            super().load_buildings()
            return
        self.buildings.clear()
        assert self.tilemap is not None, "tilemap not loaded yet"
        for saved in self._web_snapshot.get("buildings", []):
            row, column = saved["row"], saved["column"]
            self.add_building(
                saved["level"],
                row,
                column,
                saved["door_side"],
                booster=saved["booster"],
                income_fraction=saved["income_fraction"],
            )

    def load_tasks(self) -> None:
        if not web.is_web():
            super().load_tasks()
            return
        data = self._web_snapshot
        self.tasks.restore(
            set(data.get("tasks_done", [])), bool(data.get("boost_unlocked", False))
        )

    def save_audio_settings(self) -> None:
        if not web.is_web():
            super().save_audio_settings()
            return
        self.web_settings.update(
            master_volume=self.audio.master_volume(),
            music_volume=self.audio.music_volume(),
            sfx_volume=self.audio.sfx_volume(),
        )
        self.show_storage_status()

    def save_game(self) -> None:
        if not web.is_web():
            super().save_game()
            return
        if self.web_save_invalid:
            self.show_storage_status()
            return  # Only an explicit New Game may replace an invalid stored save.
        self.buildings.finish_pending_merges()
        assert self.tilemap is not None, "tilemap not loaded yet"
        self.web_save.save(
            {
                "version": 1,
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
        )
        self.web_has_progress = True  # Also retain a failed write for Continue/retry.
        self.show_storage_status()

    def delete_data(self) -> None:
        if web.is_web():
            self.web_save.delete()
            self.web_save_invalid = False
            self.web_has_progress = False
            self.show_storage_status()
        else:
            super().delete_data()
