"""Generates the two page-header images (assets/images/gui/header/).

    uv run python scripts/gen_header_art.py <path to the extracted Kenney UI Pack>

Style a, plate.png: the UI Pack's blue depth-flat button, hue-shifted to purple, a
color no button uses.
Style b, banner.png: a ribbon with swallowtail ends and a gold edge, drawn here.

Both are nine-slice friendly (20 px borders, a flat middle), so the header stretches
to any width. The art is committed; rerun this only to change it.
"""

import colorsys
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

OUT = Path("assets/images/gui/header")
SS = 4  # supersampling factor for the banner


def recolor_plate(pack: Path) -> pygame.Surface:
    image = pygame.image.load(pack / "PNG/Blue/Default/button_rectangle_depth_flat.png")
    out = image.copy()
    target_hue = 0.76  # purple
    for x in range(image.get_width()):
        for y in range(image.get_height()):
            r, g, b, a = image.get_at((x, y))
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s > 0.15:  # leave the white and grey bevel as it is
                h, s, v = target_hue, s * 0.7, v * 0.85
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            out.set_at((x, y), (round(nr * 255), round(ng * 255), round(nb * 255), a))
    return out


def banner() -> pygame.Surface:
    w, h = 160 * SS, 70 * SS
    notch = 18 * SS
    big = pygame.Surface((w, h), pygame.SRCALPHA)
    body = [(0, 0), (w, 0), (w - notch, h // 2), (w, h), (0, h), (notch, h // 2)]
    pygame.draw.polygon(big, (39, 52, 82), body)  # dark slate
    inner = [
        (3 * SS, 4 * SS),
        (w - 3 * SS, 4 * SS),
        (w - notch - 1 * SS, h // 2),
        (w - 3 * SS, h - 4 * SS),
        (3 * SS, h - 4 * SS),
        (notch + 1 * SS, h // 2),
    ]
    pygame.draw.polygon(big, (58, 76, 118), inner)  # lighter face
    pygame.draw.line(
        big,
        (238, 196, 72),
        (notch + 4 * SS, 6 * SS),
        (w - notch - 4 * SS, 6 * SS),
        2 * SS,
    )
    pygame.draw.line(
        big,
        (238, 196, 72),
        (notch + 4 * SS, h - 7 * SS),
        (w - notch - 4 * SS, h - 7 * SS),
        2 * SS,
    )
    return pygame.transform.smoothscale(big, (160, 70))


def main() -> None:
    pack = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    pygame.image.save(recolor_plate(pack), str(OUT / "plate.png"))
    pygame.image.save(banner(), str(OUT / "banner.png"))


if __name__ == "__main__":
    main()
