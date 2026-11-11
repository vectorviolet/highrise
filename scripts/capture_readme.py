"""Capture the README media (and the devlog's screenshot candidates) from the current game.

Run from the repo root:

    uv run --group dev python scripts/capture_readme.py

Writes docs/preview.gif and docs/screenshots/01_main_menu.png, 02_build_mode.png and
03_inspection.png (the README's), and the extra candidates into --candidates (default
docs/devlog/img/screenshots-2026-11/). Needs Pillow (the `dev` group has it).

The game runs headless (dummy SDL drivers) and is driven by calling its own methods, the way
the key presses and clicks would. Nothing here touches a real save: every Database opens in a
temporary folder (what scripts/smoke_test.py and tests/conftest.py do). The random numbers are
seeded, the clock is a fake one that advances 1000 / FPS ms per frame, and the mouse is pinned,
so two runs write the same pictures.
"""

import argparse
import os
import random
import sys
import tempfile
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "pygamine"))
os.chdir(ROOT)  # the game reads config/ and assets/ relative to the repo root

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

from gameplay.buildings.building import Building  # noqa: E402
from pygamine import StateObject  # noqa: E402
from ui.ui_scale import DEFAULT_UI_SCALE  # noqa: E402

SEED = 44
# The canvas every picture is taken at (the game's authored size, 16:9).
RESOLUTION = (1920, 1080)
FPS = 25
FRAME_MS = 1000 // FPS
# README images are at most this wide.
MAX_WIDTH = 1280
# The GIF's width and its palette's sample frames (see save_gif).
GIF_WIDTH = 1000
# The GIF shows this part of the canvas (left, top, right, bottom): the board and the toolbar.
GIF_CROP = (200, 170, 1720, 1080)
PALETTE_SAMPLES = 12
# Where the mouse rests when it should touch nothing (over the bare sky).
IDLE_MOUSE = (60, 60)
# A GIF frame is taken every this many game frames.
CLIP_STRIDE = 2
# Frames to let an effect (a floating text, an opening panel) settle before a shot.
SETTLE_FRAMES = 6


