"""GamePersistenceMixin -- FakeGame subclasses the mixin directly (same
approach as test_game_events.py) against a real pygamine.Database pointed at
pytest's tmp_path, so save/load round-trips exercise real SQL rather than a
mocked connection. add_building() (defined on Game itself, not this mixin)
is stubbed to build a real Building through Buildings.create (the production
creation path) on the real Tilemap load_game_data() constructs."""

from types import SimpleNamespace


from app.game_persistence import GamePersistenceMixin, GameSettings
from gameplay.buildings.sprites import DOOR_SIDES, default_door_side
from ui.ui_scale import DEFAULT_UI_SCALE
from gameplay.buildings.building import Building, Buildings
from pygamine import Database


class FakeAudio:
    def __init__(self, music=0.5, sfx=0.5):
        self._master = 1.0
        self._music = music
        self._sfx = sfx

    def master_volume(self) -> float:
        return self._master

    def set_master_volume(self, value) -> None:
        self._master = value

    def music_volume(self) -> float:
        return self._music

    def sfx_volume(self) -> float:
        return self._sfx

    def set_music_volume(self, value) -> None:
        self._music = value

    def set_sfx_volume(self, value) -> None:
        self._sfx = value


class FakeGame(GamePersistenceMixin):
    def __init__(
        self,
        tmp_path,
        assets,
        *,
        starting_money=500,
        default_music=0.5,
        default_sfx=0.5,
        max_size=7,
    ):
        self.database = Database("test_persistence", directory=str(tmp_path))
        self.starting_money = starting_money
        self.default_music_volume = default_music
        self.default_sfx_volume = default_sfx
        self.max_size = max_size
        self.player = SimpleNamespace(money=0)
        self.audio = FakeAudio(default_music, default_sfx)
        self.max_building_level = 11
        self.tilemap = None
        self.tile_selector = SimpleNamespace(tilemap=None)
        self.buildings = Buildings()
        self.calls: list = []

    def add_building(self, level, row, column, door_side=None) -> None:
        self.calls.append(("add_building", level, row, column))
        tile = self.tilemap[row - 1][column - 1]
        self.buildings.append(self.buildings.create(level, tile, door_side=door_side))


def insert_building_row(game, level, row, column):
    game.database.execute_safely(
        "INSERT INTO buildings(level, row, column) VALUES (?, ?, ?)",
        params=(level, row, column),
    )


# ── init / seed ──────────────────────────────────────────────────────────────


def test_init_database_creates_empty_tables(tmp_path, assets):
    game = FakeGame(tmp_path, assets)

    game.init_database()

    assert game.database.execute_safely("SELECT * FROM game", True) == []
    assert game.database.execute_safely("SELECT * FROM buildings", True) == []


def test_get_game_data_seeds_a_default_row_on_first_call(tmp_path, assets):
    game = FakeGame(tmp_path, assets, starting_money=777)
    game.init_database()

    data = game.get_game_data()

    assert data == [(0, 2, 777, game.default_music_volume, game.default_sfx_volume)]


