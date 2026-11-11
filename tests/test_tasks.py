"""Age tasks (gameplay/tasks.py): each task type, the latch, the unlock of BOOST and the config
checks. The numbers come from config/tasks.yaml, so the tests build their own small configs."""

import pytest

from gameplay.buildings.boosters import BoosterConfig
from gameplay.buildings.building import AGES, Buildings
from gameplay.tasks import AgeTasks, Task, TasksConfig
from gameplay.tilemap import Tilemap


def make_grid(size=5) -> tuple[Buildings, Tilemap]:
    return Buildings(boosters=BoosterConfig.load(AGES)), Tilemap(size, size)


def place(buildings, tilemap, row, col, *, level=1, booster=False):
    b = buildings.create(level, tilemap[row - 1][col - 1], booster=booster)
    buildings.append(b)
    return b


def make_tasks(*age_tasks: dict) -> AgeTasks:
    """Tasks for the wood age (and rock, if given a second list)."""
    data = {
        "ui": "hover",
        "next_age_cost_factor": 500,
        "ages": {
            "wood": list(age_tasks[0]),
            "rock": [
                {"type": "building_level", "target": 2},
                {"type": "building_level", "target": 3},
            ],
            "sand": [
                {"type": "building_level", "target": 2},
                {"type": "building_level", "target": 3},
            ],
        },
    }
    return AgeTasks(TasksConfig.from_dict(data, AGES), AGES)


LEVEL_3 = {"type": "building_level", "target": 3}
INCOME_20 = {"type": "income_per_second", "target": 20}
BOOSTED_2 = {"type": "boosted_buildings", "target": 2}


def test_building_level_needs_a_building_of_that_level_or_higher():
    buildings, tilemap = make_grid()
    task = Task("building_level", 3)
    place(buildings, tilemap, 1, 1, level=2)
    assert task.current(buildings) < 3

    place(buildings, tilemap, 1, 2, level=4)

    assert task.current(buildings) >= 3


def test_a_booster_does_not_count_as_a_building_level():
    buildings, tilemap = make_grid()
    place(buildings, tilemap, 1, 1, level=1)
    place(buildings, tilemap, 1, 2, level=5, booster=True)

    assert Task("building_level", 3).current(buildings) == 1


def test_income_per_second_adds_the_speed_of_every_building():
    buildings, tilemap = make_grid()
    place(buildings, tilemap, 1, 1, level=3)  # wood, level 3: speed 5
    place(buildings, tilemap, 1, 3, level=2)  # speed 3

    assert Task("income_per_second", 8).current(buildings) == 8


def test_income_per_second_includes_the_boost():
    buildings, tilemap = make_grid()
    place(buildings, tilemap, 1, 1, level=3)  # speed 5
    place(buildings, tilemap, 1, 2, booster=True)  # wood booster x1.1 next to it

    assert Task("income_per_second", 1).current(buildings) == pytest.approx(5.5)


def test_boosted_buildings_counts_buildings_on_covered_tiles_only():
    buildings, tilemap = make_grid()
    place(buildings, tilemap, 2, 2, booster=True)  # wood: the 4 neighbors
    place(buildings, tilemap, 1, 2)  # covered
    place(buildings, tilemap, 2, 1)  # covered
    place(buildings, tilemap, 1, 1)  # diagonal: not covered
    place(buildings, tilemap, 4, 4)  # far away

    assert Task("boosted_buildings", 2).current(buildings) == 2


def test_a_booster_is_not_a_boosted_building():
    buildings, tilemap = make_grid()
    place(buildings, tilemap, 2, 2, booster=True)
    place(buildings, tilemap, 2, 3, booster=True)  # covered by the first one

    assert Task("boosted_buildings", 1).current(buildings) == 0


def test_a_building_waiting_to_merge_away_is_not_counted():
    buildings, tilemap = make_grid()
    leaving = place(buildings, tilemap, 1, 1, level=3)
    leaving.should_destroy = True

    assert Task("building_level", 1).current(buildings) == 0
    assert Task("income_per_second", 1).current(buildings) == 0


def test_a_task_is_done_when_the_board_meets_it_and_not_before():
    buildings, tilemap = make_grid()
    tasks = make_tasks([LEVEL_3, INCOME_20])
    place(buildings, tilemap, 1, 1, level=3)

    changed = tasks.update(buildings)

    assert changed
    assert tasks.done == {0}
    assert not tasks.all_done()
    assert not tasks.update(buildings)  # nothing new


def test_a_done_task_stays_done_when_the_board_falls_behind():
    buildings, tilemap = make_grid()
    tasks = make_tasks([LEVEL_3, INCOME_20])
    level_3 = place(buildings, tilemap, 1, 1, level=3)
    tasks.update(buildings)

    buildings.remove(level_3)
    tasks.update(buildings)

    assert tasks.is_done(0)


