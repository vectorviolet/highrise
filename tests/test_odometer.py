"""The cash odometer (ui/odometer.py): which digits roll, in which direction, retargeting while
rolling, digits that appear or leave, and clipping. The clock is passed in, so no test waits."""

from types import SimpleNamespace

import pygame
import pytest

from app.game import Game
from ui.odometer import Odometer
from pygamine.util.localization import localization

DURATION = 200


@pytest.fixture
def widget(assets):
    font = pygame.font.Font(str(assets.font_path("titillium_bold")), 32)
    height = font.get_height()
    return SimpleNamespace(
        font=font, color=(255, 255, 255), rect=pygame.Rect(0, 20, 300, height)
    )


@pytest.fixture
def odometer(widget) -> Odometer:
    odometer = Odometer(DURATION)
    odometer.bind(widget, pygame.Rect(0, 0, 400, 100))
    return odometer


def rolling_chars(odometer: Odometer) -> list[tuple[str, str]]:
    """(from, to) of every slot that rolls, rightmost first."""
    return [(s.from_char, s.to_char) for s in odometer._slots if s.direction]


def test_only_the_digits_that_change_roll(odometer):
    odometer.snap("12,345$")

    odometer.set_target("12,346$", 1, now_ms=0)

    assert rolling_chars(odometer) == [("5", "6")]
    assert odometer.text == "12,346$"


def test_a_carry_rolls_every_digit_it_changes_but_not_the_separator_or_sign(odometer):
    odometer.snap("12,999$")

    odometer.set_target("13,000$", 1, now_ms=0)

    assert rolling_chars(odometer) == [("9", "0"), ("9", "0"), ("9", "0"), ("2", "3")]


def test_the_same_text_rolls_nothing(odometer):
    odometer.snap("500$")

    odometer.set_target("500$", -1, now_ms=0)

    assert rolling_chars(odometer) == []
    assert not odometer.is_rolling(0)


def test_everything_stops_after_the_duration(odometer):
    odometer.snap("100$")
    odometer.set_target("101$", 1, now_ms=1000)

    assert odometer.is_rolling(1000 + DURATION - 1)
    assert not odometer.is_rolling(1000 + DURATION)


def blits(odometer: Odometer, monkeypatch, now_ms: int) -> list[tuple[str, int]]:
    """(character, vertical offset from its cell) of everything drawn at `now_ms`."""
    drawn = []
    monkeypatch.setattr(
        odometer,
        "_blit",
        lambda surface, char, cell, dy: drawn.append((char, dy)),
    )
    odometer.draw(pygame.Surface((400, 100)), now_ms)
    return drawn


