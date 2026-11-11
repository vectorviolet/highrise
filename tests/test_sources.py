"""assets/SOURCES.yaml -- where every asset comes from -- is complete and
consistent: every file under assets/ is listed, every listed file exists,
every pack has its license text in licenses/assets/, and CREDITS.md's asset
section is exactly what scripts/gen_credits.py builds from it."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
LICENSES = ROOT / "licenses" / "assets"

_spec = importlib.util.spec_from_file_location(
    "gen_credits", ROOT / "scripts" / "gen_credits.py"
)
gen_credits = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen_credits)


@pytest.fixture(scope="module")
def sources() -> dict:
    return gen_credits.load_sources()


def _asset_files() -> set[str]:
    return {
        p.relative_to(ASSETS).as_posix()
        for p in ASSETS.rglob("*")
        if p.is_file() and p.name != "SOURCES.yaml"
    }


def test_every_asset_file_is_listed(sources):
    assert sorted(_asset_files() - set(sources["files"])) == []


def test_every_listed_file_exists(sources):
    assert sorted(set(sources["files"]) - _asset_files()) == []


def test_every_source_is_a_known_pack_or_own(sources):
    unknown = {
        e["source"] for e in sources["files"].values() if e["source"] != "own"
    } - set(sources["packs"])
    assert unknown == set()


def test_every_pack_file_names_its_original(sources):
    for rel, e in sources["files"].items():
        if e["source"] != "own":
            assert "original" in e or "composited_from" in e, rel


def test_every_pack_has_its_license_text(sources):
    for slug in sources["packs"]:
        text = LICENSES / f"{slug}.txt"
        assert text.is_file() and text.stat().st_size > 0, slug


def test_no_license_text_for_a_pack_that_is_not_used(sources):
    assert {p.stem for p in LICENSES.glob("*.txt")} == set(sources["packs"])


def test_credits_md_asset_section_is_generated_from_sources(sources):
    text = gen_credits.CREDITS.read_text(encoding="utf-8")
    assert gen_credits.updated_credits(text, gen_credits.render(sources)) == text, (
        "CREDITS.md is out of date: run scripts/gen_credits.py"
    )


# The license as the in-game CREDITS page writes it.
CREDITS_PAGE_LICENSES = {
    "CC0-1.0": "CC0",
    "OFL-1.1": "SIL OFL 1.1",
    "CC-BY-3.0": "CC BY 3.0",
}


def _credits_page_entries() -> list[str]:
    import yaml

    panels = yaml.safe_load((ROOT / "config" / "panels.yaml").read_text("utf-8"))
    objects = panels["panels"]["credits"]["objects"]
    return [o["text"] for o in objects.values() if isinstance(o, dict) and "text" in o]


def test_the_credits_page_lists_every_pack_with_its_own_license(sources):
    entries = _credits_page_entries()
    for pack in sources["packs"].values():
        label = CREDITS_PAGE_LICENSES[pack["license"]]
        names = [i for i, e in enumerate(entries) if pack["name"] in e]
        assert names, pack["name"]
        # The license is on the entry itself, or (CC BY, whose attribution
        # takes two lines first) on a line of its own right after them.
        assert any(
            label in entries[i] or label in entries[i + 1 : i + 3] for i in names
        ), pack["name"]


def test_the_credits_page_carries_the_music_attribution_lines():
    entries = _credits_page_entries()
    assert "Music : Sakura Girl - Day Off" in entries
    assert "Link : youtu.be/vAv9KtrU_5c" in entries
