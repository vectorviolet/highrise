"""The info panel sits at the window's right edge, vertically centered, so the board stays
visible; it stays on screen and clear of the bottom bar at every UI scale (real Game and the
real config/panels.yaml)."""

import pygame
import pytest

import pygamine
from app.game import Game
from ui.ui_scale import UI_SCALES

CONTENT = (
    "info_panel_building_image",
    "sell_button",
    "close_button",
    "level_text",
    "speed_text",
    "boost_text",
    "cooldown_text",
    "sell_price_text",
)


@pytest.fixture
def game(monkeypatch) -> Game:
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)
    game = Game()
    game.run()
    return game


def rect(obj) -> pygame.Rect:
    return pygame.Rect(obj.rect.x, obj.rect.y, obj.rect.width, obj.rect.height)


@pytest.mark.parametrize("ui_scale", UI_SCALES)
def test_the_info_panel_is_at_the_right_edge_on_screen_and_clear_of_the_hud(
    game, ui_scale
):
    game.ui_scale = ui_scale
    game.rebuild_panels()
    panel = game.panel_manager["game"]
    window = pygame.Rect(0, 0, *game.size)
    info = rect(panel["info_panel"])

    assert window.contains(info)
    assert info.right > window.right * 0.9  # at the right edge
    assert info.left > window.centerx  # the board's center is free
    assert abs(info.centery - window.centery) <= 1  # vertically centered
    for name in ("game_panel", "money_panel", "next_age_button"):
        assert not info.colliderect(rect(panel[name])), name


@pytest.mark.parametrize("ui_scale", UI_SCALES)
def test_the_info_panel_content_stays_inside_it(game, ui_scale):
    game.ui_scale = ui_scale
    game.rebuild_panels()
    panel = game.panel_manager["game"]
    info = rect(panel["info_panel"])

    for name in CONTENT:
        assert info.contains(rect(panel[name])), name
