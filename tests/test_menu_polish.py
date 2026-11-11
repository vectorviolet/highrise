"""The menu polish: button colors, page headers, CONTINUE first, percent format.
Real Game() and the real config/panels.yaml; the window loop and splash are stubbed
out, as in test_ui_scale.py."""

from pathlib import Path

import pygame
import pytest
import yaml

import app.game as game_module
import pygamine
from app.game import (
    HEADER_STYLES_FOLDER,
    Game,
    format_percent,
    format_volume,
    header_style_manifest,
)
from pygamine import TextObject
from pygamine.ecs.state_object import HoverableStateObject
from pygamine.util.localization import localization
from ui.ui_scale import UI_SCALES

PANELS_YAML = Path("config/panels.yaml")
HEADER_STYLES = sorted(p.stem for p in HEADER_STYLES_FOLDER.glob("*.yaml"))
SUB_PAGES = (
    "play",
    "settings",
    "display_settings",
    "audio_settings",
    "game_settings",
    "credits",
)


@pytest.fixture(autouse=True)
def headless_run(monkeypatch) -> None:
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)


def started_game(monkeypatch, style: str | None = None) -> Game:
    """A real Game on its first page; `style` overrides settings.yaml's header style."""
    if style is not None:
        real = game_module.header_style_manifest
        monkeypatch.setattr(
            game_module, "header_style_manifest", lambda _style: real(style)
        )
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


# ── CONTINUE first ────────────────────────────────────────────────────────


@pytest.mark.parametrize("scale", UI_SCALES)
def test_continue_is_above_new_game_above_go_back(monkeypatch, scale):
    game = started_game(monkeypatch)
    game.set_ui_scale(scale)
    page = game.panel_manager["play"]

    assert (
        page["continue_button"].rect.top
        < page["new_game_button"].rect.top
        < page["play_back_button"].rect.top
    )


def test_the_keyboard_focus_order_follows_the_buttons(monkeypatch):
    game = started_game(monkeypatch)
    page = game.panel_manager["play"]

    assert game.menu_controllers["play"].buttons == [
        page["continue_button"],
        page["new_game_button"],
        page["play_back_button"],
    ]


# ── page headers ──────────────────────────────────────────────────────────


def test_the_main_menu_has_no_title(monkeypatch):
    game = started_game(monkeypatch)
    assert "menu_title" not in game.panel_manager["menu"]


@pytest.mark.parametrize("style", HEADER_STYLES)
@pytest.mark.parametrize("scale", UI_SCALES)
def test_every_sub_page_header_sits_in_the_same_place(monkeypatch, style, scale):
    game = started_game(monkeypatch, style)
    game.set_ui_scale(scale)
    window = pygame.Rect((0, 0), game.size)

    rects = {
        page: tuple(game.panel_manager[page][f"{page}_title"].rect)
        for page in SUB_PAGES
    }
    assert len(set(rects.values())) == 1, rects
    assert abs(pygame.Rect(rects["play"]).centerx - window.centerx) <= 1


@pytest.mark.parametrize("style", HEADER_STYLES)
def test_a_header_has_no_hover_state(monkeypatch, style):
    game = started_game(monkeypatch, style)
    for page in SUB_PAGES:
        header = game.panel_manager[page][f"{page}_title"]
        assert not isinstance(header, HoverableStateObject), page


@pytest.mark.parametrize("style", HEADER_STYLES)
@pytest.mark.parametrize("language", ["en", "tr"])
@pytest.mark.parametrize("scale", UI_SCALES)
def test_header_text_fits_its_plate(monkeypatch, style, language, scale):
    game = started_game(monkeypatch, style)
    localization.set_language(language)
    game.set_ui_scale(scale)

    for page in SUB_PAGES:
        game.open_panel(page)
        header = game.panel_manager[page][f"{page}_title"].rect
        text = game.panel_manager[page][f"{page}_title_text"]
        assert isinstance(text, TextObject)
        where = (style, page, language, scale)
        assert header.left < text.rect.left and text.rect.right < header.right, where
        assert abs(header.centery - text.rect.centery) <= 2, where


@pytest.mark.parametrize(("style", "image"), [("a", "plate"), ("b", "banner")])
def test_a_style_picks_the_header_image(monkeypatch, style, image):
    game = started_game(monkeypatch, style)
    assert Path(str(game.assets.image_path("header_plate"))).stem == image


def test_the_default_style_is_a():
    settings = yaml.safe_load(Path("config/settings.yaml").read_text(encoding="utf-8"))
    assert settings["ui"]["header_style"] == "a"
    assert HEADER_STYLES == ["a", "b"]


def test_an_unknown_header_style_is_refused():
    with pytest.raises(ValueError, match="Unknown header style 'z'"):
        header_style_manifest("z")


# ── percent format ────────────────────────────────────────────────────────


@pytest.mark.parametrize(("language", "text"), [("en", "60%"), ("tr", "%60")])
def test_percent_text_follows_the_language(language, text):
    localization.set_language(language)
    assert format_percent(60) == text
    assert format_volume(0.6) == text


@pytest.mark.parametrize(
    ("language", "template"), [("tr", "%{value}"), ("en", "{value}%")]
)
def test_open_values_re_text_when_the_language_changes(monkeypatch, language, template):
    game = started_game(monkeypatch)
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
        "sfx_volume_entry_text": game.audio.sfx_volume(),
    }
    for name, volume in shown.items():
        assert audio[name].text == template.format(value=round(volume * 100)), name
    ui_scale = game.panel_manager["display_settings"]["ui_scale_entry_text"]
    assert ui_scale.text == template.format(value=110)
