# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
# Install dependencies (resolved from pyproject.toml / uv.lock)
uv sync             # preferred — installs the locked dep set
# or for users without uv:
pip install .       # installs pygame-ce + pyyaml from pyproject.toml

# Run the game (__main__.py adds src/ and src/pygamine/ to sys.path)
python __main__.py
```

## Testing

```bash
uv run --group dev pytest tests/ -q                      # this app's own logic tests
uv run --group dev pytest tests/ --cov --cov-report=term  # with coverage
```

**Asset sources:** every file under `assets/` must be listed in `assets/SOURCES.yaml` with its
source pack (or `own`) and its original file name. Each pack needs its license text in
`licenses/assets/<slug>.txt`. CREDITS.md's asset section is generated from `SOURCES.yaml` by
`scripts/gen_credits.py`; don't edit it by hand. `tests/test_sources.py` enforces all of this.
Never add an asset whose origin and license you can't state. See README's "Asset sources".

**Devlog and ADRs:** every feature or design-decision PR adds or updates an entry in
`docs/devlog/` (`YYYY-MM-DD-short-title.md`); architecture choices get an ADR in
`docs/decisions/` (`NNNN-short-title.md`). Each entry carries an `<!-- index | refs: #N, PR #M -->`
comment right under its heading (see the READMEs' templates). The index tables in both READMEs are
generated: add your entry file, run `uv run python scripts/gen_devlog_index.py`, and never edit
the tables by hand. `tests/test_devlog_index.py` fails in CI if a table is out of date.

**Type check and spelling:** CI also runs `uv run --group dev mypy` (lenient: `src/` only,
`src/pygamine` excluded; config in `[tool.mypy]`) and `uv run --group dev codespell` (typos plus
British to American spelling; config in `[tool.codespell]`, project dictionary in
`.codespell-en-us.txt`). Fix the type or spelling; real words go in `ignore-words-list` with a reason.

**Code style:** run `uv run --group dev ruff format .` and `uv run --group dev ruff check .`
before every commit. Formatting is Black-compatible (`[tool.ruff.format]` in `pyproject.toml`);
lint (`[tool.ruff.lint]`) runs pyflakes (F), return-type annotations on every function in
`src/` (ANN201–ANN206; tests are exempt), no-self-use (PLR6301, a preview rule) and
complexity limits at ruff's defaults (C901 complexity 10, PLR0912 12 branches, PLR0915 50
statements). CI fails on `ruff format --check .` and on lint
errors. Keep pure reformatting out of feature commits; a repo-wide reformat goes in its own
commit, with its hash added to `.git-blame-ignore-revs`.

Note: several paths in this file (`src/game.py`,
`src/game_events.py`, `src/game_audio.py`, `src/building.py`, `src/cloud.py`, `src/tile.py`,
`src/ext/guiobject.py`) are stale — the actual layout has since moved to `src/app/`,
`src/domain/`, `src/gameplay/{buildings,clouds,tiles}/`, and `src/ui/` (see the test suite's
imports for the current module paths).

## Architecture Overview

### Entry Point and Game Class

`__main__.py` calls `Game().run()`. `src/game.py` defines the `Game` class, which inherits from `pygamine.Application` and three mixins: `GameEventsMixin` (`src/game_events.py`), `GamePersistenceMixin` (`src/game_persistence.py`), and `GameAudioMixin` (`src/game_audio.py`). These mixins handle event routing, SQLite save/load, and sound management respectively.

### pygamine — Shared Utility Package

`src/pygamine/` is a standalone, editable-installed package shared across multiple game projects. It provides:
- `Application` — base game loop class
- `AssetManager` + `ImagePath`/`FontPath`/`SoundPath` — asset loading/caching
- `PanelManager` + `PanelLoaderExt` — screen/panel management driven by `config/panels.yaml`
- `GameObject` / component system (`Transform`, `Rigidbody2D`, `SpriteRenderer2D`) — Unity-style entity model
- `Database` — SQLite wrapper (saves to `databases/database.db`)
- `MouseInteractive` mixin — mouse input for game objects

**Changes to `src/pygamine/` affect all games that depend on it.**

### Entity Hierarchy

```
pygamine.GameObject
├── StateObject (src/state_object.py) + MouseInteractive
│   ├── Building  (src/building.py)
│   └── Cloud     (src/cloud.py)
└── TextObject, InputBox  (pygamine ui_widgets)

GuiObject (src/ext/guiobject.py) — extends StateObject for UI elements
Button, ButtonText (src/button.py) — extend GuiObject
```

### YAML-Driven UI

All UI panels, buttons, and layout are declared in `config/panels.yaml`. Python code never hard-codes widget positions or sizes for UI — use `PanelLoaderExt` and `panel_factory.py` to wire YAML definitions to Python objects. `config/assets.yaml` declares the asset manifest (fonts, images by category).

### UI scale

