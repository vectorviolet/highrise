"""The game icon: every file it ships as exists and loads, and the window icon
falls back to the default instead of aborting startup (Game() itself calls
set_window_icon, which scripts/smoke_test.py boots)."""

import ast
import importlib.util
import io
import logging
import struct
import sys
from pathlib import Path

import pygame

from app.game import WINDOW_ICON, set_window_icon

ROOT = Path(__file__).resolve().parent.parent
ICO = ROOT / "packaging" / "icon.ico"
ICO_SIZES = {16, 32, 48, 64, 128, 256}

_spec = importlib.util.spec_from_file_location(
    "gen_credits", ROOT / "scripts" / "gen_credits.py"
)
gen_credits = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen_credits)


def test_window_icon_loads_as_a_square_image():
    surface = pygame.image.load(WINDOW_ICON)
    assert surface.get_width() == surface.get_height() >= 32


def test_set_window_icon_passes_the_loaded_image_on(monkeypatch):
    shown = []
    monkeypatch.setattr(pygame.display, "set_icon", shown.append)
    set_window_icon()
    assert len(shown) == 1
    assert shown[0].get_size() == pygame.image.load(WINDOW_ICON).get_size()


def test_missing_window_icon_is_logged_and_skipped(monkeypatch, tmp_path, caplog):
    shown = []
    monkeypatch.setattr(pygame.display, "set_icon", shown.append)
    with caplog.at_level(logging.WARNING):
        set_window_icon(tmp_path / "missing.png")
    assert shown == []
    assert "window icon" in caplog.text


def test_exe_icon_has_every_size_and_each_image_decodes():
    data = ICO.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", data, 0)
    assert (reserved, kind) == (0, 1)
    sizes = set()
    for i in range(count):
        width, height, _, _, _, _, length, offset = struct.unpack_from(
            "<BBBBHHII", data, 6 + 16 * i
        )
        width, height = width or 256, height or 256  # 0 means 256
        assert width == height
        sizes.add(width)
        image = data[offset : offset + length]
        assert length > 0 and len(image) == length
        assert pygame.image.load(io.BytesIO(image), "icon.png").get_size() == (
            width,
            height,
        )
    assert count == len(ICO_SIZES)
    assert sizes == ICO_SIZES


def test_design_icon_is_the_1024_master():
    assert pygame.image.load(ROOT / "docs" / "design" / "icon.png").get_size() == (
        1024,
        1024,
    )


def _spec_icon_block():
    """The spec's top-level `icon = None` ... if/elif block, as runnable code."""
    tree = ast.parse((ROOT / "highrise.spec").read_text(encoding="utf-8"))
    body = tree.body
    start = next(
        i
        for i, node in enumerate(body)
        if isinstance(node, ast.Assign)
        and [t.id for t in node.targets if isinstance(t, ast.Name)] == ["icon"]
    )
    block = ast.Module(body=body[start : start + 2], type_ignores=[])
    assert isinstance(block.body[1], ast.If)
    return compile(block, "highrise.spec", "exec")


def _chosen_icon(monkeypatch, tmp_path, platform, files):
    root = tmp_path / platform / "-".join(files)
    (root / "packaging").mkdir(parents=True)
    for name in files:
        (root / "packaging" / name).write_bytes(b"")
    monkeypatch.setattr(sys, "platform", platform)
    namespace = {"sys": sys, "ROOT": root}
    exec(_spec_icon_block(), namespace)
    return namespace["icon"]


def test_spec_picks_the_icon_per_os(monkeypatch, tmp_path):
    both = ("icon.ico", "icon.icns")
    ico = str(tmp_path / "win32" / "icon.ico-icon.icns" / "packaging" / "icon.ico")
    icns = str(tmp_path / "darwin" / "icon.ico-icon.icns" / "packaging" / "icon.icns")
    assert _chosen_icon(monkeypatch, tmp_path, "win32", both) == ico
    assert _chosen_icon(monkeypatch, tmp_path, "darwin", both) == icns


def test_spec_icon_is_none_when_the_file_is_missing(monkeypatch, tmp_path):
    assert _chosen_icon(monkeypatch, tmp_path, "win32", ("icon.icns",)) is None
    assert _chosen_icon(monkeypatch, tmp_path, "darwin", ("icon.ico",)) is None
    assert (
        _chosen_icon(monkeypatch, tmp_path, "linux", ("icon.ico", "icon.icns")) is None
    )


def test_spec_gives_the_executable_and_app_bundle_that_icon():
    tree = ast.parse((ROOT / "highrise.spec").read_text(encoding="utf-8"))
    for name in ("EXE", "BUNDLE"):
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == name
        ]
        assert len(calls) == 1
        keywords = {kw.arg: ast.unparse(kw.value) for kw in calls[0].keywords}
        assert keywords["icon"] == "icon"


def test_packaged_icon_is_where_the_spec_looks():
    assert ICO.is_file()
    assert "'packaging' / 'icon.ico'" in ast.unparse(
        ast.parse((ROOT / "highrise.spec").read_text(encoding="utf-8"))
    )


def test_credits_group_own_files_by_folder_and_say_when_ai_generated():
    files = {
        "a/one.png": {"source": "own"},
        "a/two.png": {"source": "own"},
        "b/three.png": {"source": "own"},
        "b/four.ico": {"source": "own", "generated_with": "Some Tool"},
        "c/packed.png": {"source": "some-pack"},
    }
    assert gen_credits.own_credit_lines(files) == [
        "Made for this game by its developer: one.png, two.png (in assets/a).",
        "AI-generated by its developer with Some Tool and post-processed: four.ico"
        " (in assets/b).",
        "Made for this game by its developer: three.png (in assets/b).",
    ]
