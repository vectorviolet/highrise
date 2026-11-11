"""The cash display's look: a dark UI Pack plate, a gold coin and white text, in the Kenney UI
Pack style of the HUD buttons. The layout (position, size, alignment with the buttons) is in
config/panels.yaml; this module only paints the plate and the coin and colors the text. The owner
picked this look from three candidates (devlog 2026-11-10).
"""

from functools import lru_cache

import pygame

from pygamine import AssetManager, StateObject, TextObject, load_image

# Border of the button images that stays pixel-perfect when the plate is stretched.
NINE_SLICE = 20

COIN_GOLD = (255, 196, 0)
COIN_RIM = (176, 112, 0)
COIN_SHINE = (255, 232, 140)
COIN_GLYPH = (120, 72, 0)
# The coin is drawn this many times larger and scaled down, for smooth edges.
COIN_SUPERSAMPLE = 4


PLATE_ASSET = "grey_button"  # the HUD buttons' own plate family
PLATE_TINT = (70, 78, 104)  # multiplied onto the plate: a dark slate
TEXT_COLOR = (255, 255, 255)


@lru_cache(maxsize=None)
def _glyph_font(path: str, size: int) -> pygame.font.Font:
    return pygame.font.Font(path, size)


def draw_coin(size: int, glyph_font_path: str) -> pygame.Surface:
    """A gold coin with a dollar sign, `size` pixels wide, on a transparent surface."""
    big = size * COIN_SUPERSAMPLE
    coin = pygame.Surface((big, big), pygame.SRCALPHA)
    center = big // 2
    pygame.draw.circle(coin, COIN_RIM, (center, center), center)
    pygame.draw.circle(coin, COIN_GOLD, (center, center), round(center * 0.84))
    pygame.draw.circle(
        coin,
        COIN_SHINE,
        (center, center),
        round(center * 0.84),
        width=max(2, big // 24),
    )
    font = _glyph_font(glyph_font_path, round(big * 0.68))
    glyph = font.render("$", True, COIN_GLYPH)
    coin.blit(glyph, glyph.get_rect(center=(center, center)))
    return pygame.transform.smoothscale(coin, (size, size))


def apply_cash_display(
    plate: StateObject,
    icon: StateObject,
    text: TextObject,
    assets: AssetManager,
    coin_font_path: str,
) -> None:
    """Paints the plate and the coin and colors the text. The widgets keep the size and
    position the panel loader gave them, so the UI scale already applies."""
    image = load_image(
        assets.image_path(PLATE_ASSET), plate.rect.size, NINE_SLICE
    ).copy()
    image.fill(PLATE_TINT, special_flags=pygame.BLEND_RGB_MULT)
    plate.add_surface(None, image)
    plate.set_state(None)
    icon.add_surface(None, draw_coin(icon.rect.height, coin_font_path))
    icon.set_state(None)
    text.set_color(TEXT_COLOR)
