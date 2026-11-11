# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Game icon**: a pixel-art tower icon for the window and taskbar, the Windows executable (`highrise.spec`),
  the README and the store page (`docs/design/icon.png`)
  ([devlog](docs/devlog/2026-11-11-game-icon.md)).
- **Age tasks**: every age has 2 or 3 tasks (own a building of a level, earn so much per second,
  have boosted buildings). NEXT AGE needs all of them and now costs (age + 1) x 500; finishing the
  first age's tasks unlocks BOOST, which is locked until then. Done tasks stay done and are saved
  (older saves start the current age's tasks fresh; BOOST is unlocked past age 1). Progress shows
  as a checklist over NEXT AGE while the mouse is on it
  ([devlog](docs/devlog/2026-11-11-age-tasks.md)).
- **Building outline**: every building and booster sprite (board and info panel) gets a thin outline
  in a darker shade of its own edge colors, so stacked buildings of the same age stay readable. Width
  and darkening are `outline` in `config/buildings.yaml`
  ([devlog](docs/devlog/2026-11-11-building-outline.md)).
- With a building's info panel open, clicking another building (in selection mode) switches the
  panel to it; clicks on the panel never reach the board behind it, and a click on an empty tile
  leaves the panel as it is.
- **Boosters**: a BOOST button next to BUILD puts a booster (hex ring with a red roof) on a random
  empty tile. A booster earns nothing but raises the income of every building on the tiles it
  covers (wood: 4 neighbors, rock: 4 diagonals, sand: all 8 around it, stone: its row and column);
  overlapping boosters add up. Five levels, merged like buildings (booster with booster only);
  saved with the game, placeholder numbers in `config/settings.yaml`
  ([devlog](docs/devlog/2026-11-11-boosters.md)).
- **Eleven building levels** (was six): sprites are now composed from Kenney pieces by recipes in
  `config/buildings.yaml`, and every level adds one visible change (door, window, gate, floor, roof).
  Each building has a door side (left or right) that stays through merges and age changes, saved
  with the game (older saves get a fixed default). Levels 7-11 follow the same income and sell
  price formulas for now ([devlog](docs/devlog/2026-11-11-building-recipes.md)).
- Own sounds for **build** (one per age), **NEXT AGE** and **sell** instead of the UI click, and a dust and debris effect where a sold building stood. Sounds are set in `action_sounds` in `config/settings.yaml`; three Kenney sound packs (CC0) are credited
  ([devlog](docs/devlog/2026-11-11-action-sounds-and-sell-effect.md)).
- The CREDITS page opens with the "a VECTORVIOLET game" lockup and closes with GitHub and itch.io
  rows (`umutcanekinci`), using pygamine's bundled logos.
- **Menu polish** ([devlog](docs/devlog/2026-11-11-menu-polish.md)): buttons follow one color scheme
  (red leaves, cancels or destroys; green goes; blue is the rest), and CONTINUE is above
  NEW GAME on the PLAY page.
- A **CREDITS** page replaces the DEVELOPER page: scrolling sections for the developer, art, UI,
  sound, music, fonts and software, every pack with its license and the Day Off attribution. The
  social link buttons, the photo and their assets are gone
  ([devlog](docs/devlog/2026-11-10-credits-and-master-volume.md)).
- A **MASTER VOLUME** row at the top of the AUDIO page scales the music and every sound effect live.
  Saved in the database, 100 % by default.
- A **UI scale** setting on the DISPLAY page: 80 / 90 / 100 / 110 / 125 %, applied live and saved in
  the database, with a RESET UI SCALE button. Panels, menus, the HUD and their text scale together;
  the game world does not. The default stays 100 % until the owner picks one
  ([devlog](docs/devlog/2026-11-04-ui-scale.md)).
- Background music: **Sakura Girl - Day Off** ([CC BY 3.0](https://creativecommons.org/licenses/by/3.0/)),
  looping in the menu and in game. The MUSIC VOLUME setting and its row on the AUDIO page are back.
  Credit: "Music : Sakura Girl - Day Off", youtu.be/vAv9KtrU_5c (CREDITS.md, README).
- The GAME SETTINGS page has two settings, both saved in the database: **Language** (English or
  Türkçe, applied instantly, English by default) and **Skip intro** (off by default; when on, the
  game opens straight to the menu at the next launch).
- Every player-visible string lives in `config/lang/en.yaml`, with a draft Turkish translation in
  `config/lang/tr.yaml`. Tests check that both files have the same keys and that the font has every
  character ([devlog](docs/devlog/2026-11-04-language-and-skip-intro.md)).
- The cash amount **rolls like an odometer**: only the digits that change roll (up from the
  bottom when money goes up, down from the top when it goes down), 0.25 s per change
  (`ui.cash_roll_ms`); a change during a roll retargets to the newest amount
  ([devlog](docs/devlog/2026-11-10-cash-display-and-floating-text.md)).
- **Floating money text**: a green "+X$" rises over a building that paid or was sold, and a red
  "-X$" falls from the bottom of the cash amount when you build, upgrade (NEXT AGE) or expand. Every payout
  gets its own number. Colors, sizes, speed and lifetime are in `config/settings.yaml`
  (`floating_text`); the text scales with the UI scale
  ([devlog](docs/devlog/2026-11-10-cash-display-and-floating-text.md)).

### Fixed

- The BUILD button's hover text shows the price again after a merge frees tiles, instead of
  staying on TILES FULL.
- The red and green menu buttons turn yellow on hover like the blue ones.
- Percent values follow the language: "60%" in English, "%60" in Turkish.
- The GO BACK buttons on the settings pages are centered (they sat about 8 px to the right) and
  red like the other panels; the AUDIO page's rows are spaced like the DISPLAY page's.
- `Tile` draws its grid outline on a copy of the cached `tile` image instead of the shared one.
- Moves, building, selling and NEXT AGE wait until buildings stop sliding and merging, so a merge
  can no longer leave two buildings stacked on one tile. Saving mid-merge saves the finished merge,
  and selling from an info panel whose building just merged no longer crashes the game.

### Changed

- The cash display is a UI Pack plate (a coin, light text) instead of green text on black, with the
  same height and top/bottom line as the HUD buttons at every UI scale.
- The font is now Titillium Web (SIL OFL 1.1) instead of Kenney Future, which lacks the Turkish
  letters ğ Ğ ı İ ş Ş. Info panel text is two points larger and the value boxes on the settings pages
  use a darker gray, so they stay readable.
- CI also runs mypy and codespell (American English spelling), like Chokepoint's.
- Building movement is split into smaller methods; merge sounds and payout wiring
  use callbacks attached at creation ([devlog](docs/devlog/2026-10-30-building-callbacks.md)).

- The menu, settings and game panels use Kenney's current UI Pack instead of UI Pack version 1:
  the gray panel is now a white-to-gray gradient. The v1 pack and its license file are gone.
- Sound effects can overlap: pygamine 0.26.0 plays each one on a free mixer channel, so a new
  click, menu or merge sound no longer cuts off the one before it. The SFX volume setting
  applies to all of them.
- pygamine 0.27.0: skipping the splash with Space, Enter or a click no longer also triggers the
  first menu button.
- pygamine 0.28.0: buildings, clouds and tiles use the engine's `require_component()` and
  `require_image()` instead of `get_component()` plus a `None` assert, and the volume label uses
  `clamp01()`. No gameplay change.
- pygamine 0.29.0: the display stack moved into the engine's `Display` class and localization support
  was added (Highrise uses it since the Language setting). No gameplay change.
- Bump pygamine to v0.30.0: InputMap (rebindable key actions) and TooltipManager (tooltips with key
  prompts). No game changes yet; key bindings and tooltips come in their own PRs. The game reads
  `PanelManager.current_panel`, which is now a property in pygamine and behaves the same.
- Bump pygamine to v1.0.0 (the first stable release): panel loaders reject empty YAML entries, the
  loader's `parent:` links the GameObject parent so `active` follows the hierarchy, and the Tiled
  module is now `pygamine.assets.tiledmap`. No gameplay change.
- The engine submodule no longer follows pygamine's `main` on its own (`update = merge` removed
  from `.gitmodules`); it moves only through a reviewed bump PR.
- Dependabot opens one grouped PR a week with `uv.lock` updates (`.github/dependabot.yml`).
- README: a status badge row (CI, release, license, coverage, Python) under the title, and the official itch.io badge in the Download section ([chokepoint#150](https://github.com/vectorviolet/chokepoint/issues/150)).

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
