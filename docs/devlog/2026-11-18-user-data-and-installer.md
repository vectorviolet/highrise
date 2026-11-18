# Saves in the user-data folder and a Windows installer
<!-- index | refs: #57 | area: Platform, release -->

**Date:** 2026-11-18 · **Area:** Platform, release · **Issue:** [#57](https://github.com/vectorviolet/highrise/issues/57) · **ADR:** [0003](../decisions/0003-saves-in-the-user-data-folder.md)

## Context

The Windows download was a zip: unzip anywhere, run `highrise.exe`. Players expect an installer
(Start Menu entry, an uninstall entry, a folder of their choice), and a game in `Program Files`
can't write its save next to its exe. So the save moves to the per-user data folder first, and the
installer builds on that. This is the same change Chokepoint got.

## Options

Where the save goes (details in the ADR): the user-data folder everywhere, or only in the packaged
build. Installer tools: Inno Setup, or the Windows Installer (MSI) route with WiX.

## Decision

- **Save:** user-data folder in the packaged build only; source unchanged. Owner: no migration of
  old saves.
- **Installer: Inno Setup**, one script (`packaging/highrise.iss`). It asks for the language
  (English or Turkish, the game's languages; the choice does not set the game's language), shows
  the folder page (default `Program Files\highrise` for all users, which asks for admin rights; the
  privileges dialog also offers "only for me", which installs per-user), adds a Start Menu shortcut
  and an optional desktop one, and installs the PyInstaller onedir output. The uninstaller removes
  only the install folder; the save lives in `%APPDATA%` and stays. It uses only Inno's built-in
  texts, so there are no custom strings to translate. A test keeps the installer's language list
  equal to `config/lang/`.
- **Release:** an `installer` job compiles the installer from the Windows zip and uploads it as
  `highrise-windows-setup.exe`; `attach-installer` adds it to the GitHub Release. itch.io keeps
  getting the zips, and a failed installer build never blocks the zips, the release or itch.io. An
  update deletes the old `_internal` folder first, so no stale files stay.
- Unsigned, like the zips: the README explains SmartScreen's "More info, Run anyway".

## Rejected alternatives

- **WiX/MSI:** more setup and XML for no benefit to a single-exe-folder game.
- **A one-file self-extracting exe:** no uninstaller or shortcuts.
- **Installer language sets the game's language:** the owner asked for the lists to be in sync only.

## Result

Screenshots of the installer's language dialog and folder page are not included: they come from a
running installer, and the CI artifact was only smoke-tested silently. The owner does the
interactive check.

## Revisit if

- A new game language is added (the sync test fails until the installer has it).
- We sign the installer or ship it through a store.