def test_get_game_data_returns_the_existing_row_on_later_calls(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    first = game.get_game_data()

    second = game.get_game_data()

    assert second == first


# ── load_data (top-level orchestrator) ──────────────────────────────────────


def test_load_data_bootstraps_a_brand_new_database_end_to_end(tmp_path, assets):
    game = FakeGame(tmp_path, assets, starting_money=250)

    game.load_data()

    assert game.player.money == 250
    assert game.tilemap is not None
    assert (game.tilemap.row_count, game.tilemap.column_count) == (2, 2)
    assert game.buildings == []


def test_load_data_restores_a_previously_saved_game(tmp_path, assets):
    seed = FakeGame(tmp_path, assets, starting_money=250)
    seed.load_data()
    seed.player.money = 999
    seed.buildings.age_number = 2
    seed.buildings.append(
        Building(3, 2, seed.tilemap[0][0], door_side="left", on_payout=None)
    )
    seed.save_game()

    game = FakeGame(tmp_path, assets, starting_money=250)
    game.load_data()

    assert game.player.money == 999
    assert game.buildings.age_number == 2
    assert len(game.buildings) == 1
    assert game.buildings[0].level == 3


# ── load_game_data ───────────────────────────────────────────────────────────


def test_load_game_data_applies_saved_values(tmp_path, assets):
    game = FakeGame(tmp_path, assets, max_size=7)

    game.load_game_data([(3, 4, 250, 0.6, 0.2)])

    assert game.player.money == 250
    assert game.audio.music_volume() == 0.6
    assert game.audio.sfx_volume() == 0.2
    assert game.tilemap is not None
    assert (game.tilemap.row_count, game.tilemap.column_count) == (4, 4)
    assert game.tile_selector.tilemap is game.tilemap
    assert game.buildings.age_number == 3


def test_load_game_data_is_a_no_op_with_no_rows(tmp_path, assets):
    game = FakeGame(tmp_path, assets)

    game.load_game_data(None)
    game.load_game_data([])

    assert game.tilemap is None
    assert game.player.money == 0


# ── load_buildings ───────────────────────────────────────────────────────────


def test_load_buildings_restores_valid_rows_within_the_grid(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.load_game_data([(0, 3, 0, 0.5, 0.5)])  # 3x3 grid
    insert_building_row(game, 2, 1, 1)
    insert_building_row(game, 1, 3, 3)

    game.load_buildings()

    assert len(game.buildings) == 2
    assert ("add_building", 2, 1, 1) in game.calls
    assert ("add_building", 1, 3, 3) in game.calls


def test_load_buildings_deletes_out_of_bounds_rows_instead_of_restoring_them(
    tmp_path, assets
):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.load_game_data([(0, 3, 0, 0.5, 0.5)])  # 3x3 grid -- row/col must be 1..3
    insert_building_row(game, 1, 99, 99)  # out of bounds

    game.load_buildings()

    assert game.buildings == []
    assert game.calls == []
    remaining = game.database.execute_safely("SELECT * FROM buildings", True)
    assert remaining == []  # the bad row was deleted, not silently kept


def test_load_buildings_clears_any_existing_in_memory_buildings_first(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.load_game_data([(0, 3, 0, 0.5, 0.5)])
    game.buildings.append(
        Building(1, 0, game.tilemap[0][0], door_side="left", on_payout=None)
    )  # stale in-memory state

    game.load_buildings()

    assert game.buildings == []  # no rows in the db -> cleared, not left stale


# ── save / delete ────────────────────────────────────────────────────────────


def test_save_audio_settings_persists_current_volumes(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.get_game_data()
    game.audio.set_music_volume(0.42)
    game.audio.set_sfx_volume(0.13)

    game.save_audio_settings()

    row = game.database.execute_safely(
        "SELECT music_volume, sfx_volume FROM game", True
    )
    assert row == [(0.42, 0.13)]


def test_save_game_persists_state_and_buildings(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.get_game_data()  # seeds the row save_game()'s UPDATE needs to hit
    game.load_game_data([(0, 3, 0, 0.5, 0.5)])
    game.player.money = 900
    game.buildings.age_number = 2
    game.buildings.append(
        Building(3, 2, game.tilemap[1][1], door_side="left", on_payout=None)
    )

    game.save_game()

    game_row = game.database.execute_safely(
        "SELECT age_number, size, money FROM game", True
    )
    assert game_row == [(2, 3, 900)]
    building_rows = game.database.execute_safely(
        "SELECT level, row, column FROM buildings", True
    )
    assert building_rows == [(3, 2, 2)]


def test_save_mid_merge_saves_the_finished_merge(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.get_game_data()
    game.load_game_data([(0, 3, 0, 0.5, 0.5)])
    game.add_building(1, 1, 1)
    game.add_building(1, 1, 2)
    game.buildings.move("left", game.tilemap, 10)
    assert game.buildings.is_busy()

    game.save_game()

    building_rows = game.database.execute_safely(
        "SELECT level, row, column FROM buildings", True
    )
    assert building_rows == [(2, 1, 1)]
    assert [b.level for b in game.buildings] == [2]


def test_save_game_replaces_rather_than_accumulates_building_rows(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.get_game_data()
    game.load_game_data([(0, 3, 0, 0.5, 0.5)])
    game.buildings.append(
        Building(1, 0, game.tilemap[0][0], door_side="left", on_payout=None)
    )
    game.save_game()

    game.buildings.clear()
    game.buildings.append(
        Building(2, 0, game.tilemap[2][2], door_side="left", on_payout=None)
    )
    game.save_game()

    building_rows = game.database.execute_safely(
        "SELECT level, row, column FROM buildings", True
    )
    assert building_rows == [(2, 3, 3)]


def test_delete_data_resets_the_game_row_and_clears_buildings(tmp_path, assets):
    game = FakeGame(tmp_path, assets, starting_money=500)
    game.init_database()
    game.get_game_data()
    game.load_game_data([(0, 3, 0, 0.5, 0.5)])
    game.buildings.append(
        Building(1, 0, game.tilemap[0][0], door_side="left", on_payout=None)
    )
    game.save_game()

    game.delete_data()

    game_row = game.database.execute_safely(
        "SELECT age_number, size, money FROM game", True
    )
    assert game_row == [(0, 2, 500)]
    building_rows = game.database.execute_safely("SELECT * FROM buildings", True)
    assert building_rows == []


# ── settings (language, skip intro) ──────────────────────────────────────────


def test_settings_default_to_english_with_the_intro_shown(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()

    assert game.load_settings() == GameSettings("en", False, DEFAULT_UI_SCALE, 1.0)


def test_settings_round_trip_through_the_database(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()

    game.save_language("tr")
    game.save_skip_intro(True)
    game.save_ui_scale(80)

    reopened = FakeGame(tmp_path, assets)
    reopened.init_database()
    assert reopened.load_settings() == GameSettings("tr", True, 80, 1.0)


def test_init_database_keeps_saved_settings(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.save_language("tr")

    game.init_database()

    assert game.load_settings().language == "tr"


def test_a_save_from_before_the_settings_existed_loads_with_defaults(tmp_path, assets):
    old = FakeGame(tmp_path, assets, starting_money=321)
    old.database.execute_safely(
        "CREATE TABLE game(age_number INTEGER, size INTEGER, money INTEGER, "
        "music_volume INTEGER, sfx_volume INTEGER)"
    )
    old.database.execute_safely(
        "INSERT INTO game VALUES(?, ?, ?, ?, ?)", params=(1, 3, 321, 0.5, 0.5)
    )

    old.load_data()

    assert old.player.money == 321
    assert old.load_settings() == GameSettings("en", False, DEFAULT_UI_SCALE, 1.0)


def test_new_game_data_reset_keeps_the_settings(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.load_data()
    game.save_language("tr")
    game.save_skip_intro(True)
    game.save_ui_scale(110)

    game.delete_data()

    assert game.load_settings() == GameSettings("tr", True, 110, 1.0)


def test_a_settings_table_from_before_the_ui_scale_gets_the_column_and_keeps_its_row(
    tmp_path, assets
):
    old = FakeGame(tmp_path, assets)
    old.database.execute_safely(
        "CREATE TABLE settings(language TEXT, skip_intro INTEGER)"
    )
    old.database.execute_safely("INSERT INTO settings VALUES('tr', 1)")

    old.init_database()

    assert old.load_settings() == GameSettings("tr", True, DEFAULT_UI_SCALE, 1.0)
    old.save_ui_scale(125)
    assert old.load_settings().ui_scale == 125


def test_init_database_keeps_a_saved_ui_scale(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.save_ui_scale(90)

    game.init_database()

    assert game.load_settings().ui_scale == 90


def test_an_unknown_saved_ui_scale_loads_as_the_default(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.save_ui_scale(33)

    assert game.load_settings().ui_scale == DEFAULT_UI_SCALE


# ── master volume ────────────────────────────────────────────────────────────


def test_the_master_volume_defaults_to_full(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()

    assert game.load_settings().master_volume == 1.0


def test_saving_the_audio_settings_keeps_the_master_volume_across_a_restart(
    tmp_path, assets
):
    game = FakeGame(tmp_path, assets)
    game.load_data()
    game.audio.set_master_volume(0.3)

    game.save_audio_settings()

    reopened = FakeGame(tmp_path, assets)
    reopened.init_database()
    assert reopened.load_settings().master_volume == 0.3


def test_new_game_data_reset_keeps_the_master_volume(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.load_data()
    game.audio.set_master_volume(0.3)
    game.save_audio_settings()

    game.delete_data()

    assert game.load_settings().master_volume == 0.3


def test_a_settings_table_from_before_the_master_volume_gets_the_column(
    tmp_path, assets
):
    old = FakeGame(tmp_path, assets)
    old.database.execute_safely(
        "CREATE TABLE settings(language TEXT, skip_intro INTEGER, "
        "ui_scale INTEGER NOT NULL DEFAULT 100)"
    )
    old.database.execute_safely("INSERT INTO settings VALUES('tr', 1, 110)")

    old.init_database()

    assert old.load_settings() == GameSettings("tr", True, 110, 1.0)


def test_door_sides_are_saved_and_loaded(tmp_path, assets):
    seed = FakeGame(tmp_path, assets)
    seed.load_data()
    tiles = seed.tilemap
    seed.buildings.append(
        Building(2, 0, tiles[0][0], door_side="right", on_payout=None)
    )
    seed.buildings.append(Building(1, 0, tiles[1][1], door_side="left", on_payout=None))
    seed.save_game()

    game = FakeGame(tmp_path, assets)
    game.load_data()

    assert {(b.level, b.door_side) for b in game.buildings} == {
        (2, "right"),
        (1, "left"),
    }


def test_a_save_from_before_door_sides_is_migrated_with_a_fixed_default(
    tmp_path, assets
):
    game = FakeGame(tmp_path, assets)
    # The buildings table as older versions created it: no door_side column.
    game.database.execute_safely(
        "CREATE TABLE buildings(level INTEGER, row INTEGER, column INTEGER)"
    )
    game.database.execute_safely(
        "INSERT INTO buildings(level, row, column) VALUES (2, 1, 1), (1, 1, 2)"
    )

    game.load_data()

    columns = game.database.execute_safely("PRAGMA table_info(buildings)", True)
    assert [c[1] for c in columns] == ["level", "row", "column", "door_side"]
    sides = {
        (b.tile.row_number, b.tile.column_number): b.door_side for b in game.buildings
    }
    assert sides == {(1, 1): default_door_side(1, 1), (1, 2): default_door_side(1, 2)}
    assert set(sides.values()) == set(DOOR_SIDES)

    # A second start gives the same sides.
    again = FakeGame(tmp_path, assets)
    again.load_data()
    assert {
        (b.tile.row_number, b.tile.column_number): b.door_side for b in again.buildings
    } == sides


def test_an_unknown_saved_door_side_falls_back_to_the_default(tmp_path, assets):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.load_game_data([(0, 3, 0, 0.5, 0.5)])
    game.database.execute_safely(
        "INSERT INTO buildings(level, row, column, door_side) VALUES (1, 2, 2, 'sideways')"
    )

    game.load_buildings()

    assert game.buildings[0].door_side == default_door_side(2, 2)


def test_a_saved_level_outside_the_recipes_is_held_to_the_valid_range(
    tmp_path, assets, caplog
):
    game = FakeGame(tmp_path, assets)
    game.init_database()
    game.load_game_data([(0, 3, 0, 0.5, 0.5)])
    insert_building_row(game, 0, 1, 1)
    insert_building_row(game, 12, 1, 2)
    insert_building_row(game, 5, 1, 3)

    with caplog.at_level("WARNING"):
        game.load_buildings()

    levels = {
        (b.tile.row_number, b.tile.column_number): b.level for b in game.buildings
    }
    assert levels == {(1, 1): 1, (1, 2): 11, (1, 3): 5}
    assert len(caplog.records) == 2  # the two bad rows, not the valid one
