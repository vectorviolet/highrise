# Contributing to Highrise

How to build, check and change the game. The [README](README.md) is the player-facing front
page, and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) explains how the code fits together.
`CLAUDE.md` is the same knowledge written for coding agents.

## Setup

Python 3.12+ and [uv](https://docs.astral.sh/uv/) are needed (pygame-ce and pyyaml are resolved
from `pyproject.toml` and `uv.lock`). The engine is a git submodule:

```bash
git clone --recurse-submodules https://github.com/vectorviolet/highrise.git
cd highrise
uv sync
uv run python __main__.py
```

In a fresh worktree or after a pull that moves the engine, run `git submodule update --init`
(on Windows, `scripts\sync-pygamine.bat` does the same).

## Checks

Run these from the project folder before every commit; CI runs the same:

```bash
uv run --group dev pytest tests/ -q                       # the app's own tests
uv run --group dev pytest tests/ --cov --cov-report=term  # with coverage
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run python scripts/smoke_test.py  # boots the game headless
uv run --group dev ruff format --check .                  # formatting (drop --check to reformat)
uv run --group dev ruff check .                           # lint
uv run --group dev mypy                                   # types (lenient, src/ only)
uv run --group dev codespell                              # typos, American English
```

The tests and the smoke test keep their saves in temporary folders. A script of your own that
creates a `Game()` must do the same, so it never touches a real save in `databases/`.

### Code style

- **Formatting:** Black-compatible, enforced by `ruff format` (line length 88, double quotes).
- **Lint:** `ruff check`: pyflakes, a return type on every function in `src/`, no-self-use and
  complexity limits (see `[tool.ruff.lint]` in `pyproject.toml`).
- **Spelling:** American English everywhere (code, docs, comments). Real words that codespell
  flags go in `ignore-words-list` in `pyproject.toml`, with a reason.
- The `src/pygamine` submodule is excluded from all of these; it has its own setup and CI.
- The commit that first applied the formatter is in `.git-blame-ignore-revs`. To have `git blame`
  skip it: `git config blame.ignoreRevsFile .git-blame-ignore-revs`.

## Asset sources

Every file under `assets/` is listed in `assets/SOURCES.yaml`; the README's
[Asset sources](README.md#asset-sources) section has the rules and the steps. Only add assets whose
license allows bundling them in a distributed game.

## Pull requests, devlog and ADRs

1. Fork, clone with `--recurse-submodules`, and create a branch (`feature/<name>`).
2. Run the checks above. Stage the files you changed by explicit path.
3. Open a pull request. The title is a conventional prefix and a plain description (for example
   "fix: Merged buildings keep their door side"), without an issue number; link the issue in the
   body with "Closes #N".
4. A feature or design-decision PR adds or updates an entry in [`docs/devlog/`](docs/devlog/README.md)
   (`YYYY-MM-DD-short-title.md`: context, options with screenshots, decision, rejected, result);
   an architecture choice gets an ADR in [`docs/decisions/`](docs/decisions/README.md). Add the file,
   then run `uv run python scripts/gen_devlog_index.py` to rebuild the index tables (never edit them
   by hand; `tests/test_devlog_index.py` fails when they are stale). Add a line to
   [CHANGELOG.md](CHANGELOG.md) for what players see.
5. `main` is protected: changes land through a pull request whose required checks pass.

## README media

`docs/preview.gif` and `docs/screenshots/` come from the current game with:

```bash
uv run --group dev python scripts/capture_readme.py
```

It runs the game headless with a seeded random generator and temporary saves, and also writes the
devlog's candidate pictures. A PR that changes how the game looks reruns it and commits the changed
pictures. The screenshots stay at full 1920x1080.

## Cover and banner

`docs/design/cover.png` and `docs/design/banner.png` (and their itch.io copies in `docs/store/`) are
built from the text-free art in `docs/design/art/`, with the title and tagline drawn by one shared
definition:

```bash
uv run --group dev python scripts/make_cover.py
```

To change the title text, font, colors or positions, edit the script and rerun it. Don't edit the art
files; see [docs/design/README.md](docs/design/README.md) for where each picture comes from.

## Building a standalone bundle

[PyInstaller](https://pyinstaller.org/) builds it from `highrise.spec`, which bundles `assets/` and
`config/` next to the executable (onedir):

```bash
uv sync --group build
uv run pyinstaller highrise.spec --noconfirm
```

The result lands in `dist/highrise/` (`dist/Highrise.app` on macOS).

### Cutting a release

A release goes through a "Release x.y.z" PR (version and changelog), then the owner tags the merged
commit `vx.y.z`. The tag triggers [`.github/workflows/release.yml`](.github/workflows/release.yml),
which builds each OS, attaches the zips to a GitHub release and pushes each build to its
[itch.io](https://umutcanekinci.itch.io/highrise) channel with
[Butler](https://itch.io/docs/butler/). **Run workflow** builds without publishing.
