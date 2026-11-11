"""Render the building sprites the game composes, as sheets for the devlog.

Uses the game's own code (src/gameplay/buildings/sprites.py) and the recipes in
config/buildings.yaml, so a sheet shows exactly what the game draws. One sheet per age: every
level with the door on the left, then a few levels with the door on each side.

    uv run --group dev python scripts/render_building_styles.py [--out DIR] [--ages wood rock]
    uv run --group dev python scripts/render_building_styles.py --boosters   # booster candidates

`--boosters` renders the booster ladders instead (five levels per age): the candidates below
side by side, and the one in config/buildings.yaml, which is the game's.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.chdir(ROOT)  # the game's asset and config paths are relative to the project root
sys.path[:0] = [
    str(ROOT / "src"),
    str(ROOT / "src" / "pygamine"),
]  # as __main__.py does

import pygame  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from gameplay.buildings import sprites  # noqa: E402

BG = (90, 120, 150, 255)
SCALE = 2
PER_ROW = 7  # levels per row before a ladder wraps
MAX_WIDTH = 1280
SIDE_DEMO_LEVELS = (2, 5, 8)
LABEL_W, CELL_W, PAD = 90, 150, 12


def to_pil(surface: pygame.Surface) -> Image.Image:
    size = surface.get_size()
    return Image.frombytes("RGBA", size, pygame.image.tobytes(surface, "RGBA"))


def font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def sheet(rows: list[tuple[str, list[tuple[str, Image.Image]]]]) -> Image.Image:
    """Lay out rows of (label, sprite) cells, wrapping each row after PER_ROW cells."""
    lines = []
    for title, cells in rows:
        for start in range(0, len(cells), PER_ROW):
            lines.append((title if start == 0 else "", cells[start : start + PER_ROW]))
    heights = [
        max(s.height for _, s in cells) * SCALE + 2 * PAD + 20 for _, cells in lines
    ]
    image = Image.new("RGBA", (LABEL_W + CELL_W * PER_ROW, sum(heights)), BG)
    draw = ImageDraw.Draw(image)
    y = 0
    for (title, cells), height in zip(lines, heights):
        draw.text((8, y + height // 2 - 10), title, font=font(18), fill="white")
        for col, (label, sprite) in enumerate(cells):
            big = sprite.resize(
                (sprite.width * SCALE, sprite.height * SCALE), Image.NEAREST
            )
            x = LABEL_W + col * CELL_W + (CELL_W - big.width) // 2
            image.alpha_composite(big, (x, y + height - 20 - PAD - big.height))
            draw.text(
                (x + big.width // 2 - 10, y + height - 22),
                label,
                font=font(14),
                fill="white",
            )
        y += height
    return image


def age_sheet(age: str) -> Image.Image:
    levels = range(1, sprites.level_count() + 1)
    rows = [
        ("levels", [(str(n), to_pil(sprites.compose(age, n, "left"))) for n in levels])
    ]
    demo = [
        (f"{level}{side[0].upper()}", to_pil(sprites.compose(age, level, side)))
        for level in SIDE_DEMO_LEVELS
        for side in sprites.DOOR_SIDES
    ]
    rows.append(("door side", demo))
    return sheet(rows)


def _ring(count: int, roof: str) -> dict:
    return {"floors": ["ring"] * count, "roof": roof}


# Booster ladder candidates (the hex ring with a red roof, five levels each), for the owner to
# pick from. A is the one in config/buildings.yaml.
BOOSTER_CANDIDATES = {
    "A": [
        _ring(1, "Short"),
        _ring(2, "Short"),
        _ring(3, "Short"),
        _ring(3, "Straight"),
        _ring(3, "Pointy"),
    ],
    "B": [
        _ring(1, "Short"),
        _ring(1, "Straight"),
        _ring(2, "Straight"),
        _ring(2, "Tall"),
        _ring(3, "Pointy"),
    ],
    "C": [
        _ring(1, "Short"),
        _ring(1, "Tall"),
        _ring(1, "Pointy"),
        _ring(2, "Pointy"),
        _ring(3, "Pointy"),
    ],
}


def booster_sheet(ages: list[str], names: list[str]) -> Image.Image:
    """One row per (candidate, age); the recipes' booster levels are swapped for each
    candidate in turn (and the sprite caches cleared), then restored."""
    boosters = sprites.recipes()["boosters"]
    original = boosters["levels"]
    rows = []
    try:
        for name in names:
            boosters["levels"] = BOOSTER_CANDIDATES[name]
            sprites.compose.cache_clear()
            for age in ages:
                cells = [
                    (str(n), to_pil(sprites.compose(age, n, "left", True)))
                    for n in range(1, sprites.level_count(True) + 1)
                ]
                rows.append((f"{name} {age}", cells))
    finally:
        boosters["levels"] = original
        sprites.compose.cache_clear()
    return sheet(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs/devlog/img")
    parser.add_argument("--ages", nargs="+", default=["wood", "rock", "stone"])
    parser.add_argument(
        "--boosters", action="store_true", help="render booster ladders"
    )
    args = parser.parse_args()
    pygame.display.set_mode(
        (1, 1)
    )  # load_image converts surfaces, which needs a display
    args.out.mkdir(parents=True, exist_ok=True)
    if args.boosters:
        path = args.out / "booster-candidates.png"
        booster_sheet(args.ages, list(BOOSTER_CANDIDATES)).save(path, optimize=True)
        print("wrote", path)
        return
    for age in args.ages:
        image = age_sheet(age)
        if image.width > MAX_WIDTH:
            image = image.resize(
                (MAX_WIDTH, round(image.height * MAX_WIDTH / image.width)),
                Image.LANCZOS,
            )
        path = args.out / f"building-ladders-{age}.png"
        image.save(path, optimize=True)
        print("wrote", path)


if __name__ == "__main__":
    main()
