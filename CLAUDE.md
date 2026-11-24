# CLAUDE.md

This file guides Claude Code in this repo. Setup, run, test and lint commands: README, CONTRIBUTING.md, `pyproject.toml`, CI.
The module layout and subsystem tours: `docs/ARCHITECTURE.md` (layout, entry point, subsystems) and the code.

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

**README media:** `docs/preview.gif` and `docs/screenshots/01-03` come from
`uv run --group dev python scripts/capture_readme.py` (headless, seeded, saves in a temp folder; it
also writes the devlog's candidate pictures). A PR that changes how the game looks reruns it and
commits the changed pictures.

**Type check and spelling:** CI also runs `mypy` (lenient, `src/` only; config in `[tool.mypy]`) and
`codespell` (typos plus British to American spelling; project dictionary in `.codespell-en-us.txt`).
Fix the type or spelling; real words go in `ignore-words-list` with a reason.

**Code style:** run `uv run --group dev ruff format .` and `uv run --group dev ruff check .` before
every commit (rules in `pyproject.toml`; CI fails on either). Keep pure reformatting out of feature
commits; a repo-wide reformat goes in its own commit, with its hash added to `.git-blame-ignore-revs`.

## Architecture notes

`src/pygamine/` is a git submodule shared with other games: **changes there affect all of them.**

### YAML-driven UI

All UI panels, buttons and layout are declared in `config/panels.yaml`. Python code never hard-codes
widget positions or sizes for UI: use `PanelLoaderExt` and `panel_factory.py` to wire YAML to objects.

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
new button there. Every button's hover (and keyboard-focus) face is the yellow `yellow_button`, so text on a button is
`type: button_text` in `config/panels.yaml` (`ui/button_text.py`, registered in `Game.build_panels`): white as written, dark navy
#1E1D3B (`YELLOW_TEXT_COLOR`) while the button shows its yellow face; `tests/test_button_text.py` checks every text on a hoverable
button is one. Use `button_text`, not `text`, for a new button's label.

### Credits page

The CREDITS page (`credits` panel) scrolls its sections with pygamine's `scrolling_panel`; `Game.open_panel` restarts it each time (content enters from below). Its entries are written in `config/panels.yaml`: when an asset pack is added to `assets/SOURCES.yaml`, add it there too (`tests/test_sources.py` checks).

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
recipes); shutter pieces are kept free for #72. The world and info panel sprites get a thin outline
(`sprites.outline`, `outline` in the recipes: width and darken factor): the silhouette's outermost
pixels recolored darker, inside the surface so size, anchor and click area don't change; built once
with the cached sprite. `scripts/render_building_styles.py` renders the
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
is (age number + 1) x factor). Targets are checked at load
(`TasksConfig.load(ages, max_level, max_tiles)`: a target the game can't reach is a ValueError).
`AgeTasks` (`Game.tasks`) reads the age from `Buildings.age_number` (no copy) and holds the done tasks
(latched, keyed by age: a done task stays done), `boost_unlocked` (latched when the first age's tasks are
done; any later age counts too) and the cost. `Game._update_tasks` runs every frame: `AgeTasks.update()`
measures each task once and stores `values` (the checklist reads them), and a newly done task refreshes
the button texts (BOOST and NEXT AGE show `game.locked` until their tasks are done). `Game.next_age`
checks tasks and cash before paying. State is saved in the `tasks` table (`GamePersistenceMixin.load_tasks`
/ `save_tasks`); an old save starts its tasks fresh and has BOOST unlocked past age 1. The checklist (`ui/task_list.py`) shows over the NEXT AGE button while the mouse is on it.

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

SQLite database `database.db`: in `databases/` (cwd-relative) when run from source, in `user_data_dir("highrise") / "databases"` (`%APPDATA%\VectorViolet\highrise\databases` on Windows) in the packaged build (pygamine's `packaged_data_dir("highrise", "databases")`, `Game._make_database`; ADR 0003). The installer (`packaging/highrise.iss`, built by the release workflow's `installer` job) keeps its `[Languages]` list equal to `config/lang/` (`tests/test_installer.py`). Tables `game`, `tasks`, `buildings`, `settings`: old tables are migrated, old building rows are plain buildings with no fraction. `settings` (language, skip intro, UI scale, master volume): the first three are saved the moment they change on the Game and Display settings pages, the master volume with the AUDIO page's SAVE; all are kept by New Game.

**Browser build (issue #97, ADR 0004):** `WebPersistenceMixin` delegates to the SQLite mixin on desktop and, when `util/web.is_web()` is true (pygbag, `sys.platform == "emscripten"`), keeps progress and settings as JSON in localStorage through pygamine's public `SaveStore` (`highrise-save`, `highrise-settings`; no SQLite import and no `Database` on that path). Restoring reads the save once, holds every value to a valid one (the building loop is `GamePersistenceMixin._restore_building`, shared with desktop) and never touches the board halfway. A stored save that can't be read is kept (and Continue hidden) until an explicit New Game. The board saves on ESC and also 2 s after a build, sell, move, merge, NEXT AGE or expand, and every 10 s while the game panel is open if money or the board changed (the payouts) (`request_autosave` / `autosave_if_due`), because a closed tab raises no QUIT. One notice (`storage.unavailable`, through `util/web.show_notice`) tells the player when nothing survives a reload: `util/web.storage_available()` probes localStorage once (blocked storage makes `SaveStore` fall back to memory, which looks like a working save), and `save_game` reads the save back to catch a refused write. `util/web.py` is the only module that talks to the page (fullscreen, opening the itch.io page, the notice box in `web/template.tmpl`); tests fake it with the `browser` fixture in `tests/conftest.py`. Exit opens the `thanks` panel instead of quitting.  `uv run python scripts/build_web.py` builds the bundle in `build/web/`. The browser renders `WEB_FPS` frames a second while the motion (buildings sliding, clouds) steps per update, so `Game._update_web_motion` adds the steps (`Game._motion_step`: the buildings twice and both cloud kinds, as a desktop update does) the elapsed time owes, at the desktop's `window.fps` rate; `tests/test_web.py` counts them per second against desktop. Inactive (hidden) buttons are ignored where activation happens (`GameEventsMixin._clicked` / `_is_activated`), and a hidden Continue is left out of the play menu's keyboard controller (`Game._play_buttons`).

### Audio

Channel 0 is the looping music; SFX use pygamine's pool (channel 3 up; 1 and 2 are reserved and unused here), and a sound is dropped when all are busy. Master volume scales music and SFX through `GameAudio`; music and SFX volumes are in the `game` table, the master volume in `settings`.

Build (one sound per age), NEXT AGE and sell have their own sounds, named in `action_sounds` in `config/settings.yaml` and looked up by `app/action_sounds.py` (`Game.action_sounds`); they play through `play_sfx` like every other SFX. A sale also starts the dust effect of `ui/dust_effect.py` (`Game.sell_effect`, drawn as a world object under the HUD, numbers in `sell_effect` in `config/settings.yaml`).

Background music is optional: the game plays the `bg` sound from `config/assets.yaml` if it's there. Without it, the game plays no music and hides the music volume row on the AUDIO settings screen (`MUSIC_KEY` / `MUSIC_VOLUME_OBJECTS` in `app/game.py`). The track is Sakura Girl - Day Off (CC BY 3.0, `assets/sounds/bg.ogg`); its attribution ("Music : Sakura Girl - Day Off", youtu.be/vAv9KtrU_5c) lives in CREDITS.md and README. Any other track needs a license that allows bundling it in the game.
