"""Issue #6: add_objects() runs at startup and again on every New game, but
the Player is created once. Each run must replace the money listener, not
add another one, and the listener must update the current money text."""

from __future__ import annotations

import pytest

import pygamine
from app.game import Game


@pytest.fixture
def game(monkeypatch) -> Game:
    # The real window loop and splash don't apply headlessly; everything
    # else in run() does.
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)
    game = Game()
    game.run()
    return game


def money_text(game: Game):
    return game.panel_manager["game"]["money_text"]


def test_startup_registers_one_listener_and_shows_the_money(game):
    assert len(game.player._money_listeners) == 1
    assert money_text(game).text == f"{game.player.money}$"

    game.player.earn(7)

    assert money_text(game).text == f"{game.player.money}$"


def test_several_new_games_keep_exactly_one_listener(game):
    for _ in range(3):
        game.new_game()

    assert len(game.player._money_listeners) == 1


def test_money_change_after_new_games_updates_the_current_text(game):
    for _ in range(3):
        game.new_game()
    current = money_text(game)

    game.player.earn(42)

    assert current.text == f"{game.player.money}$"
