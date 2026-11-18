"""Browser startup, navigation and persistence with a real game and a fake page."""

import asyncio
import json
import logging
import platform
import subprocess
import sys
import textwrap
from unittest.mock import Mock

import pygame
import pytest

from app.game import WEB_FPS, Game
from app.web_persistence import AUTOSAVE_DELAY_MS, AUTOSAVE_INTERVAL_MS
from pygamine import Application


def boot():
    game = Game()
    game._prepare_run()
    return game


def stored(browser, name="highrise-save"):
    """The raw text the page's localStorage holds for a store, or None."""
    items = browser.localStorage.items
    return next((v for k, v in items.items() if k.endswith(f"{name}.json")), None)


def test_browser_boot_does_not_import_sqlite_or_construct_splash(browser):
    script = textwrap.dedent("""
        import builtins, platform, sys
        original = builtins.__import__
        def no_sqlite(name, *args, **kwargs):
            assert not name.startswith(("sqlite3", "pygamine.assets.database")), name
            return original(name, *args, **kwargs)
        builtins.__import__ = no_sqlite
        sys.path[:0] = ["src", "src/pygamine"]
        from types import SimpleNamespace
        from app.game import Game
        storage = SimpleNamespace(
            getItem=lambda key: None, setItem=lambda k, v: None, removeItem=lambda k: None
        )
        platform.window = SimpleNamespace(
            localStorage=storage,
            document=SimpleNamespace(
                fullscreenElement=None,
                getElementById=lambda name: SimpleNamespace(textContent=""),
            ),
        )
        sys.platform = "emscripten"
        game = Game()
        game._prepare_run()
        assert not hasattr(game, "database")
        assert game.splash is None
        assert "sqlite3" not in sys.modules
    """)
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stdout + result.stderr
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
    browser.open.assert_called_once_with(
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
    game.cloud_animation.clear()
    game.window.fill("magenta")
    game.draw()
    assert game.window.get_at((0, 0)) == pygame.Color("yellow")


def test_f11_uses_browser_fullscreen(browser):
    game = boot()
    game._handle_core_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11))
    browser.document.documentElement.requestFullscreen.assert_called_once()
    browser.document.fullscreenElement = object()
    game.cycle_window_mode()
    browser.document.exitFullscreen.assert_called_once()


def test_fullscreen_label_follows_delayed_browser_transition_and_native_escape(browser):
    game = boot()
    game.open_panel("display_settings")
    game.clock = Mock(get_time=lambda: 0)
    game.set_window_mode_label = Mock(wraps=game.set_window_mode_label)
    game.update()
    game.set_window_mode_label.reset_mock()
    game.cycle_window_mode()
    game.update()
    game.set_window_mode_label.assert_not_called()
    browser.document.fullscreenElement = object()
    game.update()
    game.set_window_mode_label.assert_called_once()
    game.update()
    game.set_window_mode_label.assert_called_once()
    browser.document.fullscreenElement = None
    game.update()
    assert game.set_window_mode_label.call_count == 2


def test_empty_expanded_board_can_continue_after_reload(browser):
    game = boot()
    game.player.money = 10000
    game.expand()
    game.save_game()
    restored = boot()
    assert restored.has_save_data()
    restored.play()
    assert restored.panel_manager.current_panel == "play"
    assert restored.tilemap.row_count == 3
    assert restored.player.money == game.player.money


def motion_steps_per_second(game, frames, frame_ms):
    """Counts the frame-count motion steps (buildings, both kinds of clouds) over `frames`
    simulated frames of `frame_ms` each on the game panel."""
    game.open_panel("game")
    game.clock = Mock(get_time=lambda: frame_ms)
    counts = {"buildings": 0, "clouds": 0, "transition_clouds": 0}
    for key, owner in (
        ("buildings", game.buildings),
        ("clouds", game.panel_manager["game"]["clouds"]),
        ("transition_clouds", game.cloud_animation),
    ):

        def count(key=key):
            counts[key] += 1

        owner.update = count
    for _ in range(frames):
        game.update()
    return counts


