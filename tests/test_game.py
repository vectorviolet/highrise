"""Game itself (app/game.py) -- constructing a real Game() needs the full
YAML panel/asset/tilemap stack for no benefit here (same reasoning
test_game_events.py/test_game_persistence.py already established for their
mixins). These build a bare Game instance via object.__new__(Game), which
skips __init__ entirely, then attach only what the method under test
touches -- real Player/Buildings/Tilemap where the game logic itself is
under test, small fakes for pure UI/plumbing (panel_manager, audio, ...).
"""

from collections.abc import KeysView
from types import SimpleNamespace

import pygame
import pytest

from app.game import Game, format_volume
from app.game_persistence import GameSettings
from domain.player import Player
from gameplay.buildings.building import Building, Buildings
from gameplay.tile_selector import TileSelector
from gameplay.tilemap import Tilemap
from pygamine import TextObject, Transform
from pygamine.util.localization import localization
from ui.info_panel import InfoPanel
from ui.ui_scale import DEFAULT_UI_SCALE

MAX_SIZE = 7
MAX_BUILDING_LEVEL = 10


class Spy:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)


class FakeText:
    def __init__(self):
        self.text = None
        self.state = None

    def set_text(self, text, state=None) -> None:
        self.text = text
        self.state = state


class FakePanelManager(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_panel = "menu"

    def keys(self) -> KeysView[str]:
        return dict.keys(self)

    def update(self):
        pass

    def draw(self, surface):
        pass

    def handle_event(self, event, pos):
        pass

    def open_panel(self, tab):
        self.current_panel = tab


class FakeAudio:
    def __init__(self):
        self.played = []
        self._music = 0.5
        self._sfx = 0.5

    def play_sfx(self, path):
        self.played.append(path)

    def music_volume(self) -> float:
        return self._music

    def sfx_volume(self) -> float:
        return self._sfx

    def set_music_volume(self, v):
        self._music = v

    def set_sfx_volume(self, v):
        self._sfx = v


class FakeLabel(FakeText):
    """A key-driven label (text_key + text_params), as the info panel texts are."""

    def set_params(self, **params) -> None:
        self.params = params


def make_panels() -> FakePanelManager:
    panel = FakePanelManager(
        {
            "game": {"build_button_text": FakeText()},
            "audio_settings": {
                "music_volume_entry_text": FakeText(),
                "sfx_volume_entry_text": FakeText(),
            },
            "display_settings": {
                "window_size_entry_text": FakeText(),
                "window_mode_entry_text": FakeText(),
                "ui_scale_entry_text": FakeText(),
            },
            "game_settings": {
                "language_entry_text": FakeText(),
                "skip_intro_entry_text": FakeText(),
            },
        }
    )
    return panel


def make_game(assets, *, size=3, max_size=MAX_SIZE, starting_money=500) -> Game:
    game = object.__new__(Game)
    game.assets = assets
    game.player = Player()
    game.player.money = starting_money
    game.buildings = Buildings(
        on_merge=game._on_buildings_merged, on_payout=game._on_building_payout
    )
    game.tilemap = Tilemap(size, max_size)
    game.max_size = max_size
    game.max_building_level = MAX_BUILDING_LEVEL
    game.starting_money = starting_money
    game.tile_selector = SimpleNamespace(is_active=False, tilemap=game.tilemap)
    game.audio = FakeAudio()
    game.click_sound_path = "assets/sfx/click.ogg"
    game.go_back_sound_path = "assets/sfx/back.ogg"
    game.merge_sound_path = assets.sound_path("merge")
    game.panel_manager = make_panels()
    game.cloud_animation = SimpleNamespace(
        create_clouds=Spy(), update=Spy(), draw=Spy()
    )
    game.info_panel = SimpleNamespace(is_active=False, close=Spy())
    game.old_music_volume = 0.5
    game.old_sfx_volume = 0.5
    game.update_button_texts = Spy()
    game.skip_intro = False
    game.ui_scale = DEFAULT_UI_SCALE
    # pygamine 0.29.0 owns the display stack in Application.display; Game
    # forwards display_surface, window_mode and resolution to it.
    game.display = SimpleNamespace(
        display_surface=pygame.display.get_surface(),
        window_mode="windowed",
        resolution=(1280, 720),
    )
    return game


# ── expand ───────────────────────────────────────────────────────────────────


def test_expand_grows_the_map_and_relocates_building_tiles(assets):
    game = make_game(assets, size=3, starting_money=100_000)
    tile = game.tilemap[1][1]
    building = Building(1, 0, tile, on_payout=None)
    game.buildings.append(building)

    game.expand()

    assert (game.tilemap.row_count, game.tilemap.column_count) == (4, 4)
    # Same logical (row, col) on the new, bigger grid -- a fresh Tile object.
    assert building.tile is game.tilemap[1][1]
    assert len(game.update_button_texts.calls) == 1
    assert game.audio.played == [game.click_sound_path]


def test_expand_does_nothing_at_max_size(assets):
    game = make_game(assets, size=MAX_SIZE, starting_money=100_000)

    game.expand()

    assert (game.tilemap.row_count, game.tilemap.column_count) == (MAX_SIZE, MAX_SIZE)
    assert game.audio.played == []


def test_expand_does_nothing_when_unaffordable(assets):
    game = make_game(assets, size=3, starting_money=0)

    game.expand()

    assert (game.tilemap.row_count, game.tilemap.column_count) == (3, 3)
    assert game.player.money == 0


# ── add_building ─────────────────────────────────────────────────────────────


def test_add_building_appends_and_sorts_by_column(assets):
    game = make_game(assets, size=3)

    game.add_building(1, 1, 3)
    game.add_building(2, 1, 1)

    assert [b.tile.column_number for b in game.buildings] == [1, 3]


def test_add_building_marks_tiles_full_once_the_grid_is_saturated(assets):
    game = make_game(assets, size=1)  # a single tile

    game.add_building(1, 1, 1)

    assert game.panel_manager["game"]["build_button_text"].text == "TILES FULL"


# ── create_building ──────────────────────────────────────────────────────────


def test_create_building_places_on_an_empty_tile_and_spends_money(assets, monkeypatch):
    game = make_game(assets, size=2, starting_money=100_000)
    monkeypatch.setattr("app.game.choice", lambda seq: sorted(seq)[0])

    game.create_building()

    assert len(game.buildings) == 1
    assert game.buildings[0].tile.row_number, game.buildings[0].tile.column_number == (
        1,
        1,
    )
    assert game.player.money == 100_000 - game.buildings.get_build_cost()
    assert game.audio.played == [game.click_sound_path]


def test_create_building_does_nothing_when_unaffordable(assets):
    game = make_game(assets, size=2, starting_money=0)

    game.create_building()

    assert len(game.buildings) == 0


# ── age progression ──────────────────────────────────────────────────────────


def test_set_age_within_range_updates_buildings_and_button_texts(assets):
    game = make_game(assets, size=3)

    game.set_age(1)

    assert game.buildings.age_number == 1
    assert len(game.update_button_texts.calls) == 1


def test_set_age_beyond_max_is_a_no_op(assets):
    game = make_game(assets, size=3)
    beyond_max = game.buildings.max_age_number + 1

    game.set_age(beyond_max)

    assert game.buildings.age_number == 0


def test_next_age_advances_and_spends_money(assets):
    game = make_game(assets, size=3, starting_money=100_000)

    game.next_age()

    assert game.buildings.age_number == 1
    assert game.audio.played == [game.click_sound_path]


def test_next_age_does_nothing_when_unaffordable(assets):
    game = make_game(assets, size=3, starting_money=0)

    game.next_age()

    assert game.buildings.age_number == 0


def test_next_age_does_nothing_at_max_age(assets):
    game = make_game(assets, size=3, starting_money=100_000_000)
    game.buildings.age_number = game.buildings.max_age_number

    game.next_age()

    assert game.buildings.age_number == game.buildings.max_age_number


def _start_merge(game):
    """Two level-1 buildings side by side, moved left so they start merging."""
    game.add_building(1, 1, 1)
    game.add_building(1, 1, 2)
    game.move_buildings("left")
    survivor, sacrificial = sorted(game.buildings, key=lambda b: b.should_destroy)
    assert sacrificial.merge_target is survivor
    return survivor, sacrificial


def _run_until_settled(game, max_frames=100):
    for _ in range(max_frames):
        game.buildings.control_moving()
        if not game.buildings.is_busy():
            return
        for building in game.buildings:
            if building.rigidbody.velocity != (0, 0):
                building.rect.topleft = tuple(map(int, building.target_position))
    raise AssertionError("buildings never settled")


def test_next_age_works_again_once_the_merge_has_finished(assets):
    game = make_game(assets, size=3, starting_money=100_000)
    _start_merge(game)
    _run_until_settled(game)

    game.next_age()

    assert game.buildings.age_number == 1
    assert [(b.level, b.age_number) for b in game.buildings] == [(2, 1)]


@pytest.mark.parametrize("path", ["purchase", "load", "age", "merge"])
def test_every_production_insertion_path_pays_the_player(assets, path, monkeypatch):
    game = make_game(assets, size=3, starting_money=100_000)
    if path == "purchase":
        monkeypatch.setattr("app.game.choice", lambda tiles: (1, 1))
        game.create_building()
    elif path == "load":
        game.database = SimpleNamespace(execute_safely=lambda *a: [(2, 1, 1)])
        game.load_buildings()
    elif path == "age":
        game.add_building(1, 1, 1)
        game.next_age()
    else:
        _start_merge(game)
        _run_until_settled(game)

    assert len(game.buildings) == 1
    building = game.buildings[0]
    money = game.player.money
    building._payout()
    assert game.player.money == money + building.cooldown * building.speed


def test_a_building_cannot_be_constructed_without_choosing_a_payout(assets):
    with pytest.raises(TypeError):
        Building(1, 0, Tilemap(3, 3)[0][0])


# ── move_buildings ───────────────────────────────────────────────────────────


def test_move_buildings_forwards_to_buildings_move(assets):
    game = make_game(assets, size=3)
    game.buildings.move = Spy()

    game.move_buildings("right")

    assert game.buildings.move.calls == [("right", game.tilemap, MAX_BUILDING_LEVEL)]


def test_move_buildings_is_a_no_op_while_the_tile_selector_is_active(assets):
    game = make_game(assets, size=3)
    game.tile_selector.is_active = True
    game.buildings.move = Spy()

    game.move_buildings("right")

    assert game.buildings.move.calls == []


# ── payouts / panels ─────────────────────────────────────────────────────────


def test_on_building_payout_credits_the_player(assets):
    game = make_game(assets, size=3)

    game._on_building_payout(15)

    assert game.player.money == 500 + 15


def test_open_panel_exits_for_the_exit_tab(assets):
    game = make_game(assets, size=3)
    game.exit = Spy()

    game.open_panel("exit")

    assert len(game.exit.calls) == 1
    assert len(game.cloud_animation.create_clouds.calls) == 0


def test_open_panel_switches_tabs_and_spawns_clouds(assets):
    game = make_game(assets, size=3)

    game.open_panel("game")

    assert game.panel_manager.current_panel == "game"
    assert len(game.cloud_animation.create_clouds.calls) == 1


def test_has_save_data_true_with_buildings_or_advanced_age(assets):
    game = make_game(assets, size=3)
    assert game.has_save_data() is False

    game.buildings.append(Building(1, 0, game.tilemap[0][0], on_payout=None))
    assert game.has_save_data() is True

    game2 = make_game(assets, size=3)
    game2.buildings.age_number = 1
    assert game2.has_save_data() is True


def test_play_opens_the_play_panel_when_a_save_exists(assets):
    game = make_game(assets, size=3)
    game.buildings.append(Building(1, 0, game.tilemap[0][0], on_payout=None))

    game.play()

    assert game.panel_manager.current_panel == "play"


def test_play_starts_a_new_game_with_no_save(assets):
    game = make_game(assets, size=3)
    game.delete_data = Spy()
    game.load_data = Spy()
    game.add_objects = Spy()
    game.set_music_label = Spy()
    game.set_sfx_label = Spy()

    game.play()

    assert len(game.load_data.calls) == 1
    assert game.panel_manager.current_panel == "game"


# ── volume / window labels ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("volume", "text"),
    [
        (0.0, "%0"),
        (0.5, "%50"),
        (0.567, "%57"),
        (1.0, "%100"),
        (-0.5, "%0"),
        (1.5, "%100"),
    ],
)
def test_format_volume_is_a_clamped_rounded_percentage(volume, text):
    assert format_volume(volume) == text


