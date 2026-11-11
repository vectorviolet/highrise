"""Render the building style comparison images from config/buildings.yaml.

Composes buildings from the raw Kenney "Hexagon Buildings" pieces and writes, per age, a sheet
of today's sprite next to recipe styles A and B for levels 1-6, plus one mixed board per style.
Dev tool for docs/devlog/2026-11-11-building-recipes.md; the game does not use it.

    uv run --group dev python scripts/render_building_styles.py [--pack DIR] [--out DIR]
"""

import argparse
import random
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PACK = (
    Path.home() / "Desktop/asset-library/kenney/hexagon-buildings/extracted/Tiles"
)
BG = (90, 120, 150, 255)
LEVELS = range(1, 7)
BOARD_SEED = 7
SHEET_SCALE = 2
BOARD_SCALE = 2
MAX_WIDTH = 1280
TILE_STEP = (66, 33)  # isometric step between neighboring tiles of tile.png
# The game draws a building 50 px wide at tile.x + 43 with its foot at tile.y + 52.
GAME_SPRITE_WIDTH, GAME_SPRITE_X, GAME_FOOT_Y = 50, 43, 52
SPRITE_WIDTH = 65
BOARD_CELLS = [  # (age, level) per row of the 4x4 board
    [("wood", 1), ("rock", 3), ("sand", 2), ("stone", 5)],
    [("rock", 2), ("stone", 1), ("wood", 4), ("sand", 6)],
    [("sand", 3), ("wood", 6), ("stone", 2), ("rock", 5)],
    [("stone", 4), ("sand", 1), ("rock", 6), ("wood", 3)],
]


def load_recipes(path: Path) -> dict:
    with open(path, encoding="utf-8") as file:
        return yaml.safe_load(file)


def piece(pack: Path, name: str) -> Image.Image:
    return Image.open(pack / f"{name}.png").convert("RGBA")


def pick(options: list[str], rng: random.Random | None) -> str:
    """The default (first) variant, or a seeded random one when `rng` is given."""
    return options[0] if rng is None else rng.choice(options)


def compose(
    recipes: dict,
    style: str,
    age: str,
    level: int,
    pack: Path,
    rng: random.Random | None = None,
) -> Image.Image:
    """Stack the recipe's floors and roof into one sprite, its foot at the bottom edge."""
    recipe = recipes["styles"][style][level]
    prefixes = recipes["ages"][age]
    width, floor_height = recipes["pack_piece_size"]
    step, roof_base = recipes["floor_step"], recipes["roof_base"]
    floors = [
        piece(pack, prefixes["floor"] + pick(slot, rng)) for slot in recipe["floors"]
    ]
    roof = piece(pack, prefixes["roof"] + "Roof" + pick(recipe["roof"], rng))
    # y of each piece's top, 0 = the ground floor's top, negative = higher
    floor_tops = [-i * step for i in range(len(floors))]
    roof_top = floor_tops[-1] + roof_base - roof.height
    top = min(roof_top, floor_tops[-1])
    sprite = Image.new("RGBA", (width, floor_height - top), (0, 0, 0, 0))
    for image, y in [*zip(floors, floor_tops), (roof, roof_top)]:
        sprite.alpha_composite(image, (0, y - top))
    return sprite


def font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def age_sheet(recipes: dict, age: str, pack: Path) -> Image.Image:
    """Rows: today, A, B. Columns: levels 1-6. Default variants only."""
    cell_w, cell_h = (SPRITE_WIDTH + 5) * SHEET_SCALE, 170 * SHEET_SCALE
    label_w, head = 70, 40
    sheet = Image.new("RGBA", (label_w + cell_w * len(LEVELS), head + cell_h * 3), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), age.upper(), font=font(22), fill="white")
    for col, level in enumerate(LEVELS):
        draw.text(
            (label_w + col * cell_w + 8, 12),
            f"level {level}",
            font=font(14),
            fill="white",
        )
    for row, name in enumerate(["today", "A", "B"]):
        draw.text(
            (8, head + row * cell_h + cell_h // 2), name, font=font(18), fill="white"
        )
        for col, level in enumerate(LEVELS):
            if name == "today":
                path = ROOT / f"assets/images/buildings/{age}/level{level}.png"
                sprite = Image.open(path).convert("RGBA")
            else:
                sprite = compose(recipes, name, age, level, pack)
            size = (sprite.width * SHEET_SCALE, sprite.height * SHEET_SCALE)
            sprite = sprite.resize(size, Image.NEAREST)
            x = label_w + col * cell_w + (cell_w - sprite.width) // 2
            sheet.alpha_composite(
                sprite, (x, head + (row + 1) * cell_h - sprite.height - 8)
            )
    return sheet


def board(recipes: dict, style: str, pack: Path) -> Image.Image:
    """A 4x4 isometric board on the game's tile.png, one seeded variant per building."""
    tile = Image.open(ROOT / "assets/images/tile.png").convert("RGBA")
    rng = random.Random(BOARD_SEED)
    size = len(BOARD_CELLS)
    ox, oy = (size - 1) * TILE_STEP[0], 90
    canvas = Image.new(
        "RGBA",
        (2 * ox + tile.width, oy + (2 * size - 2) * TILE_STEP[1] + tile.height),
        BG,
    )
    cells = sorted(
        ((r, c) for r in range(size) for c in range(size)),
        key=lambda rc: (sum(rc), rc[0]),
    )
    for r, c in cells:  # back to front
        x, y = ox + (c - r) * TILE_STEP[0], oy + (c + r) * TILE_STEP[1]
        canvas.alpha_composite(tile, (x, y))
        age, level = BOARD_CELLS[r][c]
        sprite = compose(recipes, style, age, level, pack, rng)
        scaled = (
            GAME_SPRITE_WIDTH,
            round(sprite.height * GAME_SPRITE_WIDTH / sprite.width),
        )
        sprite = sprite.resize(scaled, Image.LANCZOS)
        canvas.alpha_composite(
            sprite, (x + GAME_SPRITE_X, y + GAME_FOOT_Y - sprite.height)
        )
    return canvas.resize(
        (canvas.width * BOARD_SCALE, canvas.height * BOARD_SCALE), Image.NEAREST
    )


def save(image: Image.Image, path: Path) -> None:
    if image.width > MAX_WIDTH:
        image = image.resize(
            (MAX_WIDTH, round(image.height * MAX_WIDTH / image.width)), Image.LANCZOS
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)
    print("wrote", path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pack", type=Path, default=DEFAULT_PACK, help="pack Tiles folder"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "docs/devlog/img")
    parser.add_argument("--recipes", type=Path, default=ROOT / "config/buildings.yaml")
    args = parser.parse_args()
    recipes = load_recipes(args.recipes)
    for age in recipes["ages"]:
        save(
            age_sheet(recipes, age, args.pack), args.out / f"building-recipes-{age}.png"
        )
    for style in ("A", "B"):
        save(
            board(recipes, style, args.pack),
            args.out / f"building-recipes-board-{style}.png",
        )


if __name__ == "__main__":
    main()
