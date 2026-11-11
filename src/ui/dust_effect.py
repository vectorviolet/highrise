"""The sell effect: a puff of dust and a few chips of debris where a building stood.

Nothing here knows about the game: callers pass the building's screen rect and the time
(milliseconds, the same clock the floating texts use), so the logic is testable without a
window. The numbers come from `sell_effect` in config/settings.yaml (DustConfig).

Each burst's particles are made once, when it starts, with their whole path fixed by their
start speed; a frame only moves and draws them. The circles are painted once per size and
opacity step and cached, so a frame copies no surface. A burst that is over is dropped.
"""

import random
from dataclasses import dataclass

import pygame
from pygame.math import Vector2

Color = tuple[int, int, int]

ALPHA_STEPS = 8  # the fade-out is drawn in this many opacity steps
PUFF_OPACITY = 0.75  # puffs are soft: this share of a chip's opacity


def _check_color(color: object) -> None:
    """Raises ValueError unless `color` is a list of 3 whole numbers from 0 to 255."""
    ok = (
        isinstance(color, (list, tuple))
        and len(color) == 3
        and all(isinstance(c, int) and 0 <= c <= 255 for c in color)
    )
    if not ok:
        raise ValueError(
            f"sell_effect colors must be [r, g, b] in 0-255, got {color!r}"
        )


def _validate(values: dict) -> None:
    """Raises ValueError for a sell_effect section that would fail on a sale."""
    if values["lifetime_ms"] <= 0:
        raise ValueError("sell_effect.lifetime_ms must be greater than 0")
    if values["max_bursts"] < 1:
        raise ValueError("sell_effect.max_bursts must be at least 1")
    for key in ("dust_count", "debris_count"):
        if not isinstance(values[key], int) or values[key] < 0:
            raise ValueError(f"sell_effect.{key} must be a whole number, 0 or more")
    for key in ("dust_growth", "spread", "rise", "gravity"):
        if values[key] < 0:
            raise ValueError(f"sell_effect.{key} must be 0 or more")
    for key in ("dust_radius", "debris_size"):
        low, high = values[key]
        if not 1 <= low <= high:
            raise ValueError(f"sell_effect.{key} must be [min, max] with min >= 1")
    _validate_colors(values)


def _validate_colors(values: dict) -> None:
    if not values["debris_colors"]:
        raise ValueError("sell_effect.debris_colors needs at least one color")
    for color in (values["dust_color"], *values["debris_colors"]):
        _check_color(color)


@dataclass(frozen=True)
class DustConfig:
    lifetime_ms: int
    dust_count: int  # soft puffs per burst
    debris_count: int  # small falling chips per burst
    dust_radius: tuple[int, int]  # a puff's starting radius range, pixels
    dust_growth: float  # a puff's radius multiplier at the end of its life
    debris_size: tuple[int, int]  # a chip's side range, pixels
    spread: float  # pixels a particle travels sideways over its life, at most
    rise: float  # pixels a puff drifts up over its life, at most
    gravity: float  # pixels a chip falls over its life
    dust_color: Color
    debris_colors: tuple[Color, ...]
    max_bursts: int  # alive at once; the oldest is dropped first

    @classmethod
    def from_dict(cls, values: dict) -> "DustConfig":
        _validate(values)
        return cls(
            lifetime_ms=values["lifetime_ms"],
            dust_count=values["dust_count"],
            debris_count=values["debris_count"],
            dust_radius=tuple(values["dust_radius"]),
            dust_growth=values["dust_growth"],
            debris_size=tuple(values["debris_size"]),
            spread=values["spread"],
            rise=values["rise"],
            gravity=values["gravity"],
            dust_color=tuple(values["dust_color"]),
            debris_colors=tuple(tuple(c) for c in values["debris_colors"]),
            max_bursts=values["max_bursts"],
        )


@dataclass(frozen=True)
class Particle:
    origin: Vector2
    sideways: float  # pixels moved sideways over the whole life
    lift: float  # pixels moved up over the whole life, before gravity
    size: int  # a puff's radius or a chip's side
    color: Color
    is_debris: bool


@dataclass
class Burst:
    born_ms: int
    particles: list[Particle]


