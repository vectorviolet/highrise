"""Age tasks: what the player must do in an age before NEXT AGE works (issue #52).

The tasks of every age are in config/tasks.yaml. A task, once done, stays done (it is latched
and saved), even if the board changes afterwards. Finishing the tasks of the first age unlocks
BOOST for good. `AgeTasks` holds that state; `Task.current` measures one task on the board.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

from gameplay.buildings.building import Building, Buildings

MIN_TASKS = 2
MAX_TASKS = 3
UI_MODES = ("hover", "panel")


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


@dataclass(frozen=True)
class Task:
    type: str
    target: int

    def current(self, buildings: Buildings) -> float:
        return MEASURES[self.type](buildings)


@dataclass(frozen=True)
class TasksConfig:
    """config/tasks.yaml, checked."""

    ui: str
    next_age_cost_factor: int
    ages: dict[str, tuple[Task, ...]]

    @classmethod
    def from_dict(cls, data: dict, ages: list[str]) -> "TasksConfig":
        """Every age but the last needs 2 or 3 tasks of a known type with a positive integer
        target (the last age has no NEXT AGE, so no tasks)."""
        ui = data["ui"]
        if ui not in UI_MODES:
            raise ValueError(f"tasks: ui must be one of {UI_MODES}, not {ui!r}")
        factor = data["next_age_cost_factor"]
        if not _is_positive_int(factor):
            raise ValueError("tasks: next_age_cost_factor must be a positive integer")
        tasks: dict[str, tuple[Task, ...]] = {}
        for age in ages[:-1]:
            entries = data["ages"].get(age)
            if (
                not isinstance(entries, list)
                or not MIN_TASKS <= len(entries) <= MAX_TASKS
            ):
                raise ValueError(
                    f"tasks: age {age!r} needs {MIN_TASKS} to {MAX_TASKS} tasks"
                )
            for entry in entries:
                if entry["type"] not in MEASURES:
                    raise ValueError(f"tasks: unknown task type {entry['type']!r}")
                if not _is_positive_int(entry["target"]):
                    raise ValueError(
                        f"tasks: a target of age {age!r} must be a positive integer"
                    )
            tasks[age] = tuple(Task(e["type"], e["target"]) for e in entries)
        unknown = set(data["ages"]) - set(tasks)
        if unknown:
            raise ValueError(f"tasks: no tasks wanted for the ages {sorted(unknown)}")
        return cls(ui, factor, tasks)

    @classmethod
    def load(cls, ages: list[str]) -> "TasksConfig":
        """The config of config/tasks.yaml."""
        data = yaml.safe_load(Path("config/tasks.yaml").read_text(encoding="utf-8"))
        return cls.from_dict(data, ages)


class AgeTasks:
    """The tasks of the current age and which of them are done, and whether BOOST is unlocked."""

    def __init__(self, config: TasksConfig, ages: list[str]) -> None:
        self.config = config
        self._ages = ages
        self.age_number = 0
        self.boost_unlocked = False
        self._done: set[int] = set()

    @property
    def tasks(self) -> tuple[Task, ...]:
        """The current age's tasks (none in the last age)."""
        return self.config.ages.get(self._ages[self.age_number], ())

    @property
    def done(self) -> frozenset[int]:
        """The indices of the current age's tasks that are done."""
        return frozenset(self._done)

    def is_done(self, index: int) -> bool:
        return index in self._done

    def all_done(self) -> bool:
        return len(self._done) == len(self.tasks)

    def next_age_cost(self) -> int:
        return (self.age_number + 1) * self.config.next_age_cost_factor

    def update(self, buildings: Buildings) -> bool:
        """Latches every task the board meets now. Returns whether anything changed
        (a task finished or BOOST unlocked)."""
        before = (len(self._done), self.boost_unlocked)
        for index, task in enumerate(self.tasks):
            if index not in self._done and task.current(buildings) >= task.target:
                self._done.add(index)
        if self.age_number == 0 and self.all_done():
            self.boost_unlocked = True
        return before != (len(self._done), self.boost_unlocked)

    def start_age(self, age_number: int) -> None:
        """Enters an age with its tasks all open. Being past the first age unlocks BOOST."""
        assert 0 <= age_number < len(self._ages), age_number
        self.age_number = age_number
        self._done = set()
        if age_number >= 1:
            self.boost_unlocked = True

    def restore(self, age_number: int, done: set[int], boost_unlocked: bool) -> None:
        """Takes up a saved state. Indices that are no task of the age are dropped. An old save
        has no task state (nothing done, BOOST not saved as unlocked): its tasks start fresh,
        and BOOST is unlocked if the save is past the first age."""
        self.reset()
        self.start_age(age_number)
        self._done = {i for i in done if 0 <= i < len(self.tasks)}
        self.boost_unlocked = self.boost_unlocked or boost_unlocked

    def reset(self) -> None:
        """A new game: the first age, nothing done, BOOST locked."""
        self.age_number = 0
        self._done = set()
        self.boost_unlocked = False
