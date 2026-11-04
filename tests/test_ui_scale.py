"""The UI scale setting on a real Game (the real panels.yaml): persistence,
hit-testing, layout and text fit at every step, in both languages and at both
supported window sizes. The window loop and splash are stubbed out, as in
test_music.py."""

import pygame
import pytest

import pygamine
from app.game import Game
from pygamine import TextObject
from pygamine.util.localization import localization
from ui.ui_scale import DEFAULT_UI_SCALE, UI_SCALES, step_ui_scale

PANELS = (
    "menu",
    "play",
    "settings",
    "display_settings",
    "audio_settings",
    "game_settings",
    "developer",
    "game",
)


@pytest.fixture(autouse=True)
def headless_run(monkeypatch) -> None:
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)


def started_game(resolution=(1920, 1080)) -> Game:
    game = Game()
    game.set_windowed()
    game.set_resolution(resolution)
    game.run()
    game.open_panel("display_settings")
    return game


def click(game: Game, name: str, panel: str = "display_settings") -> None:
    """A real left click at the middle of the named widget."""
    button = game.panel_manager[panel][name]
    center = button.rect.center
    game.mouse.position = center
    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        game.handle_event(pygame.event.Event(kind, button=1, pos=center))


def test_the_default_is_one_of_the_steps():
    assert DEFAULT_UI_SCALE in UI_SCALES


def test_stepping_stops_at_both_ends():
    assert step_ui_scale(UI_SCALES[0], -1) == UI_SCALES[0]
    assert step_ui_scale(UI_SCALES[-1], 1) == UI_SCALES[-1]
    assert step_ui_scale(100, 1) == 110


def test_the_scale_is_saved_the_moment_it_changes_and_survives_a_restart():
    game = started_game()
    game.set_ui_scale(80)

    restarted = started_game()

    assert restarted.ui_scale == 80
    width = restarted.panel_manager["menu"]["menu_panel"].rect.width
    assert width == round(440 * 0.8)


def test_an_unknown_scale_is_rejected_before_anything_changes():
    game = started_game()

    with pytest.raises(ValueError):
        game.set_ui_scale(95)

    assert game.ui_scale == DEFAULT_UI_SCALE
    assert game.load_settings().ui_scale == DEFAULT_UI_SCALE


def test_reset_restores_the_default_and_saves_it():
    game = started_game()
    game.set_ui_scale(125)

    click(game, "ui_scale_reset_button")

    assert game.ui_scale == DEFAULT_UI_SCALE
    assert game.load_settings().ui_scale == DEFAULT_UI_SCALE
    assert game.panel_manager["display_settings"]["ui_scale_entry_text"].text == (
        f"%{DEFAULT_UI_SCALE}"
    )
    assert game.panel_manager.current_panel == "display_settings"


@pytest.mark.parametrize("resolution", [(1280, 720), (1920, 1080)])
@pytest.mark.parametrize("scale", UI_SCALES)
def test_the_buttons_of_a_scaled_page_hit_the_right_widget(resolution, scale):
    game = started_game(resolution)
    game.set_ui_scale(scale)

    click(game, "ui_scale_plus_button")
    assert game.ui_scale == step_ui_scale(scale, 1)

    click(game, "ui_scale_minus_button")
    click(game, "ui_scale_minus_button")
    assert game.ui_scale == step_ui_scale(step_ui_scale(scale, 1), -2)

    click(game, "display_back_button")
    assert game.panel_manager.current_panel == "settings"


@pytest.mark.parametrize("language", ["en", "tr"])
@pytest.mark.parametrize("resolution", [(1280, 720), (1920, 1080)])
@pytest.mark.parametrize("scale", UI_SCALES)
def test_every_panel_stays_on_screen_and_its_text_fits(language, resolution, scale):
    game = started_game(resolution)
    localization.set_language(language)
    game.set_ui_scale(scale)
    screen = pygame.Rect((0, 0), game.size)

    for panel in PANELS:
        game.open_panel(panel)
        for obj in game.panel_manager[panel].values():
            rect = getattr(obj, "rect", None)
            if not isinstance(rect, pygame.Rect) or not obj.active:
                continue
            where = (panel, rect, language, scale)
            if isinstance(obj, TextObject):
                # A text rect is the font's line box, a little taller than the
                # glyphs: its width must fit and its middle must sit in the box.
                box = rect.parent
                assert box.left <= rect.left and rect.right <= box.right, where
                assert box.top <= rect.centery <= box.bottom, where
            elif rect.width <= screen.width:  # not the extra-wide HUD background
                assert screen.contains(rect), where


@pytest.mark.parametrize("scale", UI_SCALES)
def test_the_hud_bar_hugs_the_bottom_edge_and_the_world_is_not_scaled(scale):
    default = started_game()
    reference = default.panel_manager["game"]["tiles"][0][0].rect.size
    game = started_game()
    game.set_ui_scale(scale)
    panel = game.panel_manager["game"]

    assert panel["game_panel"].rect.bottom == game.size[1] - round(15 * scale / 100)
    assert panel["expand_button"].rect.width == round(200 * scale / 100)
    assert panel["tiles"][0][0].rect.size == reference