def test_set_music_and_sfx_labels_round_to_a_percentage(assets):
    game = make_game(assets, size=3)

    game.set_music_label(0.567)
    game.set_sfx_label(1.0)

    assert game.panel_manager["audio_settings"]["music_volume_entry_text"].text == "%57"
    assert game.panel_manager["audio_settings"]["sfx_volume_entry_text"].text == "%100"


def test_set_music_label_clamps_out_of_range_values(assets):
    game = make_game(assets, size=3)

    game.set_music_label(-0.5)
    assert game.panel_manager["audio_settings"]["music_volume_entry_text"].text == "%0"

    game.set_music_label(1.5)
    assert (
        game.panel_manager["audio_settings"]["music_volume_entry_text"].text == "%100"
    )


def test_set_window_size_and_mode_labels(assets):
    game = make_game(assets, size=3)
    game.display.resolution = (1280, 720)
    game.display.window_mode = "windowed"

    game.set_window_size_label()
    game.set_window_mode_label()

    assert (
        game.panel_manager["display_settings"]["window_size_entry_text"].text
        == "1280x720"
    )
    assert (
        game.panel_manager["display_settings"]["window_mode_entry_text"].text
        == "WINDOWED"
    )


# ── event / update / draw dispatch ───────────────────────────────────────────