def test_all_done_when_every_task_is_met():
    buildings, tilemap = make_grid()
    tasks = make_tasks([LEVEL_3, INCOME_20])
    for column in range(1, 5):
        place(buildings, tilemap, 1, column, level=3)  # 4 x speed 5 = 20

    tasks.update(buildings)

    assert tasks.all_done()


def test_boost_is_locked_until_the_first_ages_tasks_are_done():
    buildings, tilemap = make_grid()
    tasks = make_tasks([LEVEL_3, INCOME_20])
    place(buildings, tilemap, 1, 1, level=3)
    tasks.update(buildings)
    assert not tasks.boost_unlocked

    for column in range(2, 5):
        place(buildings, tilemap, 1, column, level=3)
    tasks.update(buildings)

    assert tasks.boost_unlocked


def test_boost_stays_unlocked_when_the_board_falls_behind():
    buildings, tilemap = make_grid()
    tasks = make_tasks([LEVEL_3, INCOME_20])
    for column in range(1, 5):
        place(buildings, tilemap, 1, column, level=3)
    tasks.update(buildings)

    buildings.clear()
    tasks.update(buildings)

    assert tasks.boost_unlocked


def test_the_second_ages_tasks_do_not_unlock_boost():
    tasks = make_tasks([LEVEL_3, INCOME_20])
    tasks.start_age(1)
    buildings, tilemap = make_grid()
    tasks.boost_unlocked = False
    place(buildings, tilemap, 1, 1, level=3)

    tasks.update(buildings)

    assert tasks.all_done()
    assert not tasks.boost_unlocked


def test_entering_an_age_starts_its_tasks_open_and_unlocks_boost():
    tasks = make_tasks([LEVEL_3, INCOME_20])
    tasks.restore(0, {0, 1}, False)

    tasks.start_age(1)

    assert tasks.done == frozenset()
    assert tasks.boost_unlocked


def test_the_next_age_cost_is_the_age_number_plus_one_times_the_factor():
    tasks = make_tasks([LEVEL_3, INCOME_20])
    assert tasks.next_age_cost() == 500

    tasks.start_age(2)

    assert tasks.next_age_cost() == 1500


def test_reset_locks_boost_and_clears_the_tasks():
    tasks = make_tasks([LEVEL_3, INCOME_20])
    tasks.restore(1, {0}, True)

    tasks.reset()

    assert tasks.age_number == 0
    assert tasks.done == frozenset()
    assert not tasks.boost_unlocked


def test_the_last_age_has_no_tasks():
    tasks = make_tasks([LEVEL_3, INCOME_20])
    tasks.start_age(len(AGES) - 1)

    assert tasks.tasks == ()
    assert tasks.all_done()


# ── the config ────────────────────────────────────────────────────────────────


def test_the_shipped_config_loads_and_every_age_but_the_last_has_two_or_three_tasks():
    config = TasksConfig.load(AGES)

    assert config.ui == "hover"
    assert set(config.ages) == set(AGES[:-1])
    assert all(2 <= len(tasks) <= 3 for tasks in config.ages.values())


def test_the_first_age_asks_for_a_level_3_building_and_20_dollars_a_second():
    wood = TasksConfig.load(AGES).ages["wood"]

    assert wood == (Task("building_level", 3), Task("income_per_second", 20))


def _data(**changes) -> dict:
    data = {
        "ui": "hover",
        "next_age_cost_factor": 500,
        "ages": {age: [LEVEL_3, INCOME_20] for age in AGES[:-1]},
    }
    data.update(changes)
    return data


@pytest.mark.parametrize(
    "changes",
    [
        {"ui": "sidebar"},
        {"next_age_cost_factor": 0},
        {"next_age_cost_factor": True},
        {"ages": {age: [LEVEL_3] for age in AGES[:-1]}},  # one task
        {"ages": {age: [LEVEL_3] * 4 for age in AGES[:-1]}},  # four tasks
        {"ages": {"wood": [LEVEL_3, INCOME_20]}},  # ages missing
        {"ages": {age: [LEVEL_3, {"type": "nope", "target": 1}] for age in AGES[:-1]}},
        {
            "ages": {
                age: [LEVEL_3, {"type": "building_level", "target": 0}]
                for age in AGES[:-1]
            }
        },
        {"ages": {age: [LEVEL_3, INCOME_20] for age in AGES}},  # a task in the last age
    ],
)
def test_a_bad_config_is_refused(changes):
    with pytest.raises(ValueError):
        TasksConfig.from_dict(_data(**changes), AGES)