class Studio:
    """A booted Game with a pinned mouse and a fake clock, and the helpers to drive it."""

    def __init__(self, language: str = "en") -> None:
        from app.game import Game

        self.now_ms = 10_000
        self.frame = 0
        pygame.time.get_ticks = lambda: self.now_ms
        self.game = game = Game()
        # The dummy display is 1024x768 and would make a 4:3 canvas: ask for the authored size.
        game.set_resolution(RESOLUTION)
        game.set_windowed()
        game.init_database()
        game._apply_settings(game.load_settings())
        game.load_data()
        game.tile_selector.tilemap = game.tilemap
        game.add_objects()
        game._reset_session_ui()
        game.mouse.update = lambda: None  # the real mouse has no say in a headless run
        game.mouse.set_cursor_image(self._cursor())
        game.watch_language()
        if language != "en":
            game.change_language(language)
        self.mouse(IDLE_MOUSE)

    def _cursor(self) -> "StateObject":
        game = self.game
        return StateObject(
            pos=(0, 0),
            size=game.cursor_size,
            image_path=game.assets.image_path("cursor"),
        )

    def close(self) -> None:
        self.game.unwatch_language()

    # -- driving ---------------------------------------------------------------------

    def mouse(self, position: tuple[float, float]) -> None:
        self.game.mouse.position = position
        self.game.mouse.cursor.rect.set_position(position)

    def step(self, frames: int = 1, clip: "list[Image.Image] | None" = None) -> None:
        """Advances `frames` frames; with a `clip`, every CLIP_STRIDE-th frame is added to it."""
        for _ in range(frames):
            self.now_ms += FRAME_MS
            self.game.update()
            self.frame += 1
            if clip is not None and self.frame % CLIP_STRIDE == 0:
                clip.append(self.shot())

    def move_mouse(self, target, frames: int = 8, clip=None) -> None:
        """The pinned mouse glides to `target` over `frames` frames."""
        start = pygame.Vector2(self.game.mouse.position)
        end = pygame.Vector2(target)
        for i in range(1, frames + 1):
            self.mouse(start.lerp(end, i / frames))
            self.step(1, clip)

    def clear_clouds(self) -> None:
        """Lets the clouds a panel change sweeps over the screen drift off, as they do in play."""
        for _ in range(600):
            if not self.game.cloud_animation:
                return
            self.step(1)
        raise RuntimeError("the clouds never left")

    def shot(self) -> Image.Image:
        """The current frame, drawn the way the main loop does and copied off the window."""
        game = self.game
        game.draw()
        game.draw_mouse()
        return Image.frombytes(
            "RGB", game.window.get_size(), pygame.image.tobytes(game.window, "RGB")
        )

    def settle(self, frames: int = SETTLE_FRAMES) -> Image.Image:
        self.step(frames)
        return self.shot()

    def open(self, panel: str) -> None:
        self.game.open_panel(panel)
        self.clear_clouds()

    def wait_idle(self, limit: int = 200, clip=None) -> None:
        """Frames until nothing slides and no merge is pending."""
        for _ in range(limit):
            if not self.game.buildings.is_busy():
                return
            self.step(1, clip)
        raise RuntimeError("the buildings never settled")

    def slide(self, direction: str, clip=None) -> None:
        self.game.move_buildings(direction)
        self.wait_idle(clip=clip)
        self.step(2, clip)

    # -- staging ---------------------------------------------------------------------

    def new_game(self, money: int, size: int = 2, age: int = 0) -> None:
        """A fresh board `size` x `size` (grown by the game's own expand) of `age`."""
        game = self.game
        game.new_game()
        game.player.money = 10**9  # expanding is paid for; the real amount is set below
        while game.tilemap.row_count < size:
            game.expand()
        game.set_age(age)
        game.player.money = money
        game.odometer.snap(f"{money:,}$")
        game.floating_texts.clear()
        game.sell_effect.clear()
        self.mouse(IDLE_MOUSE)
        self.clear_clouds()

    def place(
        self, level: int, row: int, col: int, door: str, booster: bool = False
    ) -> Building:
        return self.game.add_building(level, row, col, door, booster=booster)

    def center_of(self, name: str) -> tuple[int, int]:
        return self.game.panel_manager["game"][name].rect.center

    def inspect(self, building) -> None:
        """Selection mode on, the mouse over `building`, its info panel open."""
        game = self.game
        panel = game.panel_manager["game"]
        game._toggle_selection_mode(panel["selection_mode_button"])
        # The tile under the building: its sprite stands up from the tile's middle.
        self.mouse((building.rect.centerx, building.rect.bottom - 12))
        self.step(2)
        game.tile_selector.update_selection()
        game._pick_tile()
        self.step(SETTLE_FRAMES)

    def close_inspection(self) -> None:
        game = self.game
        game.info_panel.close()
        panel = game.panel_manager["game"]
        game._toggle_selection_mode(panel["selection_mode_button"])
        self.mouse(IDLE_MOUSE)
        self.step(2)


def resized(image: Image.Image, width: int) -> Image.Image:
    if image.width <= width:
        return image
    return image.resize(
        (width, round(image.height * width / image.width)), Image.Resampling.LANCZOS
    )