def progress(burst: Burst, now_ms: int, lifetime_ms: int) -> float:
    """How far through its life `burst` is, from 0.0 (just born) to 1.0 (over)."""
    return min(1.0, max(0.0, (now_ms - burst.born_ms) / lifetime_ms))


class DustBursts:
    def __init__(self, config: DustConfig, rng: random.Random | None = None) -> None:
        self.config = config
        self._rng = rng or random.Random()
        self._images: dict[tuple[bool, int, Color, int], pygame.Surface] = {}
        self.bursts: list[Burst] = []

    def spawn(self, rect: pygame.Rect, now_ms: int) -> None:
        """Starts a burst over `rect`, the area the sold building covered."""
        cfg, rng = self.config, self._rng
        particles = [
            Particle(
                origin=Vector2(
                    rng.uniform(rect.left, rect.right),
                    rng.uniform(rect.centery, rect.bottom),
                ),
                sideways=rng.uniform(-cfg.spread, cfg.spread) * 0.6,
                lift=rng.uniform(0.3, 1.0) * cfg.rise,
                size=rng.randint(*cfg.dust_radius),
                color=cfg.dust_color,
                is_debris=False,
            )
            for _ in range(cfg.dust_count)
        ]
        particles += [
            Particle(
                origin=Vector2(
                    rng.uniform(rect.left, rect.right),
                    rng.uniform(rect.top, rect.bottom),
                ),
                sideways=rng.uniform(-cfg.spread, cfg.spread),
                lift=rng.uniform(0.0, 0.6) * cfg.rise,
                size=rng.randint(*cfg.debris_size),
                color=rng.choice(cfg.debris_colors),
                is_debris=True,
            )
            for _ in range(cfg.debris_count)
        ]
        self.bursts.append(Burst(now_ms, particles))
        del self.bursts[: -cfg.max_bursts]

    def update(self, now_ms: int) -> None:
        """Drops the bursts whose life is over."""
        life = self.config.lifetime_ms
        self.bursts = [b for b in self.bursts if now_ms - b.born_ms < life]

    def clear(self) -> None:
        self.bursts.clear()

    def position(self, particle: Particle, t: float) -> Vector2:
        """Where `particle` is `t` (0.0 to 1.0) of the way through its life: it moves fast
        first and settles; a chip also falls."""
        eased = 1 - (1 - t) ** 2
        y = -particle.lift * eased
        if particle.is_debris:
            y += self.config.gravity * t * t
        return particle.origin + Vector2(particle.sideways * eased, y)

    def draw(self, surface: pygame.Surface, now_ms: int) -> None:
        life = self.config.lifetime_ms
        for burst in self.bursts:
            t = progress(burst, now_ms, life)
            fade = round((1 - t) * ALPHA_STEPS)
            if fade == 0:
                continue
            for particle in burst.particles:
                image = self._image(particle, t, fade)
                position = self.position(particle, t)
                center = (round(position.x), round(position.y))
                surface.blit(image, image.get_rect(center=center))

    def _image(self, particle: Particle, t: float, fade: int) -> pygame.Surface:
        """The picture of `particle` at opacity step `fade`, cached. A puff grows as it
        fades; its size is rounded, so there are few pictures."""
        size = particle.size
        if not particle.is_debris:
            size = max(1, round(size * (1 + (self.config.dust_growth - 1) * t)))
        key = (particle.is_debris, size, particle.color, fade)
        image = self._images.get(key)
        if image is None:
            image = self._paint(particle.is_debris, size, particle.color, fade)
            self._images[key] = image
        return image

    @staticmethod
    def _paint(is_debris: bool, size: int, color: Color, fade: int) -> pygame.Surface:
        alpha = round(255 * fade / ALPHA_STEPS)
        if is_debris:
            image = pygame.Surface((size, size), pygame.SRCALPHA)
            image.fill((*color, alpha))
        else:
            image = pygame.Surface((2 * size, 2 * size), pygame.SRCALPHA)
            pygame.draw.circle(
                image, (*color, round(alpha * PUFF_OPACITY)), (size, size), size
            )
        return image


class DustLayer:
    """The bursts as a world object: a panel draws it with the tiles and buildings, under
    the HUD, at the current time."""

    def __init__(self, bursts: DustBursts) -> None:
        self.bursts = bursts

    def draw(self, surface: pygame.Surface) -> None:
        self.bursts.draw(surface, pygame.time.get_ticks())
