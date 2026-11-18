"""Browser startup, navigation and persistence with a real game and fake JS storage."""

import asyncio
import builtins
from types import SimpleNamespace
from unittest.mock import Mock

import pygame
import pytest

from app.game import Game
from pygamine import Application
from pygamine.assets import save_store
from util import web


class Storage:
    def __init__(self):
        self.data = {}

    def getItem(self, key):
        return self.data.get(key)

    def setItem(self, key, value):
        self.data[key] = value

    def removeItem(self, key):
        self.data.pop(key, None)


@pytest.fixture
def browser(monkeypatch):
    storage = Storage()
    document = SimpleNamespace(
        fullscreenElement=None,
        exitFullscreen=Mock(),
        documentElement=SimpleNamespace(requestFullscreen=Mock()),
    )
    window = SimpleNamespace(document=document, open=Mock())
    monkeypatch.setattr(web, "is_web", lambda: True)
    monkeypatch.setattr(web, "_window", lambda: window)
    monkeypatch.setattr(save_store, "_browser_storage", lambda: storage)
    return storage, window


def boot():
    game = Game()
    game._prepare_run()
    return game


def test_browser_boot_does_not_import_sqlite_or_construct_splash(browser, monkeypatch):
    original = builtins.__import__

    def no_sqlite(name, *args, **kwargs):
        assert name not in ("sqlite3", "pygamine.assets.database")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_sqlite)
    game = boot()
    assert not hasattr(game, "database")
    assert game.splash is None
    for panel in (
        "menu",
        "play",
        "settings",
        "display_settings",
        "audio_settings",
        "game_settings",
        "credits",
        "thanks",
        "game",
    ):
        game.open_panel(panel)
        game.update()
        game.draw()


def test_async_run_initializes_world_and_releases_language_listener(
    browser, monkeypatch
):
    calls = []

    async def loop(game):
        assert game.tilemap is not None
        assert game.panel_manager.current_panel == "menu"
        assert game._panels_built
        calls.append(game)

    monkeypatch.setattr(Application, "run_async", loop)
    game = Game()
    cleanup = Mock(wraps=game.unwatch_language)
    monkeypatch.setattr(game, "unwatch_language", cleanup)
    asyncio.run(game.run_async())
    assert calls == [game]
    cleanup.assert_called_once()


def test_save_survives_new_game_instance_and_keeps_all_fields(browser):
    game = boot()
    game.buildings.age_number = 1
    game.add_building(3, 1, 1, "right", income_fraction=0.35)
    game.add_building(2, 2, 2, "left", booster=True)
    game.player.money = 4321
    game.tasks.restore({0}, True)
    game.save_game()
    game.save_language("tr")
    game.save_ui_scale(90)
    game.audio.set_master_volume(0.4)
    game.audio.set_music_volume(0.3)
    game.audio.set_sfx_volume(0.2)
    game.save_audio_settings()
    restored = boot()
    assert restored.player.money == 4321
    assert restored.buildings.age_number == 1
    assert [
        (
            b.level,
            b.tile.row_number,
            b.tile.column_number,
            b.is_booster,
            b.income_fraction,
        )
        for b in restored.buildings
    ] == [(3, 1, 1, False, 0.35), (2, 2, 2, True, 0.0)]
    assert restored.buildings[0].door_side == "right"
    assert restored.tasks.done == {0}
    assert restored.tasks.boost_unlocked
    assert restored.ui_scale == 90
    assert restored.load_settings().language == "tr"
    assert restored.audio.master_volume() == pytest.approx(0.4)
    assert restored.audio.music_volume() == pytest.approx(0.3)
    assert restored.audio.sfx_volume() == pytest.approx(0.2)
    restored.new_game()
    fresh = boot()
    assert fresh.player.money == fresh.starting_money
    assert not fresh.buildings
    assert fresh.load_settings().language == "tr"
    assert fresh.audio.master_volume() == pytest.approx(0.4)


def test_exit_and_escape_stay_in_browser(browser):
    game = boot()
    game.exit = Mock(side_effect=AssertionError("browser must keep running"))
    game.open_panel("exit")
    assert game.panel_manager.current_panel == "thanks"
    game.on_exit_request()
    assert game.panel_manager.current_panel == "menu"
    game.on_exit_request()
    assert game.panel_manager.current_panel == "thanks"
    game.handle_thanks_events(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))
    browser[1].open.assert_called_once_with(
        "https://umutcanekinci.itch.io/highrise", "_blank"
    )


def test_hidden_desktop_rows_cannot_be_clicked_and_stay_hidden_after_rebuild(browser):
    game = boot()
    for scale in (80, 100, 125):
        game.set_ui_scale(scale)
        for panel_name, prefix, handler in (
            ("display_settings", "window_size", game.handle_display_settings_events),
            ("game_settings", "skip_intro", game.handle_game_settings_events),
        ):
            panel = game.panel_manager[panel_name]
            game.mouse.position = panel[prefix + "_plus_button"].rect.center
            assert not panel[prefix + "_plus_button"].active
            assert not panel[prefix + "_entry_text"].active
            before = game.resolution, game.skip_intro
            handler(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1))
            assert (game.resolution, game.skip_intro) == before


def test_leaving_board_mid_merge_saves_finished_result_for_reload(browser):
    game = boot()
    game.add_building(1, 1, 1, "left", income_fraction=0.7)
    game.add_building(1, 1, 2, "right", income_fraction=0.8)
    game.open_panel("game")
    game.move_buildings("left")
    assert game.buildings.is_busy()
    game.on_exit_request()
    assert game.panel_manager.current_panel == "menu"
    restored = boot()
    assert len(restored.buildings) == 1
    building = restored.buildings[0]
    assert building.level == 2
    assert building.income_fraction == pytest.approx(0.5)
    assert restored.player.money == game.starting_money + 1
    assert not restored.buildings.is_busy()


def test_thanks_clears_old_frame_pixels(browser):
    game = boot()
    game.open_panel("exit")
    game.cloud_animation.clouds.clear()
    game.window.fill("magenta")
    game.draw()
    assert game.window.get_at((0, 0)) == pygame.Color("yellow")


def test_f11_uses_browser_fullscreen(browser):
    game = boot()
    game._handle_core_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11))
    browser[1].document.documentElement.requestFullscreen.assert_called_once()
    browser[1].document.fullscreenElement = object()
    game.cycle_window_mode()
    browser[1].document.exitFullscreen.assert_called_once()


def test_fullscreen_label_follows_delayed_browser_transition_and_native_escape(browser):
    game = boot()
    game.clock = Mock(get_time=lambda: 0)
    game.set_window_mode_label = Mock(wraps=game.set_window_mode_label)
    game.update()
    game.set_window_mode_label.reset_mock()
    game.cycle_window_mode()
    game.update()
    game.set_window_mode_label.assert_not_called()
    browser[1].document.fullscreenElement = object()
    game.update()
    game.set_window_mode_label.assert_called_once()
    game.update()
    game.set_window_mode_label.assert_called_once()
    browser[1].document.fullscreenElement = None
    game.update()
    assert game.set_window_mode_label.call_count == 2


def test_browser_preserves_desktop_world_update_rate(browser):
    game = boot()
    game.clock = Mock(get_time=lambda: 1000 / 60)
    game._update_world = Mock()
    for _ in range(60):
        game.update()
    assert game._update_world.call_count == game.settings["window"]["fps"]
    game._update_world.reset_mock()
    game.clock = Mock(get_time=lambda: 60_000)
    game.update()
    assert game._update_world.call_count <= 17
