# Architecture

A guided tour of how Highrise is put together, for people reading or changing the code. It is
deliberately high level: the code and its docstrings have the details, and
[`docs/decisions/`](decisions/README.md) records why the bigger choices were made. For how to build
and check changes, see [CONTRIBUTING.md](../CONTRIBUTING.md). (`CLAUDE.md` is the longer,
agent-facing version of this tour.)

## Project layout

```
__main__.py            Entry point: puts src/ and src/pygamine/ on sys.path, runs Game
src/app/               Game (the top-level class), its event and save mixins, action sounds
src/domain/            Pure data (Player: money)
src/gameplay/          Tilemap, tile selector, age tasks
src/gameplay/buildings/  Building, the Buildings collection, boosters, sprite recipes
src/gameplay/tiles/    Isometric tile and its geometry
src/gameplay/clouds/   The drifting background clouds
src/ui/                Info panel, cash display, odometer, floating texts, dust effect, task list, UI scale
src/util/              Frozen-build resource paths
src/pygamine/          Engine submodule (Application, PanelLoaderExt, Database, GameAudio, ...)
config/                YAML: assets, panels, settings, buildings, tasks, language files
assets/                Images, sounds, fonts (every file listed in assets/SOURCES.yaml)
scripts/               Smoke test, README media, cover and banner, credits and devlog generators
tests/                 The app's own pytest suite
docs/                  Devlog, decision records, design art, store page text, screenshots
```

The game is built on [pygamine](https://github.com/vectorviolet/pygamine), the author's own engine
layer on top of pygame-ce, pinned as a git submodule in `src/pygamine/`. A change there affects the
other games that use it.

## Entry point and the Game class

`__main__.py` creates `Game()` and calls `run()`. `Game` (`src/app/game.py`) extends
`pygamine.Application` plus two mixins: `GameEventsMixin` (`game_events.py`: routing mouse and key
events to the panels and the board) and `GamePersistenceMixin` (`game_persistence.py`: the SQLite
save, settings and loading). `Game` itself builds the panels, owns the buildings, tasks, audio and
effects, and ties them together; the pieces below don't import it, they get callbacks.

## Config-driven UI

Panels, buttons and layout are written in `config/panels.yaml` and built by pygamine's
`PanelLoaderExt`; Python code looks widgets up by name and never hard-codes UI positions or sizes.
`config/assets.yaml` is the asset manifest (fonts, images, sounds by key). The DISPLAY page's UI scale
is applied through the panel loader's scale and rebuilds the panels (`src/ui/ui_scale.py`), so code
that needs a widget's size reads it from the built widget.

Every player-visible string lives in `config/lang/<code>.yaml` (`en.yaml` is the reference and
fallback, `tr.yaml` is Turkish) and is looked up by key (`text_key:` in panels, `tr("key")` in code).
Tests check that every language file has the same keys and that the fonts can draw every character.
Money and percentages go through helpers (`src/ui/money_format.py`) so each language writes them its
own way.

## Tiles, buildings and merging

The board is an isometric grid of `Tile`s (`src/gameplay/tiles/`, collected by `Tilemap`);
selection uses point-in-quadrangle collision. `Buildings` (`src/gameplay/buildings/building.py`) is
the list of `Building`s on the board. It owns moving them (WASD or the arrows) with 2048-style
merging: same-level neighbors merge into one of the next level. Merges are collected during the move
and applied afterwards, and the board-changing actions (move, build, sell, NEXT AGE) wait while
`Buildings.is_busy()`. Buildings talk to the game through callbacks (`on_payout`, `on_merge`), see
[ADR 0001](decisions/0001-building-callbacks.md).

A building's picture is composed from Kenney pieces by the recipes in `config/buildings.yaml`
(`sprites.py`), cached per age, level and door side, with a thin outline. There are four ages
(`AGES`: wood, rock, sand, stone); advancing changes every building's look but keeps its level.

Boosters are buildings that earn nothing themselves but raise the income of the buildings on the
tiles they cover. Their numbers are `boosters` in `config/settings.yaml` (checked by `BoosterConfig`)
and their look is in `config/buildings.yaml`.

## Age tasks

`config/tasks.yaml` gives each age but the last two or three tasks (own a building of a level, earn
so much per second, have boosted buildings) and the NEXT AGE cost factor. `AgeTasks`
(`src/gameplay/tasks.py`, `Game.tasks`) measures them every frame, keeps the done ones, and unlocks
BOOST when the first age's tasks are done. The checklist over the NEXT AGE button is
`src/ui/task_list.py`.

## Money, feedback and effects

Spending goes through `Game._spend` and income through `Game._on_building_payout`, so the cash
display (`src/ui/cash_display.py`, with a rolling-digit `Odometer`) and the floating "+X$" texts
(`src/ui/floating_text.py`) always agree. Selling plays a dust burst (`src/ui/dust_effect.py`).
The info panel (`src/ui/info_panel.py`) shows the selected building at the window's right edge.

## Persistence

Saves are a SQLite database (`databases/database.db`, through pygamine's `Database`) with four
tables: `game` (age, map size, money, volumes), `tasks`, `buildings` (level, position, door side,
booster flag, held-back income) and `settings` (language, skip intro, UI scale, master volume). The
tables are created on first run and older ones are migrated. All of it is in
`GamePersistenceMixin`; leaving the board for the menu saves, and saving first finishes pending
merges. [ADR 0002](decisions/0002-settings-table.md) explains the separate settings table.

## Audio

Music plays on channel 0 and sound effects on a pool of channels, through pygamine's `GameAudio`; the
master volume scales both. Build (one sound per age), NEXT AGE and sell have their own sounds,
chosen from `action_sounds` in `config/settings.yaml` by `src/app/action_sounds.py`. The background
track is optional: without the `bg` entry in `config/assets.yaml` the game plays no music and hides
the music volume row.

## Tests and scripts

`tests/` is the app's own suite (pygamine has its own); `tests/conftest.py` sets dummy SDL drivers
and temporary saves so tests run headless and never touch a real save. Tests also guard the data:
`test_sources.py` (every asset has a source and license), `test_localization.py` and
`test_devlog_index.py` (the generated index tables). `scripts/smoke_test.py` boots the game headless;
`capture_readme.py` makes the README pictures, `make_cover.py` the cover and banner, and
`gen_credits.py` and `gen_devlog_index.py` the generated documentation sections.
