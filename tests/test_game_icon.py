"""The game icon: every file it ships as exists and loads (Game() itself loads
the window icon, which scripts/smoke_test.py boots)."""

from pathlib import Path

import pygame

from app.game import WINDOW_ICON

ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = ROOT / "assets" / "images" / "icon"


def test_window_icon_loads_as_a_square_image():
    surface = pygame.image.load(ROOT / WINDOW_ICON)
    assert surface.get_width() == surface.get_height() >= 32


def test_exe_icon_has_every_size():
    # An .ico starts with a header: reserved 0, type 1 (icon), then the image count.
    data = (ICON_DIR / "highrise.ico").read_bytes()
    assert data[:4] == b"\x00\x00\x01\x00"
    assert int.from_bytes(data[4:6], "little") == 6


def test_store_icon_is_the_1024_master():
    assert pygame.image.load(ROOT / "docs" / "store" / "icon.png").get_size() == (
        1024,
        1024,
    )


def test_spec_uses_the_ico_for_the_executable():
    spec = (ROOT / "highrise.spec").read_text(encoding="utf-8")
    assert '"icon" / "highrise.ico"' in spec