The DISPLAY page's UI scale (`UI_SCALES` in `src/ui/ui_scale.py`, percent; default `DEFAULT_UI_SCALE`)
is applied by `Game.add_objects()` through `PanelLoader.scale`; `Game.set_ui_scale()` saves it and
rebuilds the panels. Panels scale about the window center, so edge-hugging chrome (the HUD bar) uses
`anchor: bottom` and children of a fixed-size root. Python code that needs a widget size reads it
from the built widget (`image.rect.size`), never from a hard-coded pixel count. Nine-slice borders and
padding are not scaled by the loader.

### Localization

Every player-visible string lives in `config/lang/<code>.yaml` (`en.yaml` is the reference and the
fallback; `tr.yaml` is Turkish), loaded with pygamine's `localization`. Panels use `text_key:` (and
`text_params:`) instead of `text:`; code uses `tr("section.key")`. Texts inside `states:` are not
key-driven in the engine, so `Game._on_language_changed` re-sets the ones the game builds from code
(toolbar hover texts, window-mode label, the Game settings labels, the percent values: write a percentage with `format_percent`, never by joining a "%" to a number; `common.percent` holds each language's order). Add a key to every language
file with the same `{placeholders}`: `tests/test_localization.py` fails otherwise, and fails when a
font in `assets/fonts/` lacks a character of any language (Titillium Web has no arrow, so don't use
one). Quote every value: a bare `yes` or `10` is not a string. Don't write `on:`/`off:` as keys: YAML
turns them into booleans.

### Menu button colors

Red (`red_button`) leaves, cancels or destroys (EXIT, every GO BACK, CANCEL, SELL), green goes (PLAY,
CONTINUE, SAVE, BUILD, BOOST), blue is the rest; `tests/test_menu_polish.py` lists every button's color, so add a
new button there.

### Credits page

The CREDITS page (`credits` panel) scrolls its sections with pygamine's `scrolling_panel`; `Game.open_panel` restarts it each time (content enters from below). Its entries are written in `config/panels.yaml`: when an asset pack is added to `assets/SOURCES.yaml`, add it there too (`tests/test_sources.py` checks).

### Isometric Tilemap

`src/tile.py` renders an isometric diamond grid. Tile selection uses point-in-quadrangle collision. Selected tiles visually shift up by 10 px. Building movement (WASD/arrows) triggers 2048-style merge logic: same-level adjacent buildings merge and level up.

### Buildings

`Buildings` owns movement and replacement construction. Use `Buildings.create`
for production building creation (purchase/load, merge and age change) so the
collection's `on_payout` callback (`(building, amount)`) is passed in. `Building` requires `on_payout`
as a keyword-only argument (`None` for no income), so it can't be forgotten.
`on_merge` delegates the merge sound to `Game`; the collection has no
asset/audio dependency. Merges are collected during movement checks and applied
after iteration, then sorted by column. Keep the existing next-frame merge after
arrival. Board-changing actions (moves, build, sell, NEXT AGE) wait while
`Buildings.is_busy()`; the one guard is in `GameEventsMixin.handle_game_events`.
Saving finishes pending merges first. See ADR 0001.

Building sprites are composed from Kenney pieces (`assets/images/buildings/`) by the recipes in
`config/buildings.yaml` (`gameplay/buildings/sprites.py`), cached per (age, level, door side);
level N is entry N of `levels`, and `max_building_level` may not exceed the number of entries. The
only variety is the door side (left or right): random when a building is built, saved in the
`buildings` table (old saves get a fixed default from row and column), kept by a merge (the
survivor's side) and an age change. Each level adds one visible change (the `adds` notes in the
recipes); shutter pieces are kept free for #72. `scripts/render_building_styles.py` renders the
sprites for the devlog.

Boosters (issue #51) are `Building`s with a `booster_multiplier` (None for a normal building;
`is_booster`), no payout callback and speed 0. They come from `Buildings.create(..., booster=True)`
(`Game.create_booster`, the BOOST button, locked until `Game.tasks.boost_unlocked`, see Age tasks) and keep their kind through merges, age changes and saves. Their numbers (price per age,
multiplier per level, shape per age) are `boosters` in `config/settings.yaml`, checked by
`gameplay/buildings/boosters.py` (`BoosterConfig`; the shapes themselves are code, selected by
name); their look is the `boosters` section of `config/buildings.yaml` (the ring piece with a red
roof; the sprite cache key and the sprite functions take `booster`), and the level counts of both
must match. The boost belongs to the tile: `Buildings.income_multiplier(building)` is 1 plus the
bonuses (multiplier - 1) of every booster covering the building's tile, and
`Game._on_building_payout` applies it (`Building.boosted_income` keeps the fractions a payout can't
pay; a merge adds both buildings' fractions and pays the whole dollar through `on_carried_income` (a building never holds 1$ or more), an age change keeps them, a save keeps them in
`buildings.income_fraction`). `Buildings`
needs its `BoosterConfig` passed in (`Game` builds it once, checking the multiplier count against the
booster sprite levels; tests use `BoosterConfig.load`); a booster has no payout timer. Boosters merge only with a booster of the same level, up to their own maximum level; normal
buildings never merge with them. While a booster's info panel is open, or the mouse is over a booster (info panel closed, game
panel), `Game._highlight_boosted_tiles` sets `Tile.highlighted` on the tiles it covers; it walks the
tiles only when the shown booster, its tile or age, or the board changes. A booster just placed
with BOOST also stays lit for `boosters.placed_highlight_ms` (the open panel and the hover win). The info panel sits at the
window's right edge (`anchor: right` in `config/panels.yaml`, its content parented to it) so the
board stays visible; `tests/test_info_panel_layout.py` checks it at every UI scale.