def test_handle_event_dispatches_to_the_current_panels_handler(assets):
    game = make_game(assets, size=3)
    game.panel_manager.current_panel = "game"
    game.mouse = SimpleNamespace(position=(0, 0))
    game.menu_controllers = {}
    handler = Spy()
    game.handlers = {"game": handler}
    event = pygame.event.Event(pygame.MOUSEMOTION, pos=(0, 0))

    game.handle_event(event)

    assert handler.calls == [(event,)]


def test_add_building_assigns_payout_before_the_first_update(assets):
    game = make_game(assets, size=3)
    game.add_building(1, 1, 1)
    building = game.buildings[0]

    # Bound-method identity isn't stable across separate attribute accesses
    # in Python -- == (same underlying function + instance) is the right check.
    assert building.on_payout == game._on_building_payout
    money = game.player.money
    building._payout()
    assert game.player.money == money + building.cooldown * building.speed


def test_game_plays_the_merge_sound_through_the_collection_callback(assets):
    game = make_game(assets)
    game.add_building(1, 1, 1)
    game.add_building(1, 1, 2)
    survivor, sacrificial = game.buildings
    sacrificial.merge_into(survivor)

    game.buildings.control_moving()

    assert game.audio.played == [assets.sound_path("merge")]
    assert game.buildings[0].on_payout == game._on_building_payout


