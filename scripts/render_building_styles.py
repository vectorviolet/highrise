"""Render the building ladder comparison images from config/buildings.yaml.

Composes buildings from the raw Kenney "Hexagon Buildings" pieces and writes, per age, a sheet
with today's six sprites, every ladder in the recipe file, and a door-left / door-right row.
Dev tool for docs/devlog/2026-11-11-building-recipes.md; the game does not use it.

    uv run --group dev python scripts/render_building_styles.py [--pack DIR] [--out DIR]
"""

import argparse
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PACK = (
    Path.home() / "Desktop/asset-library/kenney/hexagon-buildings/extracted/Tiles"
)
BG = (90, 120, 150, 255)
TODAY_LEVELS = 6
SCALE = 2
PER_ROW = 7  # levels per row before a ladder wraps
MAX_WIDTH = 1280
SIDE_DEMO = ("L1", [2, 5, 8])  # ladder and levels shown in both door sides
LABEL_W, CELL_W, PAD = 90, 150, 12


def load_recipes(path: Path) -> dict:
    with open(path, encoding="utf-8") as file:
        return yaml.safe_load(file)


def piece(pack: Path, name: str) -> Image.Image:
    return Image.open(pack / f"{name}.png").convert("RGBA")


def kind_piece(recipes: dict, kind: str, side: str) -> str:
    entry = recipes["floor_kinds"][kind]
    return entry if isinstance(entry, str) else entry[side]


def compose(
    recipes: dict, ladder: str, age: str, level: int, pack: Path, side: str = "left"
) -> Image.Image:
    """Stack a level's floors and roof into one sprite, its foot at the bottom edge."""
    recipe = recipes["ladders"][ladder][level - 1]
    prefixes = recipes["ages"][age]
    width, floor_height = recipes["pack_piece_size"]
    step, roof_base = recipes["floor_step"], recipes["roof_base"]
    floors = [
        piece(pack, prefixes["floor"] + kind_piece(recipes, kind, side))
        for kind in recipe["floors"]
    ]
    roof = piece(pack, prefixes["roof"] + "Roof" + recipe["roof"])
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


def today_sprite(age: str, level: int) -> Image.Image:
    return Image.open(ROOT / f"assets/images/buildings/{age}/level{level}.png").convert(
        "RGBA"
    )


def draw_row(
    sheet_rows: list[tuple[str, list[tuple[str, Image.Image]]]],
) -> Image.Image:
    """Lay out rows of (label, sprite) cells, wrapping each row after PER_ROW cells."""
    lines: list[tuple[str, list[tuple[str, Image.Image]]]] = []
    for title, cells in sheet_rows:
        for start in range(0, len(cells), PER_ROW):
            lines.append((title if start == 0 else "", cells[start : start + PER_ROW]))
    heights = [
        max(s.height for _, s in cells) * SCALE + 2 * PAD + 20 for _, cells in lines
    ]
    sheet = Image.new("RGBA", (LABEL_W + CELL_W * PER_ROW, sum(heights)), BG)
    draw = ImageDraw.Draw(sheet)
    y = 0
    for (title, cells), height in zip(lines, heights):
        draw.text((8, y + height // 2 - 10), title, font=font(18), fill="white")
        for col, (label, sprite) in enumerate(cells):
            big = sprite.resize(
                (sprite.width * SCALE, sprite.height * SCALE), Image.NEAREST
            )
            x = LABEL_W + col * CELL_W + (CELL_W - big.width) // 2
            sheet.alpha_composite(big, (x, y + height - 20 - PAD - big.height))
            draw.text(
                (x + big.width // 2 - 10, y + height - 22),
                label,
                font=font(14),
                fill="white",
            )
        y += height
    return sheet


def age_sheet(recipes: dict, age: str, pack: Path) -> Image.Image:
    rows = [
        (
            "today",
            [(str(n), today_sprite(age, n)) for n in range(1, TODAY_LEVELS + 1)],
        )
    ]
    for ladder, levels in recipes["ladders"].items():
        cells = [
            (str(n), compose(recipes, ladder, age, n, pack))
            for n in range(1, len(levels) + 1)
        ]
        rows.append((f"{ladder} ({len(levels)})", cells))
    ladder, picks = SIDE_DEMO
    demo = []
    for level in picks:
        for side in ("left", "right"):
            demo.append(
                (
                    f"{level}{side[0].upper()}",
                    compose(recipes, ladder, age, level, pack, side),
                )
            )
    rows.append(("door side", demo))
    return draw_row(rows)


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
    parser.add_argument("--ages", nargs="+", default=["wood", "rock", "stone"])
    args = parser.parse_args()
    recipes = load_recipes(args.recipes)
    for age in args.ages:
        save(
            age_sheet(recipes, age, args.pack), args.out / f"building-ladders-{age}.png"
        )


if __name__ == "__main__":
    main()
