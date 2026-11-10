"""Floating money text (ui/floating_text.py): signs, colors, amounts, the per-source merge
window, expiry, scaling and drawing. The clock is passed in, so no test waits."""

import pygame
import pytest
from pygame.math import Vector2

from ui.floating_text import FloatingTextConfig, FloatingTexts

CONFIG = FloatingTextConfig(
    gain_font_size=24,
    spend_font_size=30,
    gain_color=(10, 250, 10),
    spend_color=(250, 10, 10),
    outline_color=(0, 0, 0),
    lifetime_ms=1000,
    rise=80,
    fall=60,
    merge_window_ms=500,
    max_texts=3,
)


@pytest.fixture
def texts(assets) -> FloatingTexts:
    return FloatingTexts(CONFIG, str(assets.font_path("titillium_black")))


def test_a_gain_reads_plus_dollar_amount_and_rises(texts):
    texts.gain("a", (100, 200), 35, now_ms=0)

    (text,) = texts.texts
    assert text.text == "+35$"
    assert text.amount == 35
    assert texts.current_position(text, 0) == Vector2(100, 200)
    assert texts.current_position(text, 1000).y == 200 - CONFIG.rise
    assert texts.current_position(text, 400).y < 200  # already moving up


def test_a_spend_reads_minus_dollar_amount_and_falls(texts):
    texts.spend((300, 80), 120, now_ms=0)

    (text,) = texts.texts
    assert text.text == "-120$"
    assert text.amount == -120
    assert texts.current_position(text, 1000) == Vector2(300, 80 + CONFIG.fall)


def test_payouts_of_one_source_inside_the_merge_window_become_one_number(texts):
    texts.gain("a", (0, 0), 10, now_ms=0)
    texts.gain("a", (0, 0), 5, now_ms=499)

    assert [t.text for t in texts.texts] == ["+15$"]
    assert texts.texts[0].born_ms == 0  # merging doesn't restart its life


def test_a_payout_after_the_merge_window_starts_a_new_number(texts):
    texts.gain("a", (0, 0), 10, now_ms=0)
    texts.gain("a", (0, 0), 5, now_ms=500)

    assert [t.text for t in texts.texts] == ["+10$", "+5$"]


def test_payouts_of_different_sources_never_merge(texts):
    texts.gain("a", (0, 0), 10, now_ms=0)
    texts.gain("b", (50, 0), 10, now_ms=1)

    assert [t.text for t in texts.texts] == ["+10$", "+10$"]


def test_a_spend_never_merges_with_a_gain_or_another_spend(texts):
    texts.gain("a", (0, 0), 10, now_ms=0)
    texts.spend((0, 0), 10, now_ms=1)
    texts.spend((0, 0), 10, now_ms=2)

    assert [t.text for t in texts.texts] == ["+10$", "-10$", "-10$"]


def test_texts_vanish_after_their_lifetime(texts):
    texts.gain("a", (0, 0), 10, now_ms=0)
    texts.spend((0, 0), 5, now_ms=600)

    texts.update(now_ms=999)
    assert len(texts.texts) == 2
    texts.update(now_ms=1000)
    assert [t.text for t in texts.texts] == ["-5$"]
    texts.update(now_ms=1600)
    assert texts.texts == []


def test_at_most_max_texts_stay_alive_and_the_oldest_go_first(texts):
    for i in range(5):
        texts.spend((0, 0), i + 1, now_ms=i)

    assert [t.text for t in texts.texts] == ["-3$", "-4$", "-5$"]


def test_the_distance_scales_with_the_ui_scale(texts):
    texts.scale = 1.25
    texts.gain("a", (0, 100), 10, now_ms=0)

    assert texts.current_position(texts.texts[0], 1000).y == 100 - CONFIG.rise * 1.25


def test_the_font_scales_with_the_ui_scale(texts):
    texts.gain("a", (0, 0), 10, now_ms=0)
    small = texts._render(texts.texts[0]).get_height()
    texts.scale = 1.25

    assert texts._render(texts.texts[0]).get_height() > small


@pytest.mark.parametrize(
    ("amount", "color"), [(10, CONFIG.gain_color), (-10, CONFIG.spend_color)]
)
def test_gains_are_drawn_green_and_spends_red(texts, amount, color):
    if amount > 0:
        texts.gain("a", (100, 100), amount, now_ms=0)
    else:
        texts.spend((100, 100), -amount, now_ms=0)
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)

    texts.draw(surface, now_ms=0)

    drawn = {
        tuple(surface.get_at((x, y)))[:3]
        for x in range(200)
        for y in range(200)
        if surface.get_at((x, y)).a == 255
    }
    assert color in drawn
    other = CONFIG.spend_color if amount > 0 else CONFIG.gain_color
    assert other not in drawn