def test_loaded_buildings_have_payout_callbacks_without_an_update(assets):
    game = make_game(assets)
    game.database = SimpleNamespace(execute_safely=lambda *args: [(2, 1, 1)])

    game.load_buildings()

    assert len(game.buildings) == 1
    building = game.buildings[0]
    assert building.level == 2
    money = game.player.money
    building._payout()
    assert game.player.money == money + building.cooldown * building.speed


def test_draw_calls_panels_and_clouds(assets):
    game = make_game(assets, size=3)
    game.panel_manager.draw = Spy()
    game.window = pygame.Surface((100, 100))

    game.draw()

    assert len(game.panel_manager.draw.calls) == 1
    assert len(game.cloud_animation.draw.calls) == 1


# ── exit flow ────────────────────────────────────────────────────────────────


def test_on_exit_request_from_menu_exits(assets):
    game = make_game(assets, size=3)
    game.panel_manager.current_panel = "menu"
    game.exit = Spy()

    game.on_exit_request()

    assert len(game.exit.calls) == 1
    assert game.audio.played == [game.go_back_sound_path]


@pytest.mark.parametrize(
    "panel,expected",
    [
        ("play", "menu"),
        ("settings", "menu"),
        ("display_settings", "settings"),
        ("game_settings", "settings"),
        ("developer", "menu"),
    ],
)
def test_on_exit_request_navigates_back(assets, panel, expected):
    game = make_game(assets, size=3)
    game.panel_manager.current_panel = panel

    game.on_exit_request()

    assert game.panel_manager.current_panel == expected


def test_on_exit_request_from_audio_settings_restores_snapshotted_volumes(assets):
    game = make_game(assets, size=3)
    game.panel_manager.current_panel = "audio_settings"
    game.audio._music, game.audio._sfx = 0.9, 0.9
    game.old_music_volume, game.old_sfx_volume = 0.2, 0.3

    game.on_exit_request()

    assert (game.audio._music, game.audio._sfx) == (0.2, 0.3)
    assert game.panel_manager.current_panel == "settings"


