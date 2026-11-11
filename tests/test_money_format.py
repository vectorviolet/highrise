"""Money is written with the language's thousands separator and the $ after the digits."""

import pytest
from pygame.math import Vector2

from pygamine.util.localization import localization
from ui.floating_text import FloatingText
from ui.money_format import format_money


@pytest.mark.parametrize(
    ("language", "amount", "expected"),
    [
        ("en", 0, "0$"),
        ("en", 7, "7$"),
        ("en", 999, "999$"),
        ("en", 1000, "1,000$"),
        ("en", 12345, "12,345$"),
        ("en", 1234567890, "1,234,567,890$"),
        ("en", -5, "-5$"),
        ("en", -12345, "-12,345$"),
        ("tr", 0, "0$"),
        ("tr", 999, "999$"),
        ("tr", 1000, "1.000$"),
        ("tr", 12345, "12.345$"),
        ("tr", 1234567890, "1.234.567.890$"),
        ("tr", -12345, "-12.345$"),
    ],
)
def test_format_money(language, amount, expected):
    localization.set_language(language)

    assert format_money(amount) == expected


def test_the_floating_text_uses_the_same_format():
    localization.set_language("tr")

    assert FloatingText(Vector2(), 12345, 0, -1, "midbottom").text == "+12.345$"
    assert FloatingText(Vector2(), -1200, 0, 1, "bottomright").text == "-1.200$"


def test_a_multiplier_uses_the_languages_decimal_mark():
    from ui.money_format import format_multiplier

    assert format_multiplier(1.35) == "1.35"
    assert format_multiplier(2.0) == "2"
    localization.set_language("tr")
    assert format_multiplier(1.35) == "1,35"