### Age tasks

Issue #52. `config/tasks.yaml` gives every age but the last 2 or 3 tasks (`building_level`,
`income_per_second`, `boosted_buildings`; the measures are `MEASURES` in `gameplay/tasks.py`, the
texts are `tasks.<type>` in the language files), the NEXT AGE cost factor (`next_age_cost_factor`: cost
is (age number + 1) x factor) and `ui`. `AgeTasks` (`Game.tasks`) holds the current age's done tasks
(latched: a done task stays done), `boost_unlocked` (latched; set when the first age's tasks are done
or when entering any later age) and the cost. `Game._update_tasks` runs every frame and `Game.next_age`
checks tasks and cash before paying. State is saved in the `tasks` table (`GamePersistenceMixin.load_tasks`
/ `save_tasks`); an old save starts its tasks fresh and has BOOST unlocked past age 1. `ui` picks how the
checklist (`ui/task_list.py`) shows: `hover` over the NEXT AGE button, or `panel` at the top left; the
owner is choosing one (see the devlog), the other is then removed.

### Cash display and floating money text

The cash display is `money_panel` (plate), `money_icon` (coin) and `money_text` in `config/panels.yaml`,
on the buttons' top and bottom line. `ui/cash_display.py` paints the plate and coin. Money changes show `ui/floating_text.py` texts, numbers in
`floating_text` in `config/settings.yaml`: `Game._on_building_payout` and `show_gain` (payouts, sales) and
`Game._spend` (build, upgrade, expand, NEXT AGE; always spend through it, not `Player.spend`). Amounts are
written by `ui/money_format.py` (`money.amount` and `money.thousands` in the language files: "12,345$", Turkish
"12.345$"), for the cash display, the prices and the texts alike. Every payout gets its own text.
The cash amount is drawn by `ui/odometer.py` (rolling digits, `ui.cash_roll_ms`): `money_text` is hidden and
only gives the layout (anchored rectangle, font, color); the odometer owns the text, `Game._on_money_changed` feeds it,
and a language change snaps it (`Game._on_language_changed`). A text too wide for the room right of the coin is scaled down.
World texts are hidden while the info panel is open. A building's
`on_payout` callback takes `(building, amount)`.

### Persistence

SQLite database at `databases/database.db`. Four tables: `game` (age, map size, money, volumes), `tasks` (done tasks of the current age, BOOST unlocked; one row), `buildings` (level, row, column, door side, booster flag, held-back income fraction; old tables are migrated, old rows are plain buildings with no fraction) and `settings` (language, skip intro, UI scale, master volume; the first three are saved the moment they change on the Game and Display settings pages, the master volume with the AUDIO page's SAVE; all kept by New Game). The database auto-initializes on first run. Save/load logic lives entirely in `GamePersistenceMixin`.

### Audio

Channel 0 plays the looping music. Each SFX plays on a free channel from pygamine's pool (channels 3 and up; 1 and 2 are reserved and unused here), so SFX overlap; if all are busy the new sound is dropped. The SFX volume applies to the whole pool. The master volume (first row of the AUDIO page) scales the music and the SFX pool through pygamine's `GameAudio`. The music and SFX volumes are stored in the `game` table, the master volume in `settings`, and all are applied on load. All audio logic is in `GameAudioMixin`.

Build (one sound per age), NEXT AGE and sell have their own sounds, named in `action_sounds` in `config/settings.yaml` and looked up by `app/action_sounds.py` (`Game.action_sounds`); they play through `play_sfx` like every other SFX. A sale also starts the dust effect of `ui/dust_effect.py` (`Game.sell_effect`, drawn as a world object under the HUD, numbers in `sell_effect` in `config/settings.yaml`).

Background music is optional: the game plays the `bg` sound from `config/assets.yaml` if it's there. Without it, the game plays no music and hides the music volume row on the AUDIO settings screen (`MUSIC_KEY` / `MUSIC_VOLUME_OBJECTS` in `app/game.py`). The track is Sakura Girl - Day Off (CC BY 3.0, `assets/sounds/bg.mp3`); its attribution ("Music : Sakura Girl - Day Off", youtu.be/vAv9KtrU_5c) lives in CREDITS.md and README. Any other track needs a license that allows bundling it in the game.