def test_on_exit_request_from_game_closes_info_panel_instead_of_saving(assets):
    game = make_game(assets, size=3)
    game.panel_manager.current_panel = "game"
    game.info_panel.is_active = True
    game.save_game = Spy()

    game.on_exit_request()

    assert len(game.info_panel.close.calls) == 1
    assert len(game.save_game.calls) == 0
    assert (
        game.panel_manager.current_panel == "game"
    )  # unchanged -- just closed the panel


def test_on_exit_request_from_game_saves_and_returns_to_menu(assets):
    game = make_game(assets, size=3)
    game.panel_manager.current_panel = "game"
    game.info_panel.is_active = False
    game.save_game = Spy()

    game.on_exit_request()

    assert len(game.save_game.calls) == 1
    assert game.panel_manager.current_panel == "menu"


# ── characterization: exit flow and session reset ────────────────────────────


def test_on_exit_request_from_an_unknown_panel_only_plays_the_back_sound(assets):
    game = make_game(assets, size=3)
    game.panel_manager.current_panel = "splash"
    game.exit = Spy()
    game.save_game = Spy()

    game.on_exit_request()

    assert game.audio.played == [game.go_back_sound_path]
    assert game.panel_manager.current_panel == "splash"
    assert game.exit.calls == []
    assert game.save_game.calls == []
    assert game.cloud_animation.create_clouds.calls == []


@pytest.mark.parametrize(
    "panel",
    ["play", "settings", "display_settings", "game_settings", "developer"],
)
def test_on_exit_request_back_navigation_spawns_clouds_once(assets, panel):
    game = make_game(assets, size=3)
    game.panel_manager.current_panel = panel

    game.on_exit_request()

    assert len(game.cloud_animation.create_clouds.calls) == 1
    assert game.audio.played == [game.go_back_sound_path]


def test_on_exit_request_from_audio_settings_resets_the_labels(assets):
    game = make_game(assets, size=3)
    game.panel_manager.current_panel = "audio_settings"
    game.old_music_volume, game.old_sfx_volume = 0.2, 0.3

    game.on_exit_request()

    labels = game.panel_manager["audio_settings"]
    assert labels["music_volume_entry_text"].text == "%20"
    assert labels["sfx_volume_entry_text"].text == "%30"


def test_new_game_resets_the_session_ui(assets):
    game = make_game(assets, size=3)
    game.delete_data = Spy()
    game.load_data = Spy()
    game.add_objects = Spy()
    game.tile_selector.is_active = True
    game.audio._music, game.audio._sfx = 0.2, 0.7
    game.buildings.set_age(1)

    game.new_game()

    assert len(game.delete_data.calls) == 1
    assert len(game.add_objects.calls) == 1
    assert game.buildings.age_number == 1
    assert len(game.update_button_texts.calls) >= 1
    assert len(game.info_panel.close.calls) == 1
    assert game.tile_selector.is_active is False
    labels = game.panel_manager["audio_settings"]
    assert labels["music_volume_entry_text"].text == "%20"
    assert labels["sfx_volume_entry_text"].text == "%70"
    assert game.panel_manager.current_panel == "game"


def test_run_resets_the_session_ui_and_opens_the_menu(assets, monkeypatch):
    import pygamine

    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    game = make_game(assets, size=3)
    game.show_splash = Spy()
    game.mouse = SimpleNamespace(
        set_cursor_visible=Spy(), set_cursor_image=Spy(), position=(0, 0)
    )
    game.cursor_size = (10, 10)
    game.load_data = Spy()
    game.add_objects = Spy()
    game.init_database = Spy()
    game.load_settings = lambda: GameSettings("en", False, DEFAULT_UI_SCALE)
    game.background_music_sound_path = None
    game.display.resolution = (1280, 720)
    game.display.window_mode = "windowed"
    game.audio._music, game.audio._sfx = 0.2, 0.7

    game.run()

    assert len(game.update_button_texts.calls) >= 1
    assert len(game.info_panel.close.calls) == 1
    assert game.panel_manager.current_panel == "menu"
    labels = game.panel_manager["audio_settings"]
    assert labels["music_volume_entry_text"].text == "%20"
    assert labels["sfx_volume_entry_text"].text == "%70"
    display = game.panel_manager["display_settings"]
    assert display["window_size_entry_text"].text == "1280x720"
    assert display["window_mode_entry_text"].text == "WINDOWED"
    game_settings = game.panel_manager["game_settings"]
    assert game_settings["language_entry_text"].text == "ENGLISH"
    assert game_settings["skip_intro_entry_text"].text == "OFF"


