"""Validate a complete browser snapshot before changing any live game objects."""

from math import isfinite

from gameplay.buildings.building import AGES
from gameplay.buildings.sprites import DOOR_SIDES, default_door_side


class InvalidWebSave(ValueError):
    pass


def volume_or_default(value: object, default: float) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            if isfinite(value):
                return value
        except OverflowError:
            pass
    return default


def _integer(value: object, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise InvalidWebSave("Invalid integer in browser save")
    return value


def _building(record: object, size: int, max_level: int, booster_levels: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidWebSave("Invalid building record")
    row = _integer(record.get("row"), 1, size)
    column = _integer(record.get("column"), 1, size)
    booster = record.get("booster", False)
    if type(booster) is not bool:
        raise InvalidWebSave("Invalid building kind")
    level = _integer(record.get("level"), 1, booster_levels if booster else max_level)
    fraction = record.get("income_fraction", 0.0)
    if type(fraction) not in (int, float) or not 0 <= fraction < 1:
        raise InvalidWebSave("Invalid income fraction")
    side = record.get("door_side")
    if side not in DOOR_SIDES:
        side = default_door_side(row, column)
    return dict(
        row=row,
        column=column,
        level=level,
        booster=booster,
        income_fraction=fraction,
        door_side=side,
    )


def validate_snapshot(
    data: dict, max_size: int, max_level: int, booster_levels: int, starting_money: int
) -> dict:
    version = _integer(data.get("version", 1), 1, 1)
    age = _integer(data.get("age", 0), 0, len(AGES) - 1)
    size = _integer(data.get("size", 2), 2, max_size)
    money = data.get("money", starting_money)
    if type(money) is not int or money < 0:
        raise InvalidWebSave("Invalid money")
    records = data.get("buildings", [])
    if not isinstance(records, list) or len(records) > size * size:
        raise InvalidWebSave("Invalid buildings")
    buildings = [_building(b, size, max_level, booster_levels) for b in records]
    if len({(b["row"], b["column"]) for b in buildings}) != len(buildings):
        raise InvalidWebSave("Multiple buildings on a tile")
    tasks = data.get("tasks_done", [])
    tasks = [i for i in tasks if type(i) is int] if isinstance(tasks, list) else []
    return dict(
        version=version,
        age=age,
        size=size,
        money=money,
        buildings=buildings,
        tasks_done=tasks,
        boost_unlocked=data.get("boost_unlocked") is True,
    )
