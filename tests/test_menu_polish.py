"""The menu polish: button colors, page headers, CONTINUE first, percent format.
Real Game() and the real config/panels.yaml; the window loop and splash are stubbed
out, as in test_ui_scale.py."""

from pathlib import Path

import pygame
import pytest
import yaml

import pygamine
from app.game import (
    Game,
    format_percent,
    format_volume,
)
from pygamine.util.localization import localization
from ui.ui_scale import UI_SCALES

PANELS_YAML = Path("config/panels.yaml")


@pytest.fixture(autouse=True)
def headless_run(monkeypatch) -> None:
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)


def started_game() -> Game:
    """A real Game on its first page."""
    game = Game()
    game.set_windowed()
    game.set_resolution((1920, 1080))
    game.run()
    return game


# ── button colors ─────────────────────────────────────────────────────────


def _template_asset(templates: dict, name: str) -> str:
    """The `asset` of a template, following its `extends` chain."""
    while "asset" not in templates[name]:
        name = templates[name]["extends"]
    return templates[name]["asset"]


def _button_assets() -> dict[str, str]:
    """{"panel.button": asset key} of every `*_button` object in panels.yaml."""
    config = yaml.safe_load(PANELS_YAML.read_text(encoding="utf-8"))
    templates = config["object_templates"]
    found: dict[str, str] = {}

    def visit(panel: str, objects: dict) -> None:
        for name, obj in objects.items():
            if name.endswith("_button"):
                found[f"{panel}.{name}"] = obj.get("asset") or _template_asset(
                    templates, obj["extends"]
                )
            visit(panel, obj.get("objects") or {})

    for panel, definition in config["panels"].items():
        visit(panel, definition["objects"])
    return found


EXPECTED_BUTTON_COLORS = {
    # red: leave, cancel, destroy
    "menu.exit_button": "red_button",
    "settings.settings_back_button": "red_button",
    "play.play_back_button": "red_button",
    "display_settings.display_back_button": "red_button",
    "audio_settings.cancel_button": "red_button",
    "game_settings.game_settings_back_button": "red_button",
    "credits.credits_back_button": "red_button",
    "game.sell_button": "red_button",
    # green: the main "go" action
    "menu.play_button": "green_button",
    "play.continue_button": "green_button",
    "audio_settings.save_button": "green_button",
    "game.build_button": "green_button",
    "game.boost_button": "green_button",
    # blue: everything else
    "menu.settings_button": "blue_button",
    "menu.credits_button": "blue_button",
    "play.new_game_button": "blue_button",
    "settings.display_settings_button": "blue_button",
    "settings.audio_settings_button": "blue_button",
    "settings.game_settings_button": "blue_button",
    "display_settings.ui_scale_reset_button": "blue_button",
    "game.expand_button": "blue_button",
}

# Buttons outside the scheme, with the reason.
OUTSIDE_THE_SCHEME = {
    "game.close_button",  # the info panel's X
    "game.selection_mode_button",  # a green/red toggle of the toolbar
    "game.next_age_button",  # a toolbar action like BUILD; the owner didn't list it
}


def test_every_menu_button_follows_the_color_scheme():
    found = _button_assets()
    assert {k: found[k] for k in EXPECTED_BUTTON_COLORS} == EXPECTED_BUTTON_COLORS


def test_a_new_button_must_be_added_to_the_color_table():
    steppers = ("minus_button", "plus_button")  # round blue circles, no scheme
    unlisted = {
        name
        for name in _button_assets()
        if not name.endswith(steppers)
        and name not in EXPECTED_BUTTON_COLORS
        and name not in OUTSIDE_THE_SCHEME
    }
    assert unlisted == set()


def test_no_object_template_extends_another_template():
    # pygamine resolves `extends` one level only (pygamine #46), which dropped the
    # hover image and nine_slice of the red and green buttons.
    config = yaml.safe_load(PANELS_YAML.read_text(encoding="utf-8"))

    extending = [n for n, t in config["object_templates"].items() if "extends" in t]

    assert extending == []