def _run_with_saved_settings(assets, monkeypatch, settings):
    import pygamine

    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    game = make_game(assets, size=3)
    splash = object()
    game.splash = splash
    game.calls = []
    game.show_splash = lambda: game.calls.append(("show_splash", game.splash))
    game.mouse = SimpleNamespace(
        set_cursor_visible=Spy(), set_cursor_image=Spy(), position=(0, 0)
    )
    game.cursor_size = (10, 10)
    game.load_data = Spy()
    game.add_objects = Spy()
    game.init_database = Spy()
    game.load_settings = lambda: settings
    game.background_music_sound_path = None
    game.run()
    return game, splash


def test_run_watches_the_language_while_running_and_stops_after(assets, monkeypatch):
    import pygamine

    game = make_game(assets, size=3)
    during = []

    def fake_run(self):
        localization.set_language("tr")
        during.append(len(game.update_button_texts.calls))

    monkeypatch.setattr(pygamine.Application, "run", fake_run)
    game.splash = None
    game.mouse = SimpleNamespace(
        set_cursor_visible=Spy(), set_cursor_image=Spy(), position=(0, 0)
    )
    game.cursor_size = (10, 10)
    game.load_data = Spy()
    game.add_objects = Spy()
    game.init_database = Spy()
    game.load_settings = lambda: GameSettings("en", False, DEFAULT_UI_SCALE)
    game.background_music_sound_path = None

    game.run()
    calls_after_run = len(game.update_button_texts.calls)
    localization.set_language("en")

    assert during[0] > 0  # re-texted while running
    assert len(game.update_button_texts.calls) == calls_after_run  # not afterwards


def test_a_second_game_does_not_trigger_the_first_ones_language_callback(
    assets, monkeypatch
):
    first, _ = _run_with_saved_settings(
        assets, monkeypatch, GameSettings("en", False, DEFAULT_UI_SCALE)
    )
    calls_before = len(first.update_button_texts.calls)

    _run_with_saved_settings(
        assets, monkeypatch, GameSettings("tr", False, DEFAULT_UI_SCALE)
    )

    assert len(first.update_button_texts.calls) == calls_before


def test_run_unwatches_the_language_even_when_the_loop_crashes(assets, monkeypatch):
    import pygamine

    def crash(self):
        raise RuntimeError("boom")

    monkeypatch.setattr(pygamine.Application, "run", crash)
    game = make_game(assets, size=3)
    game.splash = None
    game.mouse = SimpleNamespace(
        set_cursor_visible=Spy(), set_cursor_image=Spy(), position=(0, 0)
    )
    game.cursor_size = (10, 10)
    game.load_data = Spy()
    game.add_objects = Spy()
    game.init_database = Spy()
    game.load_settings = lambda: GameSettings("en", False, DEFAULT_UI_SCALE)
    game.background_music_sound_path = None

    with pytest.raises(RuntimeError):
        game.run()
    calls = len(game.update_button_texts.calls)
    localization.set_language("tr")

    assert len(game.update_button_texts.calls) == calls


def test_run_shows_the_intro_by_default(assets, monkeypatch):
    game, splash = _run_with_saved_settings(
        assets, monkeypatch, GameSettings("en", False, DEFAULT_UI_SCALE)
    )

    assert game.calls == [("show_splash", splash)]


def test_run_skips_the_intro_when_the_saved_setting_says_so(assets, monkeypatch):
    game, _ = _run_with_saved_settings(
        assets, monkeypatch, GameSettings("en", True, DEFAULT_UI_SCALE)
    )

    assert game.splash is None
    assert game.skip_intro is True


def test_run_opens_in_the_saved_language(assets, monkeypatch):
    game, _ = _run_with_saved_settings(
        assets, monkeypatch, GameSettings("tr", False, DEFAULT_UI_SCALE)
    )

    assert localization.language == "tr"
    assert game.panel_manager["game_settings"]["language_entry_text"].text == "TÜRKÇE"
    assert (
        game.panel_manager["display_settings"]["window_mode_entry_text"].text
        == "PENCERELİ"
    )


