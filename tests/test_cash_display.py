"""The cash display (ui/cash_display.py, config/panels.yaml): it lines up with the HUD
buttons at every UI scale, and big amounts fit."""

import pytest

import pygamine
from app.game import Game
from ui.cash_display import TEXT_COLOR
from ui.ui_scale import UI_SCALES


@pytest.fixture
def game(monkeypatch) -> Game:
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)
    game = Game()
    game.run()
    return game


def hud(game: Game) -> dict:
    return game.panel_manager["game"]


@pytest.mark.parametrize("ui_scale", UI_SCALES)
def test_the_cash_display_lines_up_with_the_buttons(game, ui_scale):
    game.ui_scale = ui_scale
    game.rebuild_panels()
    panel = hud(game)

    plate = panel["money_panel"].rect
    for name in ("expand_button", "build_button", "next_age_button"):
        button = panel[name].rect
        assert (plate.top, plate.bottom, plate.height) == (
            button.top,
            button.bottom,
            button.height,
        ), (name, ui_scale)


@pytest.mark.parametrize("ui_scale", UI_SCALES)
def test_a_large_amount_fits_inside_the_plate_and_clear_of_the_coin(game, ui_scale):
    game.ui_scale = ui_scale
    game.rebuild_panels()
    game.player.money = 999_999_999
    panel = hud(game)

    text, plate, icon = (
        panel[n].rect for n in ("money_text", "money_panel", "money_icon")
    )

    assert plate.contains(text)
    assert text.centery == pytest.approx(plate.centery, abs=4)
    assert text.left > icon.right
    assert plate.contains(icon)
    # The plate stays on the canvas, next to the last button.
    assert plate.right <= game.size[0]
    assert plate.left > panel["next_age_button"].rect.right


def test_the_text_is_light(game):
    assert hud(game)["money_text"].color == (*TEXT_COLOR,)


@pytest.mark.parametrize("ui_scale", UI_SCALES)
def test_a_spend_text_lines_up_with_the_amount_and_stays_on_screen(game, ui_scale):
    game.ui_scale = ui_scale
    game.rebuild_panels()
    game.player.money = 100_000
    game._spend(500)
    (text,) = game.floating_texts.texts
    panel = hud(game)

    assert text.position == (
        panel["money_text"].rect.right,
        panel["money_panel"].rect.bottom,
    )
    assert text.anchor == "topright"
    assert game.window.get_rect().collidepoint(text.position)
