"""The index tables in docs/devlog/README.md and docs/decisions/README.md are
exactly what scripts/gen_devlog_index.py builds from the entry files, and
every entry carries the metadata the script needs."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "gen_devlog_index", ROOT / "scripts" / "gen_devlog_index.py"
)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def test_readme_tables_are_generated_from_the_entries():
    for readme, table in gen.targets():
        text = readme.read_text(encoding="utf-8")
        assert gen.updated_readme(text, table) == text, (
            f"{readme.relative_to(ROOT).as_posix()} is out of date: "
            "run scripts/gen_devlog_index.py"
        )


def test_every_entry_file_is_indexed():
    for folder, entries in (
        (gen.DEVLOG, gen.devlog_entries()),
        (gen.DECISIONS, gen.adr_entries()),
    ):
        names = {p.name for p in folder.glob("*.md") if p.name != "README.md"}
        assert {e.path.name for e in entries} == names, folder.name


def test_metadata_comment_is_required(tmp_path):
    (tmp_path / "2026-01-01-no-meta.md").write_text(
        "# No meta\n\n**Date:** 2026-01-01 · **Area:** UI\n", encoding="utf-8"
    )
    with pytest.raises(gen.EntryError, match="metadata comment"):
        gen.devlog_entries(tmp_path)


def test_rows_sort_by_date_and_number(tmp_path):
    devlog, adrs = tmp_path / "devlog", tmp_path / "decisions"
    devlog.mkdir()
    adrs.mkdir()
    for name in ("2026-02-01-b.md", "2026-01-01-a.md"):
        (devlog / name).write_text(
            f"# {name}\n<!-- index | refs: #1 -->\n\n**Date:** x · **Area:** UI\n",
            encoding="utf-8",
        )
    assert [e.fields["date"] for e in gen.devlog_entries(devlog)] == [
        "2026-01-01",
        "2026-02-01",
    ]
    for number, status in (("0002", "Accepted"), ("0001", "Superseded (by 0002)")):
        (adrs / f"{number}-x.md").write_text(
            f"# {number}. T{number}\n<!-- index | refs: #{number} -->\n\n"
            f"- **Status:** {status}\n- **Date:** 2026-01-0{number[-1]}\n",
            encoding="utf-8",
        )
    assert gen.render_adrs(gen.adr_entries(adrs)).splitlines()[2:] == [
        "| [0001](0001-x.md) | T0001 | Superseded | 2026-01-01 | #0001 |",
        "| [0002](0002-x.md) | T0002 | Accepted | 2026-01-02 | #0002 |",
    ]


def test_missing_markers_name_the_readme():
    with pytest.raises(gen.EntryError, match="docs/devlog/README.md"):
        gen.updated_readme("no markers here\n", "new", "docs/devlog/README.md")