def test_run_falls_back_to_english_for_an_unknown_saved_language(assets, monkeypatch):
    _run_with_saved_settings(
        assets, monkeypatch, GameSettings("xx", False, DEFAULT_UI_SCALE)
    )

    assert localization.language == "en"


# -- language and skip intro (the Game settings page) --


def record_saves(game) -> None:
    """Replaces the persistence mixin's writes with a log in `game.saved`."""
    game.saved = []
    game.save_language = lambda code: game.saved.append(("language", code))
    game.save_skip_intro = lambda flag: game.saved.append(("skip_intro", flag))


def test_change_language_saves_it_and_re_texts_the_labels_at_once(assets):
    game = make_game(assets, size=3)
    record_saves(game)
    label = TextObject(
        Transform((0, 0), (100, 100)),
        (0, 0),
        font=pygame.font.Font(None, 15),
        text_key="menu.play",
    )
    assert label.text == "PLAY"
    localization.on_language_changed(game._on_language_changed)
    try:
        game.change_language("tr")
    finally:
        localization.remove_language_changed(game._on_language_changed)
        label.on_removed()

    assert game.saved == [("language", "tr")]
    assert label.text == "OYNA"
    assert game.panel_manager["game_settings"]["language_entry_text"].text == "TÜRKÇE"
    assert game.update_button_texts.calls  # the hover texts follow too


def test_change_language_rejects_an_unknown_language_before_saving(assets):
    game = make_game(assets, size=3)
    record_saves(game)

    with pytest.raises(KeyError):
        game.change_language("xx")

    assert game.saved == []
    assert localization.language == "en"


@pytest.mark.parametrize("delta", [1, -1])
def test_cycle_language_wraps_around_the_available_languages(assets, delta):
    game = make_game(assets, size=3)
    record_saves(game)

    game.cycle_language(delta)
    assert localization.language == "tr"

    game.cycle_language(delta)
    assert localization.language == "en"
    assert game.saved == [("language", "tr"), ("language", "en")]


def test_set_skip_intro_saves_it_and_updates_the_label(assets):
    game = make_game(assets, size=3)
    record_saves(game)
    label = game.panel_manager["game_settings"]["skip_intro_entry_text"]

    game.set_skip_intro(True)
    assert (game.skip_intro, label.text, game.saved) == (
        True,
        "ON",
        [("skip_intro", True)],
    )

    localization.set_language("tr")
    game.set_skip_intro(False)
    assert (game.skip_intro, label.text) == (False, "KAPALI")


def test_the_window_mode_label_is_translated(assets):
    game = make_game(assets, size=3)
    localization.set_language("tr")
    game.display.window_mode = "borderless"

    game.set_window_mode_label()

    assert (
        game.panel_manager["display_settings"]["window_mode_entry_text"].text
        == "ÇERÇEVESİZ"
    )


# -- board-changing input while buildings are busy (real event path) --


class FakeButton:
    def __init__(self):
        self.clicked = False

    def is_clicked(self, event, mouse_pos) -> bool:
        clicked, self.clicked = self.clicked, False
        return clicked

    def set_base_state(self, state) -> None:
        self.base_state = state


class FakeImage:
    rect = Transform((0, 0), (65, 89))

    def add_surface(self, name, surface) -> None:
        pass

    def set_state(self, state) -> None:
        pass


class InfoPanelWidget:
    """panel["info_panel"]: active while the InfoPanel's root is."""

    def __init__(self, info_panel):
        self._info_panel = info_panel

    @property
    def active(self) -> bool:
        return self._info_panel.is_active


def make_playable_game(assets) -> Game:
    """make_game plus the real TileSelector, InfoPanel and handle_game_events."""
    game = make_game(assets, size=3, starting_money=100_000)
    game.mouse = SimpleNamespace(position=(-9999, -9999))
    game.tile_selector = TileSelector(game.tilemap, game.mouse, game.buildings)
    game.panel_manager.current_panel = "game"
    game.info_panel = InfoPanel(game.panel_manager)
    game.info_panel.close()
    panel = game.panel_manager["game"]
    for name in (
        "level_text",
        "speed_text",
        "cooldown_text",
        "sell_price_text",
    ):
        panel[name] = FakeLabel()
    panel["sell_button_text"] = FakeText()
    panel["info_panel_building_image"] = FakeImage()
    panel["info_panel"] = InfoPanelWidget(game.info_panel)
    for name in (
        "sell_button",
        "close_button",
        "selection_mode_button",
        "expand_button",
        "build_button",
        "next_age_button",
    ):
        panel[name] = FakeButton()
    return game


