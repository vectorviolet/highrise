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
    odometer.bind(
        widget.rect, widget.font, widget.color, pygame.Rect(0, 0, 400, 100), 0
    )
    return odometer


def rolling_chars(odometer: Odometer) -> list[tuple[str, str]]:
    """(from, to) of every slot that rolls, rightmost first."""
    return [(s.from_char, s.to_char) for s in odometer._slots if s.rolls]


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
    assert [s.rolls for s in odometer._slots if s.to_char == ","] == [False]


def test_a_leaving_digit_rolls_out_at_the_left_and_is_then_gone(odometer):
    odometer.snap("1,000$")

    odometer.set_target("999$", -1, now_ms=0)

    assert odometer.text == "999$"
    assert ("1", "") in rolling_chars(odometer)
    surface = pygame.Surface((400, 100), pygame.SRCALPHA)
    odometer.draw(surface, DURATION)
    assert all(s.to_char for s in odometer._slots)  # the leaving digit was dropped


def test_digits_are_clipped_to_the_plate(odometer, widget):
    odometer.bind(
        widget.rect,
        widget.font,
        widget.color,
        pygame.Rect(0, widget.rect.top + 10, 400, 12),
        0,
    )
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


def test_the_odometer_owns_the_text_and_the_widget_is_only_layout(game):
    game.player.money = 1000
    money_text = game.panel_manager["game"]["money_text"]
    layout = money_text.text

    game.player.earn(234)

    assert game.odometer.text == "1,234$"
    assert not money_text.active
    # The hidden widget isn't re-rendered on every change.
    assert money_text.text == layout


def test_a_new_session_and_a_language_change_snap_without_rolling(game):
    game.player.money = 1234567
    game.new_game()
    assert not game.odometer.is_rolling(pygame.time.get_ticks())
    assert game.odometer.text == f"{game.player.money:,}$"

    game.player.earn(1_000_000)
    localization.set_language("tr")
    game._on_language_changed("tr")

    assert game.odometer.text == f"{game.player.money:,}$".replace(",", ".")
    assert not game.odometer.is_rolling(pygame.time.get_ticks())


def test_the_roll_time_is_the_configured_one(game):
    assert game.odometer.duration_ms == game.settings["ui"]["cash_roll_ms"]


def drawn_cells(
    odometer: Odometer, monkeypatch, now_ms: int
) -> list[tuple[str, pygame.Rect]]:
    """(character, cell) of every glyph drawn at `now_ms`, empty ones left out."""
    drawn = []

    def record(surface, char, cell, dy):
        if char:
            drawn.append((char, cell.copy()))

    monkeypatch.setattr(odometer, "_blit", record)
    odometer.draw(pygame.Surface((400, 100)), now_ms)
    return drawn


def test_a_leaving_separator_stays_until_its_digits_have_rolled_out(
    odometer, monkeypatch
):
    odometer.snap("1,000$")

    odometer.set_target("999$", -1, now_ms=0)

    mid = [c for c, _ in drawn_cells(odometer, monkeypatch, DURATION // 2)]
    # The leaving "1" still sits behind its comma, never glued to the digits ("1999$").
    assert mid.index(",") < mid.index("1")
    assert [c for c, _ in drawn_cells(odometer, monkeypatch, DURATION)] == list("$999")


def test_a_digit_that_was_leaving_rolls_back_in_on_a_reversal(odometer, monkeypatch):
    odometer.snap("1,000$")
    odometer.set_target("999$", -1, now_ms=0)

    odometer.set_target("1,000$", 1, now_ms=DURATION // 2)

    assert odometer.text == "1,000$"
    assert ("", "1") in rolling_chars(odometer)
    mid = [
        c for c, _ in drawn_cells(odometer, monkeypatch, DURATION // 2 + DURATION // 4)
    ]
    assert "1" in mid and "," in mid
    assert [c for c, _ in drawn_cells(odometer, monkeypatch, 10 * DURATION)] == list(
        "$000,1"
    )


def test_a_different_character_after_a_leaving_one_starts_from_its_glyph(odometer):
    odometer.snap("10$")
    odometer.set_target("9$", -1, now_ms=0)  # the "1" is leaving

    odometer.set_target("19$", 1, now_ms=10)  # a "1" comes back, the 9 stays

    assert odometer.text == "19$"
    assert ("", "1") in rolling_chars(odometer)


def leftmost_x(odometer: Odometer, monkeypatch, now_ms: int) -> int:
    return drawn_cells(odometer, monkeypatch, now_ms)[-1][1].x


def test_the_neighbors_of_a_rolling_digit_do_not_jump(odometer, monkeypatch):
    # Titillium's digits are all the same width, so give "1" a narrower glyph, as a
    # proportional font would.
    widths = {"0": 20, "1": 12, "$": 20, "": 0}
    monkeypatch.setattr(odometer, "_natural_width", lambda char: widths[char])
    odometer.snap("10$")
    before = leftmost_x(odometer, monkeypatch, 0)
    odometer.snap("11$")
    after = leftmost_x(odometer, monkeypatch, 0)
    assert before != after  # the widths differ, so this test means something
    odometer.snap("10$")
    odometer.set_target("11$", 1, now_ms=0)

    # The leading "1" doesn't move when the roll starts, nor at its end, and moves smoothly.
    assert leftmost_x(odometer, monkeypatch, 0) == before
    middle = leftmost_x(odometer, monkeypatch, DURATION // 2)
    assert min(before, after) <= middle <= max(before, after)
    assert leftmost_x(odometer, monkeypatch, DURATION) == after


def test_a_text_too_wide_for_the_room_is_scaled_to_fit(odometer, widget):
    odometer.bind(
        widget.rect, widget.font, widget.color, pygame.Rect(0, 0, 400, 100), 200
    )
    odometer.snap("100,000,000$")
    surface = pygame.Surface((400, 100), pygame.SRCALPHA)

    odometer.draw(surface, 0)

    ink = pygame.mask.from_surface(surface).get_bounding_rects()
    assert min(r.left for r in ink) >= 200
    assert max(r.right for r in ink) <= widget.rect.right


def test_a_short_text_is_not_scaled(odometer):
    odometer.snap("5$")

    odometer.draw(pygame.Surface((400, 100)), 0)

    assert odometer._fit == 1.0


@pytest.mark.parametrize("ui_scale", [80, 100, 125])
def test_big_amounts_never_cover_the_coin(game, ui_scale):
    game.ui_scale = ui_scale
    game.rebuild_panels()
    game.player.money = 100_000_000
    hud = game.panel_manager["game"]
    surface = pygame.Surface(game.window.get_size(), pygame.SRCALPHA)

    game.odometer.draw(surface, 0)

    ink = pygame.mask.from_surface(surface).get_bounding_rects()
    assert ink
    assert min(r.left for r in ink) >= hud["money_icon"].rect.right
    assert max(r.right for r in ink) <= hud["money_panel"].rect.right