def test_a_text_fades_out_over_its_life(texts):
    texts.gain("a", (100, 100), 10, now_ms=0)

    def covered(now_ms: int) -> int:
        surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        texts.draw(surface, now_ms)
        return max(surface.get_at((x, y)).a for x in range(200) for y in range(200))

    assert covered(0) == 255
    assert 0 < covered(700) < 255
    assert covered(999) < covered(700)


def test_a_gain_without_a_key_never_merges(texts):
    texts.gain("a", (0, 0), 10, now_ms=0)
    texts.gain(None, (0, 0), 500, now_ms=1)
    texts.gain(None, (0, 0), 7, now_ms=2)

    assert [t.text for t in texts.texts] == ["+10$", "+500$", "+7$"]


@pytest.mark.parametrize(
    ("change", "message"),
    [({"max_texts": 0}, "max_texts"), ({"lifetime_ms": 0}, "lifetime_ms")],
)
def test_the_config_rejects_values_that_break_the_texts(change, message):
    values = {
        "gain_font_size": 24,
        "spend_font_size": 30,
        "gain_color": [0, 255, 0],
        "spend_color": [255, 0, 0],
        "outline_color": [0, 0, 0],
        "lifetime_ms": 1000,
        "rise": 10,
        "fall": 10,
        "merge_window_ms": 500,
        "max_texts": 3,
    } | change

    with pytest.raises(ValueError, match=message):
        FloatingTextConfig.from_dict(values)


def test_gains_over_the_world_are_skipped_while_a_panel_is_open_but_spends_stay(texts):
    texts.gain("a", (50, 50), 10, now_ms=0)
    texts.spend((190, 50), 10, now_ms=0)

    def drawn(**kwargs) -> tuple[bool, bool]:
        surface = pygame.Surface((200, 100), pygame.SRCALPHA)
        texts.draw(surface, now_ms=0, **kwargs)
        left = surface.subsurface((0, 0, 100, 100))
        right = surface.subsurface((100, 0, 100, 100))
        return (
            pygame.mask.from_surface(left).count() > 0,
            pygame.mask.from_surface(right).count() > 0,
        )

    assert drawn() == (True, True)
    assert drawn(over_world=False) == (False, True)


def test_a_fade_step_is_drawn_from_one_cached_image(texts):
    texts.gain("a", (50, 50), 10, now_ms=0)
    surface = pygame.Surface((200, 100), pygame.SRCALPHA)

    texts.draw(surface, now_ms=300)
    image = texts._render(texts.texts[0], 14)
    texts.draw(surface, now_ms=301)

    assert texts._render(texts.texts[0], 14) is image


def test_a_spend_is_right_aligned_with_its_position_and_gains_are_centered(texts):
    texts.spend((190, 60), 10, now_ms=0)
    texts.gain("a", (50, 60), 10, now_ms=0)
    surface = pygame.Surface((200, 100), pygame.SRCALPHA)

    texts.draw(surface, now_ms=0)

    bounds = pygame.mask.from_surface(
        surface.subsurface((100, 0, 100, 100))
    ).get_bounding_rects()[0]
    assert (
        bounds.right + 100 <= 190 + 1
    )  # ends at the spend's x (the outline adds a pixel)
    assert bounds.right + 100 >= 190 - 4
    gain = pygame.mask.from_surface(
        surface.subsurface((0, 0, 100, 100))
    ).get_bounding_rects()[0]
    assert abs(gain.centerx - 50) <= 2


def test_a_text_that_would_leave_the_screen_is_pulled_back_in(texts):
    texts.spend((195, 5), 1_000_000, now_ms=0)
    texts.gain("a", (-30, 2), 10, now_ms=0)
    surface = pygame.Surface((200, 100), pygame.SRCALPHA)

    texts.draw(surface, now_ms=0)

    mask = pygame.mask.from_surface(surface)
    assert mask.count() > 0
    # Drawn on a surface of exactly the screen's size, so every pixel is inside; the clamp
    # keeps the whole text, not just a part of it.
    assert pygame.Rect(mask.get_bounding_rects()[0]).left >= 0


def test_gains_are_smaller_than_spends(texts):
    texts.gain("a", (0, 0), 10, now_ms=0)
    texts.spend((0, 0), 10, now_ms=0)
    gain, spend = texts.texts

    assert texts._size(gain) == 24
    assert texts._size(spend) == 30
    texts.scale = 1.25
    assert texts._size(gain) == 30
