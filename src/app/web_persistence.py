"""Browser saves use JSON/localStorage; desktop keeps its existing SQLite schema.

No SQLite import belongs on the browser startup path. Each completed save is
one localStorage write, including buildings, fractions and age-task progress.
The game-specific store names also isolate Highrise from Chokepoint on localhost.
"""

from app.game_persistence import GamePersistenceMixin, GameSettings
from gameplay.buildings.sprites import DOOR_SIDES, default_door_side
from pygamine import SaveStore
from pygamine.util.localization import DEFAULT_LANGUAGE
from ui.ui_scale import DEFAULT_UI_SCALE, UI_SCALES
from util import web


class WebPersistenceMixin(GamePersistenceMixin):
    def init_database(self) -> None:
        if not web.is_web():
            super().init_database()
            return
        self.web_settings = SaveStore("highrise-settings")
        self.web_save = SaveStore("highrise-save")

    def load_settings(self) -> GameSettings:
        if not web.is_web():
            return super().load_settings()
        data = self.web_settings.load()
        scale = data.get("ui_scale", DEFAULT_UI_SCALE)
        return GameSettings(
            data.get("language", DEFAULT_LANGUAGE),
            False,
            scale if scale in UI_SCALES else DEFAULT_UI_SCALE,
            data.get("master_volume", 1.0),
        )

    def save_language(self, language: str) -> None:
        if web.is_web():
            self.web_settings.update(language=language)
        else:
            super().save_language(language)

    def save_skip_intro(self, skip_intro: bool) -> None:
        if not web.is_web():
            super().save_skip_intro(skip_intro)

    def save_ui_scale(self, ui_scale: int) -> None:
        if web.is_web():
            self.web_settings.update(ui_scale=ui_scale)
        else:
            super().save_ui_scale(ui_scale)

    def get_game_data(self) -> list[tuple] | None:
        if not web.is_web():
            return super().get_game_data()
        data = self.web_save.load()
        settings = self.web_settings.load()
        return [
            (
                data.get("age", 0),
                data.get("size", 2),
                data.get("money", self.starting_money),
                settings.get("music_volume", self.default_music_volume),
                settings.get("sfx_volume", self.default_sfx_volume),
            )
        ]

    def load_buildings(self) -> None:
        if not web.is_web():
            super().load_buildings()
            return
        self.buildings.clear()
        assert self.tilemap is not None, "tilemap not loaded yet"
        for saved in self.web_save.load().get("buildings", []):
            row, column = saved["row"], saved["column"]
            if not (
                1 <= row <= self.tilemap.row_count
                and 1 <= column <= self.tilemap.column_count
            ):
                continue
            side = saved.get("door_side")
            if side not in DOOR_SIDES:
                side = default_door_side(row, column)
            booster = bool(saved.get("booster", False))
            self.add_building(
                self._valid_level(saved["level"], row, column, booster),
                row,
                column,
                side,
                booster=booster,
                income_fraction=self._valid_fraction(
                    saved.get("income_fraction", 0.0), row, column
                ),
            )

    def load_tasks(self) -> None:
        if not web.is_web():
            super().load_tasks()
            return
        data = self.web_save.load()
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

    def save_game(self) -> None:
        if not web.is_web():
            super().save_game()
            return
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

    def delete_data(self) -> None:
        if web.is_web():
            self.web_save.delete()
        else:
            super().delete_data()