def test_the_browser_steps_motion_as_often_per_second_as_desktop(browser, monkeypatch):
    web_game = boot()
    fps = web_game.settings["window"]["fps"]
    web = motion_steps_per_second(web_game, WEB_FPS, 1000 / WEB_FPS)
    monkeypatch.setattr(sys, "platform", "win32")
    desktop = motion_steps_per_second(boot(), fps, 1000 / fps)
    # The desktop steps the buildings twice an update (the panel's and the world's own).
    assert desktop == {
        "buildings": 2 * fps,
        "clouds": fps,
        "transition_clouds": fps,
    }
    for key, steps in desktop.items():
        assert abs(web[key] - steps) <= 2, (key, web, desktop)


def test_a_long_stall_does_not_make_the_browser_catch_up_for_ever(browser):
    game = boot()
    counts = motion_steps_per_second(game, 1, 60_000)
    assert counts["transition_clouds"] <= 9


@pytest.mark.parametrize("raw", ["{broken", "[]", "null"])
def test_unreadable_save_is_kept_until_an_explicit_new_game(browser, raw, caplog):
    path = boot().web_save.path.as_posix()
    browser.localStorage.setItem(f"pygamine:{path}", raw)
    with caplog.at_level(logging.WARNING):
        restored = boot()
    assert "unreadable" in caplog.text
    assert restored.web_save_invalid
    assert "could not be loaded" in browser.notice.textContent
    assert not restored.buildings
    assert restored.has_save_data()
    restored.play()
    assert restored.panel_manager.current_panel == "play"
    assert not restored.panel_manager["play"]["continue_button"].active
    restored.save_game()
    assert browser.localStorage.getItem(f"pygamine:{path}") == raw
    restored.new_game()
    assert not restored.web_save_invalid
    assert restored.panel_manager["play"]["continue_button"].active
    assert browser.localStorage.getItem(f"pygamine:{path}") is None


def test_damaged_values_are_held_to_valid_ones_before_the_board_changes(browser):
    game = boot()
    game.web_save.save(
        {
            "age": 999,
            "size": 999999,
            "money": None,
            "buildings": [
                {"row": 1, "column": 1, "level": 1},
                {"row": 2, "level": 1},  # no column
                {"row": 1, "column": 1, "level": 2},  # same tile again
                {"row": 9, "column": 9, "level": 1},  # off the board
                {"row": 2, "column": 2, "level": 99, "income_fraction": "x"},
                "bad",
            ],
        }
    )
    game.web_settings.save(
        {"master_volume": None, "music_volume": "bad", "sfx_volume": []}
    )
    restored = boot()
    assert restored.buildings.age_number == restored.buildings.max_age_number
    assert restored.tilemap.row_count == restored.max_size
    assert restored.player.money == restored.starting_money
    assert [(b.tile.row_number, b.tile.column_number) for b in restored.buildings] == [
        (1, 1),
        (2, 2),
    ]
    assert restored.buildings[1].level == restored.max_building_level
    assert restored.audio.master_volume() == 1.0
    assert restored.audio.music_volume() == restored.default_music_volume
    assert restored.audio.sfx_volume() == restored.default_sfx_volume


def test_bad_task_indices_are_dropped_and_the_good_one_kept(browser):
    boot().web_save.save({"tasks_done": [0, "bad", {}, None, True, -1, 999]})
    assert boot().tasks.done == {0}


def test_corrupt_settings_are_logged_and_the_game_still_starts(browser, caplog):
    game = boot()
    path = game.web_settings.path.as_posix()
    browser.localStorage.setItem(f"pygamine:{path}", "{broken")
    with caplog.at_level(logging.WARNING):
        restored = boot()
    assert "settings are unreadable" in caplog.text
    assert restored.ui_scale == restored.load_settings().ui_scale


def test_board_changes_save_after_a_short_wait(browser, monkeypatch):
    now = {"t": 10_000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now["t"])
    game = boot()
    game.open_panel("game")
    game.create_building()
    game.create_building()  # joins the first wait: one write
    assert stored(browser) is None
    game.update()
    assert stored(browser) is None
    now["t"] += AUTOSAVE_DELAY_MS
    game.update()
    assert len(json.loads(stored(browser))["buildings"]) == 2
    building = game.buildings[0]
    game.info_panel.building = building
    game._sell(building)
    now["t"] += AUTOSAVE_DELAY_MS
    game.update()
    assert len(json.loads(stored(browser))["buildings"]) == 1


