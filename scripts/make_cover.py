"""Build the cover and the itch.io banner from the text-free art in docs/design/art/.

Run from the repo root:

    uv run --group dev python scripts/make_cover.py

Writes docs/design/cover.png (1402x1122, the art's native size) and
docs/store/cover-itchio.png (630x500), docs/design/banner.png (1920x600) and
docs/store/banner-itchio.png (960x300). The title and the tagline are drawn here, so change TITLE,
TAGLINE or a style below and rerun to restyle them. The art files are never modified.

Needs Pillow (the `dev` group has it).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "docs" / "design" / "art"
FONTS = ROOT / "assets" / "fonts"

TITLE = "Highrise"
TAGLINE = "MERGE. BUILD. RISE."

NAVY = (0x14, 0x1D, 0x3B)
WHITE = (255, 255, 255)
YELLOW = (0xFF, 0xE2, 0x78)

COVER_SIZE = (1402, 1122)
COVER_STORE_SIZE = (630, 500)
BANNER_SIZE = (1920, 600)
BANNER_STORE_SIZE = (960, 300)


@dataclass(frozen=True)
class TextStyle:
    """How one line of text is drawn."""

    font: str
    fill: tuple[int, int, int]
    outline: tuple[int, int, int]
    shadow: bool


# The one shared definition: the cover and the banner use the same fonts, colors and outline;
# only the sizes and positions below differ per image.
TITLE_STYLE = TextStyle("TitilliumWeb-Black.ttf", WHITE, NAVY, shadow=True)
TAGLINE_STYLE = TextStyle("TitilliumWeb-Bold.ttf", YELLOW, NAVY, shadow=False)

SHADOW_OFFSET = (0, 8)
SHADOW_BLUR = 7
SHADOW_ALPHA = 150


def draw_text(
    image: Image.Image,
    text: str,
    style: TextStyle,
    size: int,
    center: tuple[int, int] | None = None,
    left: int | None = None,
    middle_y: int | None = None,
) -> tuple[int, int, int, int]:
    """Draw `text` onto `image` in `style`; return its bounding box.

    Place it with `center` (x, y of the middle), or with `left` (x of the left edge) plus
    `middle_y`. The outline is a tenth of the font size.
    """
    font = ImageFont.truetype(str(FONTS / style.font), size)
    stroke = max(2, round(size / 10))
    draw = ImageDraw.Draw(image)
    if center is not None:
        anchor, position = "mm", center
    else:
        assert left is not None and middle_y is not None
        anchor, position = "lm", (left, middle_y)
    box = draw.textbbox(position, text, font=font, anchor=anchor, stroke_width=stroke)
    if style.shadow:
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        shadow_position = (
            position[0] + SHADOW_OFFSET[0],
            position[1] + SHADOW_OFFSET[1],
        )
        ImageDraw.Draw(layer).text(
            shadow_position,
            text,
            font=font,
            anchor=anchor,
            fill=(0, 0, 0, SHADOW_ALPHA),
            stroke_width=stroke,
            stroke_fill=(0, 0, 0, SHADOW_ALPHA),
        )
        layer = layer.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
        image.alpha_composite(layer)
        draw = ImageDraw.Draw(image)
    draw.text(
        position,
        text,
        font=font,
        anchor=anchor,
        fill=style.fill,
        stroke_width=stroke,
        stroke_fill=style.outline,
    )
    return box


def make_cover() -> Image.Image:
    """The merge art at its native size with the title, and the tagline if it fits."""
    image = Image.open(ART / "cover-merge-island.png").convert("RGBA")
    assert image.size == COVER_SIZE, image.size
    middle_x = COVER_SIZE[0] // 2
    draw_text(
        image, TITLE, TITLE_STYLE, 210, center=(middle_x, round(COVER_SIZE[1] * 0.17))
    )
    # The tower's antenna reaches up to y~290 at x~1055; the tagline sits left of center, under
    # the title, and stays clear of it.
    draw_text(image, TAGLINE, TAGLINE_STYLE, 62, center=(middle_x - 130, 348))
    return image


def make_banner() -> Image.Image:
    """The wide art at 1920 px, center-cropped to 1920x600, title and tagline on the left."""
    image = Image.open(ART / "banner-wide.png").convert("RGBA")
    width = BANNER_SIZE[0]
    image = image.resize(
        (width, round(image.height * width / image.width)), Image.LANCZOS
    )
    top = (image.height - BANNER_SIZE[1]) // 2
    image = image.crop((0, top, width, top + BANNER_SIZE[1]))
    draw_text(image, TITLE, TITLE_STYLE, 190, left=150, middle_y=235)
    draw_text(image, TAGLINE, TAGLINE_STYLE, 52, left=155, middle_y=395)
    return image


def save_png(image: Image.Image, path: Path) -> None:
    """Save an optimized, lossless RGB PNG and print its size."""
    image.convert("RGB").save(path, optimize=True)
    size_kb = path.stat().st_size // 1024
    print(f"{path.relative_to(ROOT)}  {image.width}x{image.height}  {size_kb} KB")


def main() -> None:
    cover = make_cover()
    save_png(cover, ROOT / "docs" / "design" / "cover.png")
    save_png(
        cover.resize(COVER_STORE_SIZE, Image.LANCZOS),
        ROOT / "docs" / "store" / "cover-itchio.png",
    )
    banner = make_banner()
    save_png(banner, ROOT / "docs" / "design" / "banner.png")
    save_png(
        banner.resize(BANNER_STORE_SIZE, Image.LANCZOS),
        ROOT / "docs" / "store" / "banner-itchio.png",
    )


if __name__ == "__main__":
    main()
