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
    "credits",
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


def test_a_scale_change_leaves_the_world_alone():
    game = started_game()
    game.add_building(1, 0, 0)
    game.add_building(2, 1, 1)
    game.set_age(1)
    game.tile_selector.is_active = True
    before = list(game.buildings)
    timers = [[c.fire_at for c in b._scheduled] for b in before]
    money = game.player.money

    for scale in (80, 125, 100):
        game.set_ui_scale(scale)

    assert all(a is b for a, b in zip(game.buildings, before)) and len(
        game.buildings
    ) == len(before)
    assert [[c.fire_at for c in b._scheduled] for b in game.buildings] == timers
    assert game.buildings.age_number == 1
    assert game.player.money == money
    assert game.tile_selector.is_active
    assert game.panel_manager["game"]["selection_mode_button"]._base_state == "on"


def test_rebuilding_the_panels_does_not_pile_up_children_on_the_info_panel_root():
    game = started_game()
    count = len(game.info_panel.root._children)
    assert count > 0

    for scale in (80, 90, 100, 110, 125, 80, 100):
        game.set_ui_scale(scale)

    assert len(game.info_panel.root._children) == count


@pytest.mark.parametrize("scale", UI_SCALES)
def test_on_a_taller_canvas_the_layout_follows_the_canvas(scale):
    game = started_game((1920, 1080))
    game.set_ui_scale(scale)
    menu = game.panel_manager["menu"]["menu_panel"].rect.copy()
    button = game.panel_manager["menu"]["play_button"].rect.copy()
    toolbar = game.panel_manager["game"]["expand_button"].rect.copy()

    game.set_resolution((1920, 1200))

    assert game.size == (1920, 1200)
    panel = game.panel_manager["menu"]
    # Centered chrome moves down by half of the extra 120 px, all of it alike.
    assert panel["menu_panel"].rect.y - menu.y == 60
    assert panel["play_button"].rect.y - button.y == 60
    assert panel["menu_panel"].rect.x == menu.x
    # The HUD hugs the bottom edge of the taller canvas.
    hud = game.panel_manager["game"]
    assert hud["game_panel"].rect.bottom == 1200 - round(15 * scale / 100)
    assert hud["expand_button"].rect.y - toolbar.y == 120


BACK_BUTTONS = (
    ("settings", "settings_panel", ("settings_back_button",)),
    ("display_settings", "display_settings_panel", ("display_back_button",)),
    # CANCEL and SAVE are a pair, centered together.
    ("audio_settings", "audio_settings_panel", ("cancel_button", "save_button")),
    ("game_settings", "game_settings_panel", ("game_settings_back_button",)),
    ("credits", "credits_panel", ("credits_back_button",)),
)


@pytest.mark.parametrize("resolution", [(1280, 720), (1920, 1080)])
@pytest.mark.parametrize("scale", UI_SCALES)
def test_every_back_button_is_centered_on_its_page(resolution, scale):
    game = started_game(resolution)
    game.set_ui_scale(scale)

    window = pygame.Rect((0, 0), game.size)
    for panel, body_name, names in BACK_BUTTONS:
        page = game.panel_manager[panel]
        rects = [page[name].rect for name in names]
        row = rects[0].unionall(rects[1:])
        assert abs(row.centerx - window.centerx) <= 1, (panel, scale, row)
        # The page's own panel is centered too, so they share one center line.
        body = page[body_name].rect
        assert abs(body.centerx - window.centerx) <= 1, (panel, scale, body)


HEADERS = (
    ("menu", "menu_title", "menu_panel"),
    ("settings", "settings_title", "settings_panel"),
    ("play", "play_title", "play_panel"),
    ("display_settings", "display_settings_title", "display_settings_panel"),
    ("audio_settings", "audio_settings_title", "audio_settings_panel"),
    ("audio_settings", "audio_settings_title", "audio_settings_panel_no_music"),
    ("game_settings", "game_settings_title", "game_settings_panel"),
    ("credits", "credits_title", "credits_panel"),
)


@pytest.mark.parametrize("scale", UI_SCALES)
def test_every_header_plate_is_as_wide_as_its_body_panel(scale):
    game = started_game()
    game.set_ui_scale(scale)

    for panel, header_name, body_name in HEADERS:
        page = game.panel_manager[panel]
        header, body = page[header_name].rect, page[body_name].rect
        assert abs(header.width - body.width) <= 1, (panel, body_name, scale)
        assert abs(header.left - body.left) <= 1, (panel, body_name, scale)
