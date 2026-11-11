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


MAX_LEVEL = 11
MAX_TILES = 49


def make_tasks(buildings: Buildings, wood_tasks: list[dict]) -> AgeTasks:
    """Tasks for the age of `buildings` (wood first); the other ages get two easy ones."""
    data = {
        "ui": "hover",
        "next_age_cost_factor": 500,
        "ages": {
            "wood": wood_tasks,
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
    config = TasksConfig.from_dict(data, AGES, MAX_LEVEL, MAX_TILES)
    return AgeTasks(config, buildings, AGES)


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
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    place(buildings, tilemap, 1, 1, level=3)

    changed = tasks.update()

    assert changed
    assert tasks.done == {0}
    assert not tasks.all_done()
    assert not tasks.update()  # nothing new


def test_a_done_task_stays_done_when_the_board_falls_behind():
    buildings, tilemap = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    level_3 = place(buildings, tilemap, 1, 1, level=3)
    tasks.update()

    buildings.remove(level_3)
    tasks.update()

    assert tasks.is_done(0)


def test_all_done_when_every_task_is_met():
    buildings, tilemap = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    for column in range(1, 5):
        place(buildings, tilemap, 1, column, level=3)  # 4 x speed 5 = 20

    tasks.update()

    assert tasks.all_done()


def test_boost_is_locked_until_the_first_ages_tasks_are_done():
    buildings, tilemap = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    place(buildings, tilemap, 1, 1, level=3)
    tasks.update()
    assert not tasks.boost_unlocked

    for column in range(2, 5):
        place(buildings, tilemap, 1, column, level=3)
    tasks.update()

    assert tasks.boost_unlocked


def test_boost_stays_unlocked_when_the_board_falls_behind():
    buildings, tilemap = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    for column in range(1, 5):
        place(buildings, tilemap, 1, column, level=3)
    tasks.update()

    buildings.clear()
    tasks.update()

    assert tasks.boost_unlocked


def test_the_second_ages_tasks_do_not_unlock_boost_by_themselves_in_the_first_age():
    buildings, tilemap = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    place(buildings, tilemap, 1, 1, level=3)

    tasks.update()

    assert not tasks.boost_unlocked  # one of two first-age tasks


def test_boost_is_unlocked_in_every_age_after_the_first():
    buildings, _ = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])

    buildings.age_number = 1

    assert tasks.boost_unlocked


def test_the_age_is_the_buildings_age_and_a_new_age_starts_its_tasks_open():
    buildings, tilemap = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    place(buildings, tilemap, 1, 1, level=3)
    tasks.update()
    assert tasks.done == {0}

    buildings.age_number = 1

    assert tasks.age_number == 1
    assert tasks.done == frozenset()
    assert not tasks.is_done(0)


def test_the_next_age_cost_is_the_age_number_plus_one_times_the_factor():
    buildings, _ = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    assert tasks.next_age_cost() == 500

    buildings.age_number = 2

    assert tasks.next_age_cost() == 1500


def test_update_measures_each_task_once_and_keeps_the_values():
    buildings, tilemap = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    place(buildings, tilemap, 1, 1, level=2)  # speed 3
    assert tasks.values == [0.0, 0.0]  # before any update

    tasks.update()

    assert tasks.values == [2, 3]


def test_values_of_an_older_age_are_not_shown_for_the_new_one():
    buildings, tilemap = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    place(buildings, tilemap, 1, 1, level=2)
    tasks.update()

    buildings.age_number = 1

    assert tasks.values == [0.0, 0.0]


def test_restore_takes_up_saved_tasks_for_the_current_age():
    buildings, _ = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])

    tasks.restore({1, 7}, False)  # 7 is no task of the age

    assert tasks.done == {1}
    assert not tasks.boost_unlocked


def test_reset_locks_boost_and_clears_the_tasks():
    buildings, _ = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    tasks.restore({0}, True)

    tasks.reset()

    assert tasks.done == frozenset()
    assert not tasks.boost_unlocked


def test_the_last_age_has_no_tasks():
    buildings, _ = make_grid()
    tasks = make_tasks(buildings, [LEVEL_3, INCOME_20])
    buildings.age_number = len(AGES) - 1

    assert tasks.tasks == ()
    assert tasks.all_done()


# ── the config ────────────────────────────────────────────────────────────────


def test_the_shipped_config_loads_and_every_age_but_the_last_has_two_or_three_tasks():
    config = TasksConfig.load(AGES, MAX_LEVEL, MAX_TILES)

    assert config.ui == "hover"
    assert set(config.ages) == set(AGES[:-1])
    assert all(2 <= len(tasks) <= 3 for tasks in config.ages.values())


def test_the_first_age_asks_for_a_level_3_building_and_20_dollars_a_second():
    wood = TasksConfig.load(AGES, MAX_LEVEL, MAX_TILES).ages["wood"]

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
        # Targets the game can never reach.
        {
            "ages": {
                age: [LEVEL_3, {"type": "building_level", "target": MAX_LEVEL + 1}]
                for age in AGES[:-1]
            }
        },
        {
            "ages": {
                age: [LEVEL_3, {"type": "boosted_buildings", "target": MAX_TILES}]
                for age in AGES[:-1]
            }
        },
    ],
)
def test_a_bad_config_is_refused(changes):
    with pytest.raises(ValueError):
        TasksConfig.from_dict(_data(**changes), AGES, MAX_LEVEL, MAX_TILES)


def test_the_highest_reachable_targets_are_accepted():
    ages = {
        age: [
            {"type": "building_level", "target": MAX_LEVEL},
            {"type": "boosted_buildings", "target": MAX_TILES - 1},
        ]
        for age in AGES[:-1]
    }

    TasksConfig.from_dict(_data(ages=ages), AGES, MAX_LEVEL, MAX_TILES)


@pytest.mark.parametrize(
    ("drop", "message"),
    [
        ("ui", "'ui'"),
        ("next_age_cost_factor", "next_age_cost_factor"),
        ("ages", "'ages'"),
    ],
)
def test_a_missing_key_is_a_value_error_naming_it(drop, message):
    data = _data()
    del data[drop]

    with pytest.raises(ValueError, match=message):
        TasksConfig.from_dict(data, AGES, MAX_LEVEL, MAX_TILES)


def test_a_task_without_a_target_is_a_value_error_naming_it():
    ages = {age: [LEVEL_3, {"type": "income_per_second"}] for age in AGES[:-1]}

    with pytest.raises(ValueError, match="'target'"):
        TasksConfig.from_dict(_data(ages=ages), AGES, MAX_LEVEL, MAX_TILES)


def test_an_age_missing_from_the_file_is_a_value_error_naming_it():
    with pytest.raises(ValueError, match="'rock'"):
        TasksConfig.from_dict(
            _data(ages={"wood": [LEVEL_3, INCOME_20]}), AGES, MAX_LEVEL, MAX_TILES
        )
