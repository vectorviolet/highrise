"""The cash display (ui/cash_display.py, config/panels.yaml): it lines up with the HUD
buttons at every UI scale, in every candidate style, and big amounts fit."""

import pytest

import pygamine
from app.game import Game
from ui.cash_display import CASH_STYLES, DEFAULT_CASH_STYLE, cash_style
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


def test_the_default_style_is_the_configured_one(game):
    assert game.cash_style is cash_style(DEFAULT_CASH_STYLE)


def test_an_unknown_style_is_a_configuration_error():
    with pytest.raises(ValueError, match="ui.cash_display"):
        cash_style(99)


@pytest.mark.parametrize("style", sorted(CASH_STYLES))
@pytest.mark.parametrize("ui_scale", UI_SCALES)
def test_the_cash_display_lines_up_with_the_buttons(game, style, ui_scale):
    game.cash_style = cash_style(style)
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
        ), (name, style, ui_scale)


@pytest.mark.parametrize("style", sorted(CASH_STYLES))
@pytest.mark.parametrize("ui_scale", UI_SCALES)
def test_a_large_amount_fits_inside_the_plate_and_clear_of_the_coin(
    game, style, ui_scale
):
    game.cash_style = cash_style(style)
    game.ui_scale = ui_scale
    game.rebuild_panels()
    game.player.money = 999_999_999
    panel = hud(game)

    text, plate, icon = (
        panel[n].rect for n in ("money_text", "money_panel", "money_icon")
    )

    assert plate.contains(text)
    assert text.centery == pytest.approx(plate.centery, abs=4)
    if game.cash_style.coin:
        assert text.left > icon.right
        assert plate.contains(icon)
    # The plate stays on the canvas, next to the last button.
    assert plate.right <= game.size[0]
    assert plate.left > panel["next_age_button"].rect.right


@pytest.mark.parametrize("style", sorted(CASH_STYLES))
def test_the_style_colors_the_text_and_shows_the_coin_only_when_it_has_one(game, style):
    game.cash_style = cash_style(style)
    game.rebuild_panels()
    panel = hud(game)

    assert panel["money_text"].color == (*game.cash_style.text_color,)
    assert panel["money_icon"].active is game.cash_style.coin
