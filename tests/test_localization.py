"""The game's language files (config/lang/*.yaml): every language has every
key with the same {placeholders}, and every font the game draws text with has
every character of every language. CI runs these with the rest of the suite."""

from pathlib import Path

import pytest
import yaml

from pygamine.util.localization import Localization, missing_glyphs

ROOT = Path(__file__).resolve().parent.parent
LANG = ROOT / "config" / "lang"
FONTS = ROOT / "assets" / "fonts"


def loaded() -> Localization:
    localization = Localization()
    localization.load(LANG)
    return localization


def test_english_and_turkish_are_both_available():
    assert loaded().languages() == {"en": "English", "tr": "Türkçe"}


def test_every_language_has_exactly_the_keys_and_placeholders_of_english():
    assert loaded().check_key_coverage() == {}


def test_the_coverage_check_fails_on_a_missing_key(tmp_path):
    for file in LANG.glob("*.yaml"):
        (tmp_path / file.name).write_text(file.read_text(encoding="utf-8"), "utf-8")
    turkish = yaml.safe_load((tmp_path / "tr.yaml").read_text(encoding="utf-8"))
    del turkish["menu"]["play"]
    (tmp_path / "tr.yaml").write_text(
        yaml.safe_dump(turkish, allow_unicode=True), encoding="utf-8"
    )
    localization = Localization()
    localization.load(tmp_path)

    report = localization.check_key_coverage()

    assert report["tr"]["missing"] == ["menu.play"]


def test_the_coverage_check_fails_on_a_changed_placeholder(tmp_path):
    for file in LANG.glob("*.yaml"):
        (tmp_path / file.name).write_text(file.read_text(encoding="utf-8"), "utf-8")
    turkish = yaml.safe_load((tmp_path / "tr.yaml").read_text(encoding="utf-8"))
    turkish["game"]["level"] = "Seviye: {deger}"
    (tmp_path / "tr.yaml").write_text(
        yaml.safe_dump(turkish, allow_unicode=True), encoding="utf-8"
    )
    localization = Localization()
    localization.load(tmp_path)

    report = localization.check_key_coverage()

    assert list(report["tr"]["placeholders"]) == ["game.level"]


@pytest.mark.parametrize("font", sorted(FONTS.glob("*.ttf")), ids=lambda p: p.name)
def test_every_font_has_every_character_of_every_language(font):
    assert loaded().check_glyph_coverage(font) == {}


def test_the_glyph_check_catches_a_character_the_font_lacks():
    # Titillium Web has no arrow: a string using one would draw a blank box.
    font = FONTS / "TitilliumWeb-Regular.ttf"

    assert missing_glyphs(font, "Ğ ı İ ş Ş → ok") == ["→"]
