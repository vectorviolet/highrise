"""Headless boot check -- catches config/panel wiring mistakes that only
surface once objects are actually built (e.g. a panels.yaml entry missing a
required key). Run locally with:

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run python scripts/smoke_test.py

Requires cwd = repo root (matches how __main__.py and CI both invoke it).
Runs against a throwaway database in a temp folder, so it never touches (or
depends on) the developer's real databases/database.db: the settings are the
defaults, which includes showing the intro, so the splash really runs.
"""

import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, "src")
sys.path.insert(0, "src/pygamine")

PANELS = (
    "menu",
    "play",
    "settings",
    "display_settings",
    "audio_settings",
    "game_settings",
    "credits",
    "game",
)


def check_config_yaml() -> None:
    for path in sorted(Path("config").rglob("*.yaml")):
        yaml.safe_load(path.read_text(encoding="utf-8"))
        print(f"  {path}: OK")


def boot_game() -> None:
    from app.game import Game
    from ui.ui_scale import DEFAULT_UI_SCALE, UI_SCALES

    from pygamine.util.localization import localization

    game = Game()
    # Mirrors Game.run() up to (not including) the blocking super().run()
    # loop and the splash screen / background music, which don't apply
    # headlessly.
    game.init_database()
    game._apply_settings(game.load_settings())
    game.load_data()
    game.tile_selector.tilemap = game.tilemap
    game.add_objects()
    game._reset_session_ui()
    game.open_panel("menu")

    # Every panel in every language, the way a live switch leaves them.
    game.watch_language()
    try:
        for code in sorted(localization.languages()):
            localization.set_language(code)
            for panel in PANELS:
                game.open_panel(panel)
                game.update()
                game.draw()
                print(f"  {panel} ({code}): OK")
        # Every UI scale step, rebuilding the panels live as the setting does.
        for scale in UI_SCALES:
            game.set_ui_scale(scale)
            for panel in PANELS:
                game.open_panel(panel)
                game.update()
                game.draw()
            print(f"  every panel at UI scale {scale}%: OK")
        game.set_ui_scale(DEFAULT_UI_SCALE)
    finally:
        game.unwatch_language()
        localization.set_language("en")


def run_game_briefly() -> None:
    # The path the steps above never touch: the splash, any run() override
    # and the hand-off into the main loop (a crash there once shipped unseen).
    from app.game import Game
    from pygamine.devtools.smoke import run_briefly

    game = Game()
    frames = run_briefly(game)
    # The temp database has the default settings; a skipped splash would mean
    # this step no longer covers it.
    assert not game.skip_intro and game.splash is not None, "the splash was skipped"
    print(f"  splash + {frames} main-loop frames via the real run(): OK")


def main() -> None:
    from pygamine import Database

    # Every Database this run opens goes to a temp folder (what tests/conftest.py does).
    temp = tempfile.TemporaryDirectory()
    Database.__init__.__defaults__ = (temp.name,)
    print("Validating config/*.yaml...")
    check_config_yaml()
    print("Booting Game() and rendering every panel...")
    boot_game()
    print("Running the real run() -- splash and main loop -- briefly...")
    run_game_briefly()
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
