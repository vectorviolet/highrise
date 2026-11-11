"""Boosters: buildings that earn nothing but raise the income of the tiles around them.

The boost belongs to the tile: every building standing on a covered tile earns more, so sliding
into or out of range changes its income. Overlapping boosters add their bonuses (x1.1 and x1.2
make x1.3, not x1.32). The numbers live in `boosters` in config/settings.yaml.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

# Each shape tells whether `target` is covered by a booster at `origin`, as the row and column
# distance (dr, dc) between them. A booster never covers its own tile.
SHAPES: dict[str, Callable[[int, int], bool]] = {
    "orthogonal": lambda dr, dc: abs(dr) + abs(dc) == 1,
    "diagonal": lambda dr, dc: abs(dr) == 1 and abs(dc) == 1,
    "around": lambda dr, dc: max(abs(dr), abs(dc)) == 1,
    "row_and_column": lambda dr, dc: (dr == 0) != (dc == 0),
}


@dataclass(frozen=True)
class BoosterConfig:
    """The booster numbers of config/settings.yaml, checked."""

    price: dict[str, int]
    multipliers: tuple[float, ...]
    shapes: dict[str, str]

    @classmethod
    def from_dict(cls, data: dict, ages: list[str]) -> "BoosterConfig":
        """Reads the `boosters` section; every age needs a price and a shape."""
        config = cls(
            price=dict(data["price"]),
            multipliers=tuple(data["multipliers"]),
            shapes=dict(data["shapes"]),
        )
        for age in ages:
            if age not in config.price or age not in config.shapes:
                raise ValueError(f"boosters: price and shape needed for age {age!r}")
        for shape in config.shapes.values():
            if shape not in SHAPES:
                raise ValueError(f"boosters: unknown shape {shape!r}")
        if not config.multipliers or any(m <= 1 for m in config.multipliers):
            raise ValueError("boosters: multipliers must be above 1")
        return config

    @classmethod
    def load(cls, ages: list[str]) -> "BoosterConfig":
        """The config of config/settings.yaml."""
        settings = yaml.safe_load(Path("config/settings.yaml").read_text())
        return cls.from_dict(settings["boosters"], ages)

    @property
    def max_level(self) -> int:
        return len(self.multipliers)

    def multiplier(self, level: int) -> float:
        return self.multipliers[level - 1]

    def covers(
        self, age: str, origin: tuple[int, int], target: tuple[int, int]
    ) -> bool:
        """Whether a booster of `age` at `origin` (row, column) covers the `target` tile."""
        return SHAPES[self.shapes[age]](target[0] - origin[0], target[1] - origin[1])
