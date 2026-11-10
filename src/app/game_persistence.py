from typing import TYPE_CHECKING, Any, NamedTuple

from gameplay.tilemap import Tilemap
from pygamine import clamp01
from pygamine.util.localization import DEFAULT_LANGUAGE
from ui.ui_scale import DEFAULT_UI_SCALE, UI_SCALES

# The master volume a fresh database starts with (also its column default).
DEFAULT_MASTER_VOLUME = 1.0


class GameSettings(NamedTuple):
    """The settings saved in the database's `settings` table."""

    language: str
    skip_intro: bool
    ui_scale: int
    master_volume: float


class GamePersistenceMixin:
    if TYPE_CHECKING:
        # Attributes / methods supplied by the host class (Game).
        def __getattr__(self, name: str) -> Any: ...

        # Declared here so the mixin's assignments don't narrow the type
        # Game gives it (None until a game is loaded).
        tilemap: Tilemap | None

    def load_data(self) -> None:
        self.init_database()
        self.load_game_data(self.get_game_data())
        self.load_buildings()

    def init_database(self) -> None:
        self.database.execute_safely(
            "CREATE TABLE IF NOT EXISTS game(age_number INTEGER, size INTEGER, money INTEGER, music_volume INTEGER, sfx_volume INTEGER)"
        )
        self.database.execute_safely(
            "CREATE TABLE IF NOT EXISTS buildings(level INTEGER, row INTEGER, column INTEGER)"
        )
        # A separate table, so saves made before these settings existed load
        # unchanged: the game table keeps its columns. Seeded with the
        # defaults (English, intro shown; the column defaults the UI scale) so the UPDATEs
        # below always hit a row.
        self.database.execute_safely(
            "CREATE TABLE IF NOT EXISTS settings(language TEXT, skip_intro INTEGER, "
            f"ui_scale INTEGER NOT NULL DEFAULT {DEFAULT_UI_SCALE}, "
            f"master_volume REAL NOT NULL DEFAULT {DEFAULT_MASTER_VOLUME})"
        )
        columns = self.database.execute_safely("PRAGMA table_info(settings)", True)
        assert columns is not None
        names = [column[1] for column in columns]
        if "ui_scale" not in names:
            # A settings table from before the UI scale: its existing row gets the default.
            self.database.execute_safely(
                "ALTER TABLE settings ADD COLUMN "
                f"ui_scale INTEGER NOT NULL DEFAULT {DEFAULT_UI_SCALE}"
            )
        if "master_volume" not in names:
            # Likewise for a table from before the master volume.
            self.database.execute_safely(
                "ALTER TABLE settings ADD COLUMN "
                f"master_volume REAL NOT NULL DEFAULT {DEFAULT_MASTER_VOLUME}"
            )
        self.database.execute_safely(
            "INSERT INTO settings(language, skip_intro) "
            "SELECT ?, 0 WHERE NOT EXISTS (SELECT 1 FROM settings)",
            params=(DEFAULT_LANGUAGE,),
        )

    def load_settings(self) -> GameSettings:
        """The saved settings. Needs `init_database()` first."""
        rows = self.database.execute_safely(
            "SELECT language, skip_intro, ui_scale, master_volume FROM settings", True
        )
        assert rows, "settings row missing: call init_database() first"
        language, skip_intro, ui_scale, master_volume = rows[0]
        if ui_scale not in UI_SCALES:
            ui_scale = DEFAULT_UI_SCALE  # a step removed since, or a hand-edited file
        # A hand-edited value outside 0-1 is clamped.
        return GameSettings(
            language, bool(skip_intro), ui_scale, clamp01(float(master_volume))
        )

    def save_language(self, language: str) -> None:
        self.database.execute_safely(
            "UPDATE settings SET language=?", params=(language,)
        )

    def save_skip_intro(self, skip_intro: bool) -> None:
        self.database.execute_safely(
            "UPDATE settings SET skip_intro=?", params=(int(skip_intro),)
        )

    def save_ui_scale(self, ui_scale: int) -> None:
        self.database.execute_safely(
            "UPDATE settings SET ui_scale=?", params=(ui_scale,)
        )

    def get_game_data(self) -> list[tuple] | None:
        game_data = self.database.execute_safely("SELECT * FROM game", True)
        if game_data:
            return game_data

        self.database.execute_safely(
            "INSERT INTO game(age_number, size, money, music_volume, sfx_volume) VALUES(?, ?, ?, ?, ?)",
            params=(
                0,
                2,
                self.starting_money,
                self.default_music_volume,
                self.default_sfx_volume,
            ),
        )
        return self.database.execute_safely("SELECT * FROM game", True)

    def load_game_data(self, game_data: list[tuple] | None) -> None:
        if not game_data:
            return

        age_number, size, money, music_volume, sfx_volume = game_data[0]
        self.player.money = money
        self.audio.set_music_volume(music_volume)
        self.audio.set_sfx_volume(sfx_volume)
        self.tilemap = Tilemap(size, self.max_size)
        self.tile_selector.tilemap = self.tilemap
        self.buildings.age_number = age_number

    def load_buildings(self) -> None:
        self.buildings.clear()
        buildings = self.database.execute_safely("SELECT * FROM buildings", True)
        if not buildings:
            return
        assert self.tilemap is not None, "tilemap not loaded yet"
        rows = self.tilemap.row_count
        cols = self.tilemap.column_count
        for level, row, column in buildings:
            if 1 <= row <= rows and 1 <= column <= cols:
                self.add_building(level, row, column)
            else:
                self.database.execute_safely(
                    "DELETE FROM buildings WHERE level=? AND row=? AND column=?",
                    params=(level, row, column),
                )

    def save_audio_settings(self) -> None:
        self.database.execute_safely(
            "UPDATE game SET music_volume=?, sfx_volume=?",
            params=(self.audio.music_volume(), self.audio.sfx_volume()),
        )
        # The master volume is a player setting, so New Game keeps it.
        self.database.execute_safely(
            "UPDATE settings SET master_volume=?", params=(self.audio.master_volume(),)
        )

    def save_game(self) -> None:
        # A merge in progress saves as its finished result, not as two
        # buildings stacked on one tile.
        self.buildings.finish_pending_merges()
        assert self.tilemap is not None, "tilemap not loaded yet"
        self.database.execute_safely(
            "UPDATE game SET age_number=?, size=?, money=?",
            params=(
                self.buildings.age_number,
                self.tilemap.row_count,
                self.player.money,
            ),
        )
        self.database.execute_safely("DELETE FROM buildings")

        for building in self.buildings:
            self.database.execute_safely(
                "INSERT INTO buildings(level, row, column) VALUES(?, ?, ?)",
                params=(
                    building.level,
                    building.tile.row_number,
                    building.tile.column_number,
                ),
            )

    def delete_data(self) -> None:
        self.database.execute_safely(
            "UPDATE game SET age_number=?, size=?, money=?",
            params=(0, 2, self.starting_money),
        )
        self.database.execute_safely("DELETE FROM buildings")
