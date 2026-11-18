"""The Windows installer script (packaging/highrise.iss) stays in step with the game."""

import re
from pathlib import Path

from util.paths import LANG_FOLDER

ROOT = Path(__file__).resolve().parent.parent
ISS = (ROOT / "packaging" / "highrise.iss").read_text(encoding="utf-8")


def _installer_languages() -> set[str]:
    section = re.search(r"^\[Languages\]\n(.*?)(?=^\[|\Z)", ISS, re.M | re.S)
    assert section, "packaging/highrise.iss has no [Languages] section"
    return set(re.findall(r'^Name:\s*"([^"]+)"', section.group(1), re.M))


def test_installer_languages_match_the_games_languages():
    """Each language entry is named by its config/lang/<code>.yaml code, so adding a game
    language fails here until the installer gets it (and the reverse)."""
    game = {p.stem for p in Path(LANG_FOLDER).glob("*.yaml")}
    assert _installer_languages() == game


def test_installer_has_a_language_dialog_and_a_folder_page():
    assert re.search(r"^ShowLanguageDialog=yes$", ISS, re.M)
    assert re.search(r"^DisableDirPage=no$", ISS, re.M)


def test_installer_packs_the_pyinstaller_onedir_output():
    assert r'Source: "..\dist\highrise\*"' in ISS
    assert "recursesubdirs" in ISS


def test_installer_only_wipes_internal_in_its_own_install():
    """A folder the player picked that holds another program's _internal is never wiped."""
    assert re.search(
        r'^Type: filesandordirs; Name: "\{app\}\_internal"; Check: IsOurInstall$',
        ISS,
        re.M,
    )
    assert "function IsOurInstall: Boolean;" in ISS