def test_autosave_waits_for_a_merge_to_finish(browser, monkeypatch):
    now = {"t": 10_000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now["t"])
    game = boot()
    game.add_building(1, 1, 1, "left")
    game.add_building(1, 1, 2, "right")
    game.open_panel("game")
    game.move_buildings("left")
    game.request_autosave()
    now["t"] += AUTOSAVE_DELAY_MS
    assert game.buildings.is_busy()
    game.autosave_if_due()
    assert stored(browser) is None
    for _ in range(600):
        game.update()
        if not game.buildings.is_busy():
            break
    game.update()
    assert [b["level"] for b in json.loads(stored(browser))["buildings"]] == [2]


def test_refused_write_shows_one_notice_and_a_later_save_clears_it(
    browser, monkeypatch
):
    game = boot()
    game.add_building(1, 1, 1, "left")
    game.save_game()
    before = stored(browser)
    original = browser.localStorage.setItem
    monkeypatch.setattr(
        browser.localStorage, "setItem", Mock(side_effect=RuntimeError("quota"))
    )
    game.player.money += 5
    game.save_game()
    assert stored(browser) == before
    assert "Progress will be lost" in browser.notice.textContent
    monkeypatch.setattr(browser.localStorage, "setItem", original)
    game.save_game()
    assert browser.notice.textContent == ""
    assert json.loads(stored(browser))["money"] == game.player.money


def test_idle_income_is_saved_by_the_periodic_check(browser, monkeypatch):
    now = {"t": 10_000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now["t"])
    game = boot()
    game.open_panel("game")
    game.update()
    assert stored(browser) is None  # nothing changed: no write
    game.player.money += 77  # a payout: nobody asked for a save
    now["t"] += AUTOSAVE_INTERVAL_MS
    game.update()
    assert json.loads(stored(browser))["money"] == game.player.money
    writes = Mock(wraps=game.web_save.save)
    monkeypatch.setattr(game.web_save, "save", writes)
    now["t"] += AUTOSAVE_INTERVAL_MS
    game.update()
    writes.assert_not_called()  # unchanged since the last save


def test_a_move_without_a_merge_is_saved(browser, monkeypatch):
    now = {"t": 10_000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now["t"])
    game = boot()
    game.add_building(1, 1, 1, "left")
    game.open_panel("game")
    game.move_buildings("right")
    for _ in range(600):
        game.update()
        if not game.buildings.is_busy():
            break
    now["t"] += AUTOSAVE_DELAY_MS
    game.update()
    assert json.loads(stored(browser))["buildings"][0]["column"] == 2


def test_blocked_storage_shows_the_notice_even_though_saving_seems_to_work(
    browser, monkeypatch
):
    class Blocked:
        document = browser.document

        @property
        def localStorage(self):  # noqa: N802
            raise RuntimeError("SecurityError")

    monkeypatch.setattr(platform, "window", Blocked())
    game = boot()
    assert "Progress will be lost" in browser.notice.textContent
    game.save_game()  # SaveStore keeps it in memory: the read-back matches
    assert game.web_save.load()["money"] == game.player.money
    assert "Progress will be lost" in browser.notice.textContent


def test_a_new_game_does_not_read_the_stored_settings_again(browser, monkeypatch):
    game = boot()
    game.audio.set_music_volume(0.3)
    game.save_audio_settings()
    reads = Mock(wraps=game.web_settings.load)
    monkeypatch.setattr(game.web_settings, "load", reads)
    game.new_game()
    reads.assert_not_called()
    assert game.audio.music_volume() == pytest.approx(0.3)


def test_a_hidden_continue_is_out_of_the_play_menus_navigation(browser):
    game = boot()
    game.web_save.save({"age": 0})
    path = game.web_save.path.as_posix()
    browser.localStorage.setItem(f"pygamine:{path}", "{broken")
    game = boot()
    controller = game.menu_controllers["play"]
    panel = game.panel_manager["play"]
    assert panel["continue_button"] not in controller.buttons
    assert controller.focused is panel["new_game_button"]
    game.new_game()  # replaces the unreadable save: Continue is back, first in line
    assert controller.buttons[0] is panel["continue_button"]
    assert controller.focused is panel["continue_button"]
    assert not panel["new_game_button"].focused
