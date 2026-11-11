"""Age tasks: what the player must do in an age before NEXT AGE works (issue #52).

The tasks of every age are in config/tasks.yaml. A task, once done, stays done (it is latched
and saved), even if the board changes afterwards. Finishing the tasks of the first age unlocks
BOOST for good. `AgeTasks` holds that state; `Task.current` measures one task on the board.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from gameplay.buildings.building import Building, Buildings

MIN_TASKS = 2
MAX_TASKS = 3


def _plain_buildings(buildings: Buildings) -> list[Building]:
    """The buildings that count: no boosters, none about to be merged away."""
    return [b for b in buildings if not b.is_booster and not b.should_destroy]


def highest_level(buildings: Buildings) -> float:
    return max((b.level for b in _plain_buildings(buildings)), default=0)


def income_per_second(buildings: Buildings) -> float:
    """The current income rate: each building's speed ($ per second) times its boost."""
    return sum(
        b.speed * buildings.income_multiplier(b) for b in _plain_buildings(buildings)
    )


def boosted_count(buildings: Buildings) -> float:
    """How many buildings stand on a tile some booster covers."""
    return sum(
        1 for b in _plain_buildings(buildings) if buildings.income_multiplier(b) > 1
    )


# Task type -> how much of it the board has now. The language files hold `tasks.<type>`.
MEASURES: dict[str, Callable[[Buildings], float]] = {
    "building_level": highest_level,
    "income_per_second": income_per_second,
    "boosted_buildings": boosted_count,
}


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _need(mapping: object, key: str, where: str) -> Any:
    """`mapping[key]`, or a ValueError that names the missing key."""
    if not isinstance(mapping, dict) or key not in mapping:
        raise ValueError(f"tasks: {where} needs {key!r}")
    return mapping[key]


@dataclass(frozen=True)
class Task:
    type: str
    target: int

    def current(self, buildings: Buildings) -> float:
        return MEASURES[self.type](buildings)


@dataclass(frozen=True)
class TasksConfig:
    """config/tasks.yaml, checked."""

    next_age_cost_factor: int
    ages: dict[str, tuple[Task, ...]]

    @classmethod
    def from_dict(
        cls, data: dict, ages: list[str], max_level: int, max_tiles: int
    ) -> "TasksConfig":
        """Every age but the last needs 2 or 3 tasks of a known type with a positive integer
        target (the last age has no NEXT AGE, so no tasks). A target that can never be met would
        lock NEXT AGE for good, so a `building_level` target may not pass the highest building
        level (`max_level`) and a `boosted_buildings` target needs room on the biggest board
        (`max_tiles`) for a booster besides the buildings. An `income_per_second` target can't
        be checked: it depends on how the player builds."""
        factor = _need(data, "next_age_cost_factor", "the file")
        if not _is_positive_int(factor):
            raise ValueError("tasks: next_age_cost_factor must be a positive integer")
        age_entries = _need(data, "ages", "the file")
        limits = {"building_level": max_level, "boosted_buildings": max_tiles - 1}
        tasks: dict[str, tuple[Task, ...]] = {}
        for age in ages[:-1]:
            entries = _need(age_entries, age, "ages")
            if (
                not isinstance(entries, list)
                or not MIN_TASKS <= len(entries) <= MAX_TASKS
            ):
                raise ValueError(
                    f"tasks: age {age!r} needs {MIN_TASKS} to {MAX_TASKS} tasks"
                )
            tasks[age] = tuple(_read_task(age, e, limits) for e in entries)
        unknown = set(age_entries) - set(tasks)
        if unknown:
            raise ValueError(f"tasks: no tasks wanted for the ages {sorted(unknown)}")
        return cls(factor, tasks)

    @classmethod
    def load(cls, ages: list[str], max_level: int, max_tiles: int) -> "TasksConfig":
        """The config of config/tasks.yaml."""
        data = yaml.safe_load(Path("config/tasks.yaml").read_text(encoding="utf-8"))
        return cls.from_dict(data, ages, max_level, max_tiles)


