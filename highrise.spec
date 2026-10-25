# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build recipe for Highrise.

    pyinstaller highrise.spec --noconfirm

Produces a onedir bundle in ``dist/highrise/`` whose launcher is
``highrise`` (``highrise.exe`` on Windows). onedir is preferred over onefile
for a game: startup is instant (no per-launch temp extraction) and the assets
stay browsable next to the executable.

The ``assets/`` and ``config/`` trees are bundled as data and unpacked next to
the executable (``sys._MEIPASS``); the game resolves them cwd-relative, and
the launcher directory doubles as the cwd when double-clicked from Explorer/
Finder, so the same relative paths resolve as they do from source.
"""

import sys
from pathlib import Path

ROOT = Path(SPECPATH)  # noqa: F821 — injected by PyInstaller

# Runtime data trees the game loads by relative path.
datas = [
    (str(ROOT / "assets"), "assets"),
    (str(ROOT / "config"), "config"),
    # Attribution and license texts travel with every build.
    (str(ROOT / "CREDITS.md"), "."),
    (str(ROOT / "LICENSE"), "."),
    # pygamine's shared splash (standard_splash_media), resolved next to the
    # pygamine package rather than the game's assets/
    (str(ROOT / "src" / "pygamine" / "pygamine" / "branding"), "pygamine/branding"),
    # License texts of pygame-ce and the native libraries it bundles: inside
    # the bundle (on macOS, inside the .app) and, below, next to the executable.
    (str(ROOT / "src" / "pygamine" / "pygamine" / "licenses"), "licenses"),
    # The asset packs' own license texts (licenses/assets/<pack>.txt, see
    # assets/SOURCES.yaml), into the same licenses/ folder.
    (str(ROOT / "licenses"), "licenses"),
]

a = Analysis(
    ["__main__.py"],
    pathex=[str(ROOT / "src"), str(ROOT / "src" / "pygamine")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="highrise",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # windowed app — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="highrise",
)

# Third-party license texts (pygame-ce and the libraries it bundles; see
# src/pygamine/pygamine/licenses/README.md) next to the executable, where
# players look -- the datas copy above sits inside _internal/.
import shutil  # noqa: E402
_top = Path(DISTPATH) / "highrise"  # noqa: F821 -- injected by PyInstaller
for doc in ("CREDITS.md", "LICENSE"):
    shutil.copy2(ROOT / doc, _top / doc)
shutil.copytree(ROOT / "src" / "pygamine" / "pygamine" / "licenses", _top / "licenses", dirs_exist_ok=True)
shutil.copytree(ROOT / "licenses", _top / "licenses", dirs_exist_ok=True)

# On macOS, also wrap the onedir bundle as a .app for a native double-click.
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Highrise.app",
        icon=None,
        bundle_identifier="com.umutcanekinci.highrise",
    )
