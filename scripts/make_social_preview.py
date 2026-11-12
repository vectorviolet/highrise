"""Builds the GitHub social preview image: docs/design/social-preview.png (1280x640, GitHub's 2:1).

The banner (docs/design/banner.png, 3:1) is scaled to 1280 px wide and centered on a taller canvas
whose background is the banner's own left-edge sky gradient, so nothing is cropped. GitHub has no
API for the image: upload it by hand in Settings > Social preview.

    uv run --group dev python scripts/make_social_preview.py
"""

from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BANNER = ROOT / "docs" / "design" / "banner.png"
OUT = ROOT / "docs" / "design" / "social-preview.png"
SIZE = (1280, 640)


def extend_vertically(img: Image.Image, height: int) -> Image.Image:
    """Center `img` on a taller canvas filled with its own left-edge vertical sky gradient."""
    w, h = img.size
    off = (height - h) // 2
    column = img.crop((0, 0, 4, h)).resize((1, h), Image.BOX)
    profile = Image.new("RGB", (1, height))
    profile.paste(column.crop((0, 0, 1, 1)).resize((1, off), Image.NEAREST), (0, 0))
    profile.paste(column, (0, off))
    below = height - off - h
    profile.paste(
        column.crop((0, h - 1, 1, h)).resize((1, below), Image.NEAREST), (0, off + h)
    )
    canvas = profile.resize((w, height), Image.NEAREST)
    canvas.paste(img, (0, off))
    # Blur only the seams where the picture meets the plain gradient.
    blurred = canvas.filter(ImageFilter.GaussianBlur(5))
    mask = Image.new("L", canvas.size, 0)
    for y in (off, off + h):
        mask.paste(255, (0, max(0, y - 6), w, min(height, y + 6)))
    return Image.composite(blurred, canvas, mask)


def main() -> None:
    width, height = SIZE
    banner = Image.open(BANNER).convert("RGB")
    scaled = banner.resize(
        (width, round(banner.height * width / banner.width)), Image.LANCZOS
    )
    extend_vertically(scaled, height).save(OUT, optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
