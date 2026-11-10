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

Color = tuple[int, int, int]


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
    def text(self) -> str:
        return f"+${self.amount}" if self.amount > 0 else f"-${-self.amount}"


def progress(text: FloatingText, now_ms: int, lifetime_ms: int) -> float:
    """How far through its life `text` is, from 0.0 (just born) to 1.0 (gone)."""
    return min(1.0, max(0.0, (now_ms - text.born_ms) / lifetime_ms))


class FloatingTexts:
    def __init__(self, config: FloatingTextConfig, font_path: str) -> None:
        self.config = config
        self.scale = 1.0  # the UI scale as a factor: 1.1 at 110%
        self._font_path = font_path
        self._fonts: dict[int, pygame.font.Font] = {}
        self._images: dict[tuple[str, int], pygame.Surface] = {}
        self.texts: list[FloatingText] = []

    def gain(self, key: object, position, amount: int, now_ms: int) -> None:
        """A green "+$amount" rising from `position`. A text for the same `key` that is
        still inside the merge window takes the amount instead (and keeps floating)."""
        assert amount > 0, "a gain must be positive"
        for text in self.texts:
            if (
                text.key is key
                and text.amount > 0
                and now_ms - text.born_ms < self.config.merge_window_ms
            ):
                text.amount += amount
                return
        self._add(FloatingText(Vector2(position), amount, now_ms, key, -1))

    def spend(self, position, amount: int, now_ms: int) -> None:
        """A red "-$amount" falling from `position`."""
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

    def draw(self, surface: pygame.Surface, now_ms: int) -> None:
        for text in self.texts:
            fade = 1 - progress(text, now_ms, self.config.lifetime_ms) ** 2
            image = self._render(text).copy()
            image.set_alpha(round(255 * fade))
            position = self.current_position(text, now_ms)
            surface.blit(
                image, image.get_rect(midbottom=(round(position.x), round(position.y)))
            )

    def _font(self) -> pygame.font.Font:
        size = max(1, round(self.config.font_size * self.scale))
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(self._font_path, size)
        return self._fonts[size]

    def _render(self, text: FloatingText) -> pygame.Surface:
        size = round(self.config.font_size * self.scale)
        cache_key = (text.text, size)
        if cache_key not in self._images:
            if len(self._images) > 200:
                self._images.clear()
            self._images[cache_key] = self._paint(text)
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
