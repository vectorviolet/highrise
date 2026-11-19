"""Text on a button's yellow face (hover or keyboard focus) is dark navy, never white."""

import pygame
import pytest

from app.game import Game
from pygamine import HoverableStateObject, SpriteRenderer2D, TextObject
from ui.button_text import YELLOW_TEXT_COLOR, ButtonText

YELLOW_FACE = (255, 204, 0)  # assets/images/gui/Yellow: yellow_button


def luminance(color) -> float:
    def channel(value: int) -> float:
        value /= 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in color[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


@pytest.fixture
def game(monkeypatch) -> Game:
    monkeypatch.setattr(
        Game, "show_splash", lambda self: None
    )  # the intro clip takes 12 s
    game = Game()
    game._prepare_run()
    return game


def solid_colors(text: TextObject) -> set[tuple[int, int, int]]:
    """The colors of the fully opaque pixels of the text as it is drawn."""
    image = text.require_component(SpriteRenderer2D).require_image()
    return {
        tuple(image.get_at((x, y)))[:3]
        for x in range(image.get_width())
        for y in range(image.get_height())
        if image.get_at((x, y)).a == 255
    }


def hover_texts(game) -> list[tuple[str, str, ButtonText, object]]:
    found = []
    for panel_name in game.panel_manager._panels:
        for name, obj in game.panel_manager[panel_name]._objects.items():
            if not isinstance(obj, TextObject):
                continue
            parent = getattr(obj.rect.parent, "game_object", None)
            if parent is not None and getattr(parent, "focused", None) is not None:
                if hasattr(parent, "clear_hover"):
                    found.append((panel_name, name, obj, parent))
    return found


WHITE = (251, 254, 255)  # menu_btn_text


def move_mouse(button, position) -> None:
    button.handle_event(pygame.event.Event(pygame.MOUSEMOTION), position)


def test_navy_on_the_yellow_face_has_at_least_7_to_1_contrast():
    assert contrast(YELLOW_TEXT_COLOR, YELLOW_FACE) >= 7
    assert contrast((255, 255, 255), YELLOW_FACE) < 2  # what white was


def test_every_text_on_a_hoverable_button_is_a_button_text(game):
    texts = hover_texts(game)
    assert len(texts) > 20
    assert [(p, n) for p, n, text, _ in texts if not isinstance(text, ButtonText)] == []


def test_button_text_is_navy_on_hover_and_white_otherwise(game):
    game.open_panel("menu")
    button = game.panel_manager["menu"]["play_button"]
    text = game.panel_manager["menu"]["play_button_text"]
    button.focused = False
    text.update()
    assert solid_colors(text) == {WHITE}
    move_mouse(button, button.rect.center)
    text.update()
    assert solid_colors(text) == {YELLOW_TEXT_COLOR}
    move_mouse(button, (0, 0))
    text.update()
    assert solid_colors(text) == {WHITE}


def test_keyboard_focus_shows_navy_too(game):
    game.open_panel("play")
    controller = game.menu_controllers["play"]
    controller.focused.focused = False
    other = controller.buttons[1]
    other.focused = True
    text = next(t for _, _, t, parent in hover_texts(game) if parent is other)
    text.update()
    assert solid_colors(text) == {YELLOW_TEXT_COLOR}
    other.focused = False
    text.update()
    assert solid_colors(text) == {WHITE}


def test_the_thanks_button_shows_navy_when_it_is_focused(game):
    game.open_panel("thanks")
    link = game.panel_manager["thanks"]["thanks_link"]
    text = game.panel_manager["thanks"]["thanks_link_text"]
    link.focused = True
    text.update()
    assert solid_colors(text) == {YELLOW_TEXT_COLOR}


def test_a_new_label_set_while_the_button_is_yellow_stays_after_it_leaves(game):
    button = game.panel_manager["thanks"]["thanks_link"]
    text = game.panel_manager["thanks"]["thanks_link_text"]
    button.focused = True
    text.update()
    text.set_text("OTHER")
    assert text.states["default"] == "OTHER"
    button.focused = False
    text.update()
    assert text.text == "OTHER"
    assert solid_colors(text) == {WHITE}


def test_a_toggle_button_with_its_own_states_is_navy_on_hover_in_each_state(game):
    paths = game.assets
    button = HoverableStateObject(
        size=(200, 60),
        nine_slice=20,
        image_path=paths.image_path("green_button"),
        hover_image_path=paths.image_path("yellow_button"),
    )
    button.add_state(
        "off", paths.image_path("red_button"), paths.image_path("yellow_button")
    )
    text = ButtonText(
        button.rect,
        ("CENTER", "CENTER"),
        "TOGGLE",
        game.panel_manager["menu"]["play_button_text"].font,
        WHITE,
    )
    for state in (None, "off"):
        button.set_base_state(state)
        move_mouse(button, (-5000, -5000))
        text.update()
        assert text.color == WHITE, state
        move_mouse(button, button.rect.center)
        text.update()
        assert text.color == YELLOW_TEXT_COLOR, state


def test_set_color_changes_the_normal_color_and_not_the_yellow_one(game):
    button = game.panel_manager["thanks"]["thanks_link"]
    text = game.panel_manager["thanks"]["thanks_link_text"]
    button.focused = True
    text.update()
    text.set_color((10, 200, 10))
    assert text.color == YELLOW_TEXT_COLOR  # still on the yellow face
    button.focused = False
    text.update()
    assert text.color == (10, 200, 10)