def test_money_up_the_old_digit_leaves_at_the_top_and_the_new_one_comes_from_below(
    odometer, monkeypatch
):
    odometer.snap("0$")
    odometer.set_target("1$", 1, now_ms=0)

    drawn = dict(blits(odometer, monkeypatch, DURATION // 2))

    assert drawn["0"] < 0 < drawn["1"]


def test_money_down_the_new_digit_comes_from_the_top(odometer, monkeypatch):
    odometer.snap("1$")
    odometer.set_target("0$", -1, now_ms=0)

    drawn = dict(blits(odometer, monkeypatch, DURATION // 2))

    assert drawn["1"] > 0 > drawn["0"]


def test_a_roll_starts_a_cell_away_and_ends_in_place(odometer, monkeypatch, widget):
    odometer.snap("0$")
    odometer.set_target("1$", 1, now_ms=0)

    assert dict(blits(odometer, monkeypatch, 0)) == {
        "0": 0,
        "1": widget.rect.height,
        "$": 0,
    }
    assert blits(odometer, monkeypatch, DURATION) == [("$", 0), ("1", 0)]


def test_a_change_during_a_roll_retargets_to_the_newest_text(odometer):
    odometer.snap("100$")
    odometer.set_target("101$", 1, now_ms=0)
    odometer.set_target("102$", 1, now_ms=DURATION // 2)

    assert odometer.text == "102$"
    assert rolling_chars(odometer) == [("1", "2")]
    # The retarget restarts the roll of the digit that changed again.
    assert odometer.is_rolling(DURATION // 2 + DURATION - 1)
    assert not odometer.is_rolling(DURATION // 2 + DURATION)


def test_a_digit_already_rolling_toward_the_right_character_keeps_its_clock(odometer):
    odometer.snap("109$")
    odometer.set_target("110$", 1, now_ms=0)  # the 9 -> 0 and 0 -> 1 roll
    started = {s.to_char: s.started_ms for s in odometer._slots if s.direction}

    odometer.set_target("110$", -1, now_ms=100)  # same target again: nothing restarts

    assert {s.to_char: s.started_ms for s in odometer._slots if s.direction} == started


def test_changes_are_never_queued(odometer):
    odometer.snap("0$")
    for i, now in enumerate(range(0, 100, 10), start=1):
        odometer.set_target(f"{i % 10}$", 1, now_ms=now)

    # One roll in flight for that digit, ending DURATION after the last change.
    assert odometer.text == "0$"
    assert odometer.is_rolling(90 + DURATION - 1)
    assert not odometer.is_rolling(90 + DURATION)


def test_a_new_leading_digit_rolls_in_at_the_left(odometer):
    odometer.snap("999$")

    odometer.set_target("1,000$", 1, now_ms=0)

    assert odometer.text == "1,000$"
    assert rolling_chars(odometer) == [("9", "0"), ("9", "0"), ("9", "0"), ("", "1")]
    # The separator that appeared doesn't roll.
    assert [s.direction for s in odometer._slots if s.to_char == ","] == [0]


def test_a_leaving_digit_rolls_out_at_the_left_and_is_then_gone(odometer):
    odometer.snap("1,000$")

    odometer.set_target("999$", -1, now_ms=0)

    assert odometer.text == "999$"
    assert ("1", "") in rolling_chars(odometer)
    surface = pygame.Surface((400, 100), pygame.SRCALPHA)
    odometer.draw(surface, DURATION)
    assert all(s.to_char for s in odometer._slots)  # the leaving digit was dropped


def test_digits_are_clipped_to_the_plate(odometer, widget):
    odometer.bind(widget, pygame.Rect(0, widget.rect.top + 10, 400, 12))
    odometer.snap("0$")
    odometer.set_target("1$", 1, now_ms=0)
    surface = pygame.Surface((400, 100), pygame.SRCALPHA)

    odometer.draw(surface, DURATION // 3)

    rows = [y for y in range(100) if any(surface.get_at((x, y)).a for x in range(400))]
    assert rows
    assert min(rows) >= widget.rect.top + 10
    assert max(rows) < widget.rect.top + 10 + 12


def test_drawing_leaves_the_surfaces_clip_as_it_was(odometer):
    odometer.snap("5$")
    surface = pygame.Surface((400, 100))
    surface.set_clip(pygame.Rect(3, 4, 50, 60))

    odometer.draw(surface, 0)

    assert surface.get_clip() == pygame.Rect(3, 4, 50, 60)


def test_a_resting_odometer_looks_like_the_text(odometer, widget):
    odometer.snap("12,345$")
    surface = pygame.Surface((400, 100), pygame.SRCALPHA)

    odometer.draw(surface, 0)

    ink = pygame.mask.from_surface(surface).get_bounding_rects()
    assert ink
    assert max(r.right for r in ink) <= widget.rect.right


# ── in the game ──────────────────────────────────────────────────────────────


@pytest.fixture
def game(monkeypatch) -> Game:
    import pygamine

    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)
    game = Game()
    game.run()
    return game


def test_a_money_change_rolls_in_the_direction_of_the_change(game):
    game.player.money = 5000
    game.odometer.snap("5,000$")
    game.player.earn(1)
    assert game.odometer.text == "5,001$"
    assert rolling_chars(game.odometer) == [("0", "1")]

    game.player.spend(2)
    assert game.odometer.text == "4,999$"
    assert [s.direction for s in game.odometer._slots if s.direction] == [-1] * 4


def test_the_real_text_is_set_at_once_and_the_widget_is_hidden(game):
    game.player.money = 1000

    game.player.earn(234)

    money_text = game.panel_manager["game"]["money_text"]
    assert money_text.text == "1,234$"
    assert not money_text.active


def test_a_new_session_and_a_language_change_snap_without_rolling(game):
    game.player.money = 1234567
    game.new_game()
    assert not game.odometer.is_rolling(pygame.time.get_ticks())
    assert game.odometer.text == f"{game.player.money:,}$"

    game.player.earn(1_000_000)
    localization.set_language("tr")
    game._refresh_ui_texts()

    assert game.odometer.text == f"{game.player.money:,}$".replace(",", ".")
    assert not game.odometer.is_rolling(pygame.time.get_ticks())


def test_the_roll_time_is_the_configured_one(game):
    assert game.odometer.duration_ms == game.settings["ui"]["cash_roll_ms"]