def _click(game, button_name):
    game.panel_manager["game"][button_name].clicked = True
    game.handle_game_events(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1))


def _key(game, key):
    game.handle_game_events(pygame.event.Event(pygame.KEYUP, key=key))


def _arrive(game):
    """Put sliding buildings on their targets; control_moving then settles them."""
    for building in game.buildings:
        if building.rigidbody.velocity != (0, 0):
            building.rect.topleft = tuple(map(int, building.target_position))
    game.buildings.control_moving()


def _pick(game, tile):
    """Turn on selection mode and click a tile, through the real TileSelector."""
    game.tile_selector.is_active = True
    game.mouse.position = tile.unselected_rect.center
    game.handle_game_events(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1))
    game.tile_selector.is_active = False


@pytest.mark.parametrize("frame", ["sliding", "arrived"])
@pytest.mark.parametrize(
    "action",
    ["next_age_button", "build_button", pygame.K_SPACE, pygame.K_RIGHT, pygame.K_d],
)
def test_board_changing_input_is_ignored_while_a_merge_is_pending(
    assets, frame, action
):
    game = make_playable_game(assets)
    survivor, sacrificial = _start_merge(game)
    if frame == "arrived":
        _arrive(game)  # the merge finishes on the next frame
        assert not game.buildings.is_moving()
    money = game.player.money

    if isinstance(action, str):
        _click(game, action)
    else:
        _key(game, action)

    assert game.buildings.age_number == 0
    assert game.player.money == money
    assert {id(b) for b in game.buildings} == {id(survivor), id(sacrificial)}
    assert survivor.tile is game.tilemap[0][0]
    assert sacrificial.tile is game.tilemap[0][0]
    _run_until_settled(game)
    assert [(b.level, b.tile) for b in game.buildings] == [(2, game.tilemap[0][0])]


def test_board_changing_input_works_again_once_the_board_settles(assets):
    game = make_playable_game(assets)
    _start_merge(game)
    _run_until_settled(game)

    _click(game, "next_age_button")
    _key(game, pygame.K_RIGHT)

    assert game.buildings.age_number == 1
    assert [b.tile for b in game.buildings] == [game.tilemap[0][2]]


def test_sell_through_the_info_panel_is_ignored_mid_merge(assets):
    game = make_playable_game(assets)
    _start_merge(game)
    _pick(game, game.tilemap[0][0])
    assert game.info_panel.is_active
    shown = game.info_panel.building
    money = game.player.money

    _click(game, "sell_button")

    assert shown in game.buildings
    assert len(game.buildings) == 2
    assert game.player.money == money


def test_info_panel_closes_when_a_merge_replaces_its_building(assets):
    game = make_playable_game(assets)
    _start_merge(game)
    _pick(game, game.tilemap[0][0])
    stale = game.info_panel.building
    _arrive(game)

    game.update()  # the merge finishes and replaces both buildings

    assert stale not in game.buildings
    assert not game.info_panel.is_active
    money = game.player.money
    _click(game, "sell_button")  # the panel is closed: nothing to sell
    assert [b.level for b in game.buildings] == [2]
    assert game.player.money == money


def test_sell_never_removes_a_building_that_left_the_board(assets):
    game = make_playable_game(assets)
    _start_merge(game)
    _pick(game, game.tilemap[0][0])
    stale = game.info_panel.building
    _arrive(game)
    game.buildings.control_moving()  # merge done; no update() closed the panel
    money = game.player.money

    _click(game, "sell_button")  # was a list.remove ValueError

    assert stale not in game.buildings
    assert [b.level for b in game.buildings] == [2]
    assert game.player.money == money
    assert not game.info_panel.is_active


def test_sell_through_the_info_panel_sells_a_settled_building(assets):
    game = make_playable_game(assets)
    game.add_building(2, 2, 2)
    _pick(game, game.tilemap[1][1])
    building = game.info_panel.building
    money = game.player.money

    _click(game, "sell_button")

    assert len(game.buildings) == 0
    assert game.player.money == money + building.sell_price
    assert not game.info_panel.is_active
