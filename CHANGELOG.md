# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Sound effects can overlap: pygamine 0.26.0 plays each one on a free mixer channel, so a new
  click, menu or merge sound no longer cuts off the one before it. The SFX volume setting
  applies to all of them.
- pygamine 0.27.0: skipping the splash with Space, Enter or a click no longer also triggers the
  first menu button.
- The engine submodule no longer follows pygamine's `main` on its own (`update = merge` removed
  from `.gitmodules`); it moves only through a reviewed bump PR.

## [0.2.4] – 2026-10-25

### Changed

- Every asset now has a known source and a license that allows shipping it. Files of unknown
  origin were replaced with Kenney CC0 art:
  - the clouds, from Background Elements Remastered;
  - the info, plus and minus icons, from Game Icons;
  - the mouse cursor, from Cursor Pack's outlined pointer, now drawn at its native 32×32.
- The developer screen links to GitHub and itch.io, using the official logos that ship with
  pygamine. The LinkedIn link is removed.
- `CREDITS.md` lists every asset pack, generated from the new `assets/SOURCES.yaml`. Each
  pack's own license text ships in `licenses/assets/`.

### Added

- `assets/SOURCES.yaml`: the source pack and original file name of every file under `assets/`,
  checked by the test suite.
- Code style: Black-compatible formatting with `ruff format` and linting with `ruff check`, both
  enforced in CI.

## [0.2.3] – 2026-10-25

### Removed

- Removed background music (unlicensed third-party track). New music will come in a later release.
  The music volume control on the AUDIO settings screen is hidden until then.

### Added

- `CREDITS.md`, replacing `ASSETS.md`: every asset, font and library with its license. It
  ships with the game next to `LICENSE`, along with a `licenses/` folder holding the license
  texts of pygame-ce and the native libraries it bundles.

### Changed

- pygamine updated to 0.24.0.

## [0.2.2] – 2026-10-25

### Removed

- The Kenney logo from the main menu. It isn't covered by the CC0 license of Kenney's asset
  packs; the packs themselves stay credited by name and link.

### Changed

- The startup splash shows pygame-ce's "powered" logo instead of the original pygame logo.
- pygamine updated to 0.20.1.

## [0.2.1] – 2026-10-24

### Added

- Tests for the modules that had no coverage.

### Changed

- Startup now opens with the shared splash all the sibling games use: the publisher clip, then
  the pygame logo.
- pygamine updated to 0.19.0, now at `vectorviolet/pygamine`; repo links point at `vectorviolet`.
- The smoke test now runs the game's real `run()`, splash included, instead of stepping frames by hand.

## [0.2.0] – 2026-08-12

### Added

- CI workflow running `pygamine`'s test suite, a real app-level test suite covering the 2048-style
  merge mechanic, and an app-level smoke test that boots `Game()` and cycles every panel.

### Changed

- Renamed the `pygame_core` submodule/dependency to `pygamine`.

### Fixed

- Editable `pygame-core` install not actually taking effect.
- A stale `pygamine` deep-path reference in `src/util/paths.py`'s docstring.

## [0.1.1] – 2026-07-08

- Added a window mode picker to Display Settings; fixed resize/layout bugs.
- Documented the Windows SmartScreen warning; storefront docs reorganized.

## [0.1.0] – 2026-07-07

Initial release. 2048-style building-merge game, migrated onto `pygame_core` and renamed to Highrise,
with a splash screen, PyInstaller build/release automation, and itch.io publishing.
