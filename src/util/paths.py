"""Filesystem anchors that work both from source and inside a PyInstaller bundle.

The game loads `assets/` and `config/` with paths relative to the current
working directory (e.g. ``game.py`` opens ``"config/assets.yaml"``). That only
holds when the process runs from the project root.

When PyInstaller freezes the app, data files bundled via the spec's ``datas``
are unpacked next to the executable (onedir) or extracted to a temp dir
(onefile); either way their location is exposed as ``sys._MEIPASS``. To keep
the existing relative paths valid in both modes, ``__main__`` chdirs into
:func:`resource_root` at startup.

Implementation lives in ``pygamine.assets.paths`` -- shared with every sibling
project, since the logic has nothing project-specific in it. Re-exported
here so existing ``from util.paths import resource_root`` call sites don't
need to change.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pygamine import resource_root as resource_root, resource_path as resource_path
from pygamine import user_data_dir

# The language files (config/lang/<code>.yaml), anchored to the resource root so
# the game, the tests and the smoke test all find them from any folder.
LANG_FOLDER = resource_path("config", "lang")


def packaged_databases_dir() -> Path | None:
    """Where the save database lives in the packaged (PyInstaller) build.

    The per-user folder, ``user_data_dir("highrise") / "databases"`` (under
    ``%APPDATA%`` on Windows), so an installer or an update never touches it.
    ``None`` from source: there ``Database`` keeps its cwd-relative ``databases/``
    default (ADR 0003), which keeps each worktree's saves apart.
    """
    if not getattr(sys, "frozen", False):
        return None
    return user_data_dir("highrise") / "databases"
