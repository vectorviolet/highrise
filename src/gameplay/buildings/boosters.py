"""Boosters: buildings that earn nothing but raise the income of the tiles around them.

The boost belongs to the tile: every building standing on a covered tile earns more, so sliding
into or out of range changes its income. Overlapping boosters add their bonuses (x1.1 and x1.2
make x1.3, not x1.32). The numbers live in `boosters` in config/settings.yaml.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

from gameplay.buildings import sprites

# Each shape tells whether `target` is covered by a booster at `origin`, as the row and column
# distance (dr, dc) between them. A booster never covers its own tile.
SHAPES: dict[str, Callable[[int, int], bool]] = {
    "orthogonal": lambda dr, dc: abs(dr) + abs(dc) == 1,
    "diagonal": lambda dr, dc: abs(dr) == 1 and abs(dc) == 1,
    "around": lambda dr, dc: max(abs(dr), abs(dc)) == 1,
    "row_and_column": lambda dr, dc: (dr == 0) != (dc == 0),
}


def _is_number(value: object, kinds: type | tuple[type, ...]) -> bool:
    """Whether `value` is one of `kinds` (a bool is no number here: YAML's `yes` is one)."""
    return isinstance(value, kinds) and not isinstance(value, bool)


@dataclass(frozen=True)
class BoosterConfig:
    """The booster numbers of config/settings.yaml, checked."""

    price: dict[str, int]
    multipliers: tuple[float, ...]
    shapes: dict[str, str]
    # How long the tiles of a booster that was just placed stay lit (ms), whatever the mouse does.
    placed_highlight_ms: int

    @classmethod
    def from_dict(cls, data: dict, ages: list[str], looks: int) -> "BoosterConfig":
        """Reads the `boosters` section; every age needs a price and a shape, and there must be
        one multiplier for each of the `looks` booster levels the recipes have a sprite for
        (a level without a sprite would crash mid-game)."""
        config = cls(
            price=dict(data["price"]),
            multipliers=tuple(data["multipliers"]),
            shapes=dict(data["shapes"]),
            placed_highlight_ms=data["placed_highlight_ms"],
        )
        for age in ages:
            if age not in config.price or age not in config.shapes:
                raise ValueError(f"boosters: price and shape needed for age {age!r}")
        for age in ages:
            price = config.price[age]
            if not _is_number(price, int) or price <= 0:
                raise ValueError(
                    f"boosters: the price for {age!r} must be a positive integer"
                )
        if (
            not _is_number(config.placed_highlight_ms, int)
            or config.placed_highlight_ms < 0
        ):
            raise ValueError(
                "boosters: placed_highlight_ms must be a whole number, 0 or more"
            )
        for shape in config.shapes.values():
            if shape not in SHAPES:
                raise ValueError(f"boosters: unknown shape {shape!r}")
        if not config.multipliers or not all(
            _is_number(m, (int, float)) and math.isfinite(m) and m > 1
            for m in config.multipliers
        ):
            raise ValueError("boosters: multipliers must be finite numbers above 1")
        if len(config.multipliers) != looks:
            raise ValueError(
                f"boosters: {len(config.multipliers)} multipliers in settings.yaml but "
                f"{looks} booster levels in the recipes (config/buildings.yaml)"
            )
        return config

    @classmethod
    def load(cls, ages: list[str]) -> "BoosterConfig":
        """The config of config/settings.yaml."""
        settings = yaml.safe_load(Path("config/settings.yaml").read_text())
        return cls.from_dict(
            settings["boosters"], ages, sprites.level_count(booster=True)
        )

    @property
    def max_level(self) -> int:
        return len(self.multipliers)

    def multiplier(self, level: int) -> float:
        assert 1 <= level <= self.max_level, level
        return self.multipliers[level - 1]

    def covers(
        self, age: str, origin: tuple[int, int], target: tuple[int, int]
    ) -> bool:
        """Whether a booster of `age` at `origin` (row, column) covers the `target` tile."""
        return SHAPES[self.shapes[age]](target[0] - origin[0], target[1] - origin[1])