def _read_task(age: str, entry: object, limits: dict[str, int]) -> Task:
    kind = _need(entry, "type", f"a task of age {age!r}")
    target = _need(entry, "target", f"a task of age {age!r}")
    if kind not in MEASURES:
        raise ValueError(f"tasks: unknown task type {kind!r}")
    if not _is_positive_int(target):
        raise ValueError(
            f"tasks: a {kind} target of {age!r} must be a positive integer"
        )
    if target > limits.get(kind, target):
        raise ValueError(
            f"tasks: the {kind} target {target} of {age!r} is more than the game "
            f"allows ({limits[kind]})"
        )
    return Task(kind, target)


class AgeTasks:
    """The tasks of the current age and which of them are done, and whether BOOST is unlocked.

    The age is the one of `buildings` (`Buildings.age_number`), never a copy: tasks done in an
    earlier age are simply not the current age's."""

    def __init__(
        self, config: TasksConfig, buildings: Buildings, ages: list[str]
    ) -> None:
        self.config = config
        self._buildings = buildings
        self._ages = ages
        self._boost_latched = False
        # Done tasks as (age number, task index): an age change opens the new age's tasks
        # without anything to reset.
        self._done: set[tuple[int, int]] = set()
        # What update() measured: (age number, one value per task of that age).
        self._measured: tuple[int, list[float]] = (-1, [])

    @property
    def age_number(self) -> int:
        return self._buildings.age_number

    @property
    def tasks(self) -> tuple[Task, ...]:
        """The current age's tasks (none in the last age)."""
        return self.config.ages.get(self._ages[self.age_number], ())

    @property
    def values(self) -> list[float]:
        """How much of each current task the board had at the last update() (0 before one)."""
        age, values = self._measured
        return values if age == self.age_number else [0.0] * len(self.tasks)

    @property
    def done(self) -> frozenset[int]:
        """The indices of the current age's tasks that are done."""
        return frozenset(i for age, i in self._done if age == self.age_number)

    @property
    def boost_unlocked(self) -> bool:
        """Latched by finishing the first age's tasks; being past the first age counts too."""
        return self._boost_latched or self.age_number >= 1

    def unlock_boost(self) -> None:
        self._boost_latched = True

    def is_done(self, index: int) -> bool:
        return (self.age_number, index) in self._done

    def all_done(self) -> bool:
        return len(self.done) == len(self.tasks)

    def next_age_cost(self) -> int:
        return (self.age_number + 1) * self.config.next_age_cost_factor

    def update(self) -> bool:
        """Measures every current task once and latches those the board meets. Returns whether
        a task was newly done (finishing the first age's last one unlocks BOOST), which makes the
        buttons' texts out of date."""
        age = self.age_number
        values = [task.current(self._buildings) for task in self.tasks]
        self._measured = (age, values)
        changed = False
        for index, (task, value) in enumerate(zip(self.tasks, values)):
            if value >= task.target and (age, index) not in self._done:
                self._done.add((age, index))
                changed = True
        if age == 0 and self.all_done():
            self._boost_latched = True
        return changed

    def restore(self, done: set[int], boost_unlocked: bool) -> None:
        """Takes up a saved state for the buildings' age. Indices that are no task of the age
        are dropped. An old save has no task state (nothing done, BOOST not saved as unlocked):
        its tasks start fresh, and BOOST is unlocked if the save is past the first age."""
        self.reset()
        age = self.age_number
        self._done = {(age, i) for i in done if 0 <= i < len(self.tasks)}
        self._boost_latched = boost_unlocked

    def reset(self) -> None:
        """Nothing done and BOOST not latched (a new game, or before a load)."""
        self._done = set()
        self._boost_latched = False
        self._measured = (-1, [])
