# 0003. Saves in the user-data folder (packaged build only)
<!-- index | refs: #57 -->

- **Status:** Accepted (owner, 2026-11-17)
- **Date:** 2026-11-18
- **Issues / PRs:** [#57](https://github.com/vectorviolet/highrise/issues/57)

## Context

The game kept its SQLite database in `databases/`, relative to the working directory. For a
downloaded build that means inside the game folder: an installer into `Program Files` can't write
there without admin rights, an uninstall or an update would delete the save with the folder, and a
portable zip moved to another folder loses it. Other things rely on the cwd-relative default today:
every worktree has its own `databases/`, and the tests redirect `Database`'s default folder
(`saves_in_tmp` in `tests/conftest.py`).

## Decision

- **The packaged build** (`sys.frozen`, PyInstaller) keeps its database in
  `user_data_dir("highrise") / "databases"` (pygamine): `%APPDATA%\VectorViolet\highrise\databases`,
  `~/Library/Application Support/VectorViolet/highrise/databases`, or `$XDG_DATA_HOME` (default
  `~/.local/share`)`/VectorViolet/highrise/databases`.
- **Running from source** keeps `Database`'s own default, the cwd-relative `databases/`. Highrise has
  no web build on `main`, so there is nothing to keep there.
- One helper decides, `util.paths.packaged_databases_dir()` (`None` means "use the default"), and
  `Game._make_database` is the only place that builds the `Database`.
- **No migration** of old saves next to the executable (the owner's decision).

## Consequences

An uninstall or update never touches the save, and it stays after an uninstall. Before this change
the packaged game wrote it into its own bundle folder (the game chdirs into `sys._MEIPASS`, which
for PyInstaller 6 is `highrise\_internal` on Windows and inside the app bundle on macOS), so old
saves are in `_internal\databases`. They are not moved; a player can copy `database.db` into the
new folder by hand. The installer deletes `_internal` on an update, so installing over an old
unzipped folder drops them (accepted by the owner). `tests/test_saves_location.py` checks both modes.

## Alternatives considered

- **User-data folder everywhere.** Breaks worktree save isolation and the tests' redirect, for no
  gain to players who run from source.
- **Migrating old saves.** Dropped by the owner.