def test_every_colored_menu_button_has_a_hover_image():
    game = started_game()
    missing = []
    for path in EXPECTED_BUTTON_COLORS:
        panel, name = path.split(".")
        # The hover artwork is the engine's private state; there is no public view.
        if None not in game.panel_manager[panel][name]._hover_images:
            missing.append(path)

    assert missing == []


def test_red_and_green_menu_buttons_load_with_the_blue_ones_nine_slice():
    game = started_game()
    # Red, green and blue buttons built from the menu_btn templates.
    buttons = ("menu.play_button", "menu.exit_button", "menu.credits_button")
    buttons += ("play.continue_button", "play.play_back_button")

    slices = {}
    for path in buttons:
        panel, name = path.split(".")
        slices[path] = game.panel_manager[panel][name]._nine_slice  # engine-private

    assert slices == dict.fromkeys(buttons, 20)


# ── CONTINUE first ────────────────────────────────────────────────────────


@pytest.mark.parametrize("scale", UI_SCALES)
def test_continue_is_above_new_game_above_go_back(scale):
    game = started_game()
    game.set_ui_scale(scale)
    page = game.panel_manager["play"]

    assert (
        page["continue_button"].rect.top
        < page["new_game_button"].rect.top
        < page["play_back_button"].rect.top
    )


def test_the_keyboard_focus_order_follows_the_buttons():
    game = started_game()
    page = game.panel_manager["play"]

    assert game.menu_controllers["play"].buttons == [
        page["continue_button"],
        page["new_game_button"],
        page["play_back_button"],
    ]


# ── percent format ────────────────────────────────────────────────────────


@pytest.mark.parametrize(("language", "text"), [("en", "60%"), ("tr", "%60")])
def test_percent_text_follows_the_language(language, text):
    localization.set_language(language)
    assert format_percent(60) == text
    assert format_volume(0.6) == text


@pytest.mark.parametrize(
    ("language", "template"), [("tr", "%{value}"), ("en", "{value}%")]
)
def test_open_values_re_text_when_the_language_changes(language, template):
    game = started_game()
    game.set_ui_scale(110)
    other = "en" if language == "tr" else "tr"
    game.watch_language()
    try:
        localization.set_language(other)
        localization.set_language(language)
    finally:
        game.unwatch_language()

    audio = game.panel_manager["audio_settings"]
    shown = {
        "master_volume_entry_text": game.audio.master_volume(),
        "music_volume_entry_text": game.audio.music_volume(),
        "sfx_volume_entry_text": game.audio.sfx_volume(),
    }
    for name, volume in shown.items():
        assert audio[name].text == template.format(value=round(volume * 100)), name
    ui_scale = game.panel_manager["display_settings"]["ui_scale_entry_text"]
    assert ui_scale.text == template.format(value=110)


# ── credits: lockup and profile rows ──────────────────────────────────────


@pytest.mark.parametrize("language", ["en", "tr"])
@pytest.mark.parametrize("scale", UI_SCALES)
def test_the_credits_lockup_and_profile_rows_fit_and_are_centered(language, scale):
    game = started_game()
    localization.set_language(language)
    game.set_ui_scale(scale)
    scroller = game.panel_manager["credits"]["credits_scroller"]
    # The scroller takes its targets out of the panel and has no public way to list
    # them, so this reads its private lists (the objects are otherwise unreachable).
    page = {
        obj_name: obj
        for obj_name, obj in zip(scroller._target_names, scroller._targets)
    }
    viewport = scroller.rect
    window = pygame.Rect((0, 0), game.size)

    lockup = page["credits_lockup"].rect
    assert viewport.left <= lockup.left and lockup.right <= viewport.right
    assert abs(lockup.centerx - window.centerx) <= 1

    for icon, name in (
        ("credits_github_icon", "credits_github_name"),
        ("credits_itch_icon", "credits_itch_name"),
    ):
        pair = page[icon].rect.union(page[name].rect)
        where = (icon, language, scale)
        assert viewport.left <= pair.left and pair.right <= viewport.right, where
        assert abs(pair.centerx - window.centerx) <= 4, (
            where
        )  # hand-placed x, rounded by the scale
        assert page[icon].rect.right < page[name].rect.left, where