def save_png(image: Image.Image, path: Path, width: int = MAX_WIDTH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    resized(image, width).save(path, optimize=True)
    print(f"Captured {path}")


def palette_indices(frame_count: int) -> list[int]:
    """Up to PALETTE_SAMPLES frame indices spread evenly over the clip, first and last included."""
    k = min(PALETTE_SAMPLES, frame_count)
    if k == 1:
        return [0]
    return sorted({round(i * (frame_count - 1) / (k - 1)) for i in range(k)})


def save_gif(frames: list[Image.Image], path: Path, width: int = GIF_WIDTH) -> None:
    """One 256-color palette for the whole clip, built from frames spread over it, so colors
    that only appear later (a booster's roof, the coins) are in it too."""
    frames = [resized(f.crop(GIF_CROP), width) for f in frames]
    samples = [frames[i] for i in palette_indices(len(frames))]
    w, h = samples[0].size
    sheet = Image.new("RGB", (w, h * len(samples)))
    for i, sample in enumerate(samples):
        sheet.paste(sample, (0, i * h))
    palette = sheet.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    path.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(
        path,
        save_all=True,
        append_images=indexed[1:],
        duration=FRAME_MS * CLIP_STRIDE,
        loop=0,
        optimize=True,
        disposal=1,
    )
    print(f"Captured {path} ({path.stat().st_size / 1e6:.2f} MB, {len(frames)} frames)")


# -- the scenes ----------------------------------------------------------------------

# Door sides for the staged buildings, so no two neighbors look the same by accident.
L, R = "left", "right"


def main_menu(studio: Studio) -> Image.Image:
    """The menu with the mouse on PLAY, the way the README's first picture always showed it."""
    studio.open("menu")
    studio.move_mouse(studio.game.panel_manager["menu"]["play_button"].rect.center, 4)
    return studio.settle(6)


def mid_game(studio: Studio) -> Building:
    """A 5x5 wood board with buildings of several levels and a booster; returns the booster."""
    studio.new_game(money=2340, size=5)
    place = studio.place
    for level, row, col, door in (
        (1, 1, 2, L),
        (2, 1, 4, R),
        (3, 2, 1, R),
        (1, 2, 3, L),
        (4, 2, 5, R),
        (2, 3, 2, L),
        (5, 3, 4, R),
        (1, 4, 1, L),
        (3, 4, 3, R),
        (2, 5, 2, L),
        (1, 5, 5, L),
    ):
        place(level, row, col, door)
    booster = place(2, 3, 3, L, booster=True)
    studio.game.tasks.unlock_boost()
    studio.game.update_button_texts()
    studio.step(4)
    return booster


def build_mode(studio: Studio) -> Image.Image:
    """The board with the mouse over the booster: its covered tiles light up."""
    booster = mid_game(studio)
    studio.move_mouse(booster.rect.center, 4)
    studio.step(50)  # the payouts' texts float up
    return studio.settle()


def inspection(studio: Studio) -> Image.Image:
    mid_game(studio)
    target = next(b for b in studio.game.buildings if not b.is_booster and b.level == 5)
    studio.inspect(target)
    return studio.shot()


def merge_in_progress(studio: Studio) -> Image.Image:
    """Two level 2 buildings halfway through their slide into one level 3."""
    studio.new_game(money=1200, size=4)
    studio.place(2, 2, 1, L)
    studio.place(2, 2, 4, R)
    studio.place(1, 4, 2, L)
    studio.place(3, 1, 3, R)
    studio.step(4)
    studio.game.move_buildings("left")
    studio.step(2)
    assert studio.game.buildings.is_moving(), "the slide ended before the shot"
    return studio.shot()


def sell_option(studio: Studio) -> Image.Image:
    """A building's info panel (level, income, sell price) over a bigger board."""
    mid_game(studio)
    target = next(b for b in studio.game.buildings if not b.is_booster and b.level == 3)
    studio.inspect(target)
    return studio.shot()


def booster_inspection(studio: Studio) -> Image.Image:
    """A booster's info panel: its multiplier, and the tiles it covers lit up."""
    booster = mid_game(studio)
    studio.inspect(booster)
    return studio.shot()


def expand_before_after(studio: Studio) -> tuple[Image.Image, Image.Image]:
    studio.new_game(money=2000, size=3)
    for level, row, col, door in (
        (1, 1, 1, L),
        (2, 2, 3, R),
        (3, 3, 2, L),
        (1, 3, 3, R),
    ):
        studio.place(level, row, col, door)
    studio.step(4)
    before = studio.shot()
    studio.move_mouse(studio.center_of("expand_button"), 6)
    studio.game.expand()
    studio.step(60)  # the "-400$" text has flown off
    return before, studio.shot()


def later_age(studio: Studio) -> Image.Image:
    """The sand age (age 3) with buildings up to level 8."""
    studio.new_game(money=9800, size=5, age=2)
    for level, row, col, door in (
        (8, 3, 3, L),
        (6, 2, 2, R),
        (5, 4, 4, L),
        (4, 2, 4, R),
        (3, 4, 2, L),
        (7, 1, 3, R),
        (2, 5, 3, L),
        (1, 3, 5, R),
    ):
        studio.place(level, row, col, door)
    studio.place(3, 4, 3, R, booster=True)
    studio.step(30)
    return studio.settle()


def next_age_checklist(studio: Studio) -> Image.Image:
    """The mouse on NEXT AGE: the age's tasks as a checklist, one done and one not yet."""
    studio.new_game(money=1500, size=3)
    for level, row, col, door in (
        (3, 1, 2, L),
        (1, 2, 3, R),
        (2, 3, 1, L),
        (1, 3, 3, R),
    ):
        studio.place(level, row, col, door)
    studio.step(4)
    studio.move_mouse(studio.center_of("next_age_button"), 6)
    studio.step(8)
    return studio.shot()


def settings_turkish(studio: Studio) -> tuple[Image.Image, Image.Image]:
    """The Display page at UI scale 125% and the Game page, both in Turkish."""
    game = studio.game
    game.change_language("tr")
    game.set_ui_scale(125)
    studio.open("display_settings")
    display = studio.settle()
    studio.open("game_settings")
    game_page = studio.settle()
    game.set_ui_scale(DEFAULT_UI_SCALE)
    game.change_language("en")
    return display, game_page


def preview_gif(studio: Studio) -> list[Image.Image]:
    """A short loop: build, slide to merge, place a booster and watch the income come in."""
    clip: list[Image.Image] = []
    game = studio.game
    studio.new_game(money=1000, size=4)
    for level, row, col, door in (
        (1, 1, 1, L),
        (1, 1, 3, R),
        (2, 3, 2, R),
        (2, 4, 4, L),
        (3, 2, 4, L),
    ):
        studio.place(level, row, col, door)
    studio.step(10, clip)
    studio.move_mouse(studio.center_of("build_button"), 8, clip)
    game.create_building()
    studio.step(10, clip)
    game.create_building()
    studio.step(14, clip)
    studio.move_mouse(IDLE_MOUSE, 8, clip)
    for direction in ("left", "down", "left"):
        studio.slide(direction, clip)
        studio.step(8, clip)
    game.tasks.unlock_boost()
    game.update_button_texts()
    studio.move_mouse(studio.center_of("boost_button"), 8, clip)
    game.create_booster()
    studio.step(30, clip)
    studio.move_mouse(IDLE_MOUSE, 6, clip)
    studio.step(60, clip)
    return clip


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--docs", type=Path, default=ROOT / "docs")
    parser.add_argument(
        "--candidates",
        type=Path,
        default=ROOT / "docs" / "devlog" / "img" / "screenshots-2026-11",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Every Database this run opens goes to a temp folder, never the real databases/.
    from pygamine import Database, SaveStore

    temp = tempfile.TemporaryDirectory()
    Database.__init__.__defaults__ = (str(Path(temp.name) / "databases"),)
    SaveStore.__init__.__defaults__ = (str(Path(temp.name) / "saves"),)
    random.seed(SEED)
    studio = Studio()
    shots = args.docs / "screenshots"
    try:
        save_png(main_menu(studio), shots / "01_main_menu.png")
        save_png(build_mode(studio), shots / "02_build_mode.png")
        save_png(inspection(studio), shots / "03_inspection.png")
        save_gif(preview_gif(studio), args.docs / "preview.gif")
        extra = args.candidates
        save_png(merge_in_progress(studio), extra / "merge-in-progress.png")
        save_png(sell_option(studio), extra / "inspect-sell.png")
        save_png(booster_inspection(studio), extra / "inspect-booster.png")
        before, after = expand_before_after(studio)
        save_png(before, extra / "expand-before.png")
        save_png(after, extra / "expand-after.png")
        save_png(later_age(studio), extra / "later-age-sand.png")
        save_png(next_age_checklist(studio), extra / "next-age-checklist.png")
        display, game_page = settings_turkish(studio)
        save_png(display, extra / "settings-display-tr-125.png")
        save_png(game_page, extra / "settings-game-tr.png")
    finally:
        studio.close()
        temp.cleanup()


if __name__ == "__main__":
    main()
