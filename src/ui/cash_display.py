"""The cash display's look: the plate behind the amount, the coin and the text color.

Three candidates, all in the Kenney UI Pack style of the HUD buttons. The layout (position,
size, alignment with the buttons) is in config/panels.yaml; this module only paints the plate
and the coin and colors the text. `ui.cash_display` in config/settings.yaml picks the candidate
(a key of CASH_STYLES), so the owner's choice is a one-number change.
"""

from dataclasses import dataclass
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


@dataclass(frozen=True)
class CashStyle:
    name: str
    plate_asset: str  # image manifest key of the plate
    tint: tuple[int, int, int] | None  # multiplied onto the plate (darkens it)
    text_color: tuple[int, int, int]
    coin: bool


CASH_STYLES: dict[int, CashStyle] = {
    # 1: a dark UI Pack plate with a coin and light text.
    1: CashStyle(
        "dark plate, coin, light text",
        "grey_button",
        (70, 78, 104),
        (255, 255, 255),
        True,
    ),
    # 2: a plate like the buttons' own gloss, in yellow, with dark text.
    2: CashStyle(
        "button-style yellow plate", "yellow_button", None, (96, 58, 0), False
    ),
    # 3: the same dark plate with gold text and no coin.
    3: CashStyle(
        "dark plate, gold text", "grey_button", (70, 78, 104), (255, 200, 40), False
    ),
}
DEFAULT_CASH_STYLE = 1


def cash_style(key: int) -> CashStyle:
    """The style for `ui.cash_display`; an unknown key is a configuration error."""
    try:
        return CASH_STYLES[key]
    except KeyError:
        raise ValueError(
            f"ui.cash_display must be one of {sorted(CASH_STYLES)}, got {key!r}"
        ) from None


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


def apply_cash_style(
    style: CashStyle,
    plate: StateObject,
    icon: StateObject,
    text: TextObject,
    assets: AssetManager,
    coin_font_path: str,
) -> None:
    """Paints `plate` and `icon` and colors `text` for `style`. The widgets keep the size
    and position the panel loader gave them, so the UI scale already applies."""
    image = load_image(
        assets.image_path(style.plate_asset), plate.rect.size, NINE_SLICE
    )
    if style.tint is not None:
        image = image.copy()
        image.fill(style.tint, special_flags=pygame.BLEND_RGB_MULT)
    plate.add_surface(None, image)
    plate.set_state(None)

    icon.active = style.coin
    if style.coin:
        icon.add_surface(None, draw_coin(icon.rect.height, coin_font_path))
        icon.set_state(None)
    text.set_color(style.text_color)
