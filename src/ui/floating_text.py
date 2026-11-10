"""Floating money text: a green "+$X" that rises over a building that paid or was sold, and a
red "-$X" that falls onto the cash display from just above it when the player spends (the
display sits at the bottom screen edge, so there is no room below it).

Nothing here knows about the game: callers pass the screen position, the amount and the time
(milliseconds, the same clock the building timers use), so the logic is testable without a
window. The numbers come from `floating_text` in config/settings.yaml (FloatingTextConfig).

Payouts from the same source within `merge_window_ms` of its first text are added into that one
number instead of starting another, so a busy board stays readable.
"""

from dataclasses import dataclass

import pygame
from pygame.math import Vector2

from ui.money_format import format_money

Color = tuple[int, int, int]

ALPHA_STEPS = 16  # the fade-out is drawn in this many opacity steps
MAX_CACHED_IMAGES = 400


@dataclass(frozen=True)
class FloatingTextConfig:
    font_size: int  # pixels at 100% UI scale
    gain_color: Color
    spend_color: Color
    outline_color: Color
    lifetime_ms: int
    rise: int  # pixels a gain moves up over its life, at 100% UI scale
    fall: int  # pixels a spend moves down over its life, at 100% UI scale
    merge_window_ms: int
    max_texts: int  # alive at once; the oldest is dropped first

    @classmethod
    def from_dict(cls, values: dict) -> "FloatingTextConfig":
        if values["max_texts"] < 1:
            raise ValueError("floating_text.max_texts must be at least 1")
        if values["lifetime_ms"] <= 0:
            raise ValueError("floating_text.lifetime_ms must be greater than 0")
        return cls(
            font_size=values["font_size"],
            gain_color=tuple(values["gain_color"]),
            spend_color=tuple(values["spend_color"]),
            outline_color=tuple(values["outline_color"]),
            lifetime_ms=values["lifetime_ms"],
            rise=values["rise"],
            fall=values["fall"],
            merge_window_ms=values["merge_window_ms"],
            max_texts=values["max_texts"],
        )


@dataclass
class FloatingText:
    position: Vector2  # where it starts: the middle of its bottom edge
    amount: int  # positive: gained; negative: spent
    born_ms: int
    key: object | None  # the source whose payouts merge; None for spends
    direction: int  # -1 moves up the screen, 1 moves down

    @property
    def over_world(self) -> bool:
        """Whether it floats over the game world (a gain) rather than the HUD (a spend)."""
        return self.amount > 0

    @property
    def text(self) -> str:
        sign = "+" if self.amount > 0 else "-"
        return sign + format_money(abs(self.amount))


def progress(text: FloatingText, now_ms: int, lifetime_ms: int) -> float:
    """How far through its life `text` is, from 0.0 (just born) to 1.0 (gone)."""
    return min(1.0, max(0.0, (now_ms - text.born_ms) / lifetime_ms))


class FloatingTexts:
    def __init__(self, config: FloatingTextConfig, font_path: str) -> None:
        self.config = config
        self.scale = 1.0  # the UI scale as a factor: 1.1 at 110%
        self._font_path = font_path
        self._fonts: dict[int, pygame.font.Font] = {}
        self._images: dict[tuple[str, int, int], pygame.Surface] = {}
        self.texts: list[FloatingText] = []

    def gain(self, key: object | None, position, amount: int, now_ms: int) -> None:
        """A green "+amount" rising from `position`. With a `key`, a text for the same key
        that is still inside the merge window takes the amount instead (and keeps floating);
        with no key (a sale) the gain always gets its own text."""
        assert amount > 0, "a gain must be positive"
        for text in self.texts if key is not None else ():
            if (
                text.key is key
                and text.amount > 0
                and now_ms - text.born_ms < self.config.merge_window_ms
            ):
                text.amount += amount
                return
        self._add(FloatingText(Vector2(position), amount, now_ms, key, -1))

    def spend(self, position, amount: int, now_ms: int) -> None:
        """A red "-amount" falling from `position`."""
        assert amount > 0, "a spend must be positive"
        self._add(FloatingText(Vector2(position), -amount, now_ms, None, 1))

    def _add(self, text: FloatingText) -> None:
        self.texts.append(text)
        del self.texts[: -self.config.max_texts]

    def update(self, now_ms: int) -> None:
        """Drops the texts whose life is over."""
        life = self.config.lifetime_ms
        self.texts = [t for t in self.texts if now_ms - t.born_ms < life]

    def clear(self) -> None:
        self.texts.clear()

    def current_position(self, text: FloatingText, now_ms: int) -> Vector2:
        """Where `text` is at `now_ms`: eased, so it moves fast first and settles."""
        t = progress(text, now_ms, self.config.lifetime_ms)
        distance = self.config.fall if text.direction > 0 else self.config.rise
        eased = 1 - (1 - t) ** 2
        return text.position + Vector2(
            0, text.direction * distance * self.scale * eased
        )

    def draw(
        self, surface: pygame.Surface, now_ms: int, *, over_world: bool = True
    ) -> None:
        """Draws the texts; the gains over the world only when `over_world` (they would
        cover a panel that is open over the world)."""
        for text in self.texts:
            if text.over_world and not over_world:
                continue
            fade = 1 - progress(text, now_ms, self.config.lifetime_ms) ** 2
            image = self._render(text, round(fade * ALPHA_STEPS))
            position = self.current_position(text, now_ms)
            surface.blit(
                image, image.get_rect(midbottom=(round(position.x), round(position.y)))
            )

    @property
    def _size(self) -> int:
        """The font size in pixels at the current UI scale."""
        return max(1, round(self.config.font_size * self.scale))

    def _font(self) -> pygame.font.Font:
        size = self._size
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(self._font_path, size)
        return self._fonts[size]

    def _render(
        self, text: FloatingText, alpha_step: int = ALPHA_STEPS
    ) -> pygame.Surface:
        """The image of `text` at `alpha_step` of ALPHA_STEPS opacity, cached: the
        fade has few steps, so no frame copies a surface."""
        cache_key = (text.text, self._size, alpha_step)
        if cache_key not in self._images:
            if len(self._images) > MAX_CACHED_IMAGES:
                self._images.clear()
            image = self._paint(text)
            image.set_alpha(round(255 * alpha_step / ALPHA_STEPS))
            self._images[cache_key] = image
        return self._images[cache_key]

    def _paint(self, text: FloatingText) -> pygame.Surface:
        color = self.config.gain_color if text.amount > 0 else self.config.spend_color
        font = self._font()
        face = font.render(text.text, True, color)
        outline = font.render(text.text, True, self.config.outline_color)
        reach = max(1, round(2 * self.scale))
        image = pygame.Surface(
            (face.get_width() + 2 * reach, face.get_height() + 2 * reach),
            pygame.SRCALPHA,
        )
        for dx, dy in (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (1, 1),
            (-1, 1),
            (1, -1),
        ):
            image.blit(outline, (reach + dx * reach, reach + dy * reach))
        image.blit(face, (reach, reach))
        return image
