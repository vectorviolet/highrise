"""Building sprites composed from pack pieces by the recipes in config/buildings.yaml.

A sprite is cached per (age, level, door side), so composing happens once per combination, never
per frame. `compose` builds the full-size sprite, `game_sprite` the one drawn in the world.
"""

from functools import cache
from pathlib import Path
from random import choice

import pygame
import yaml
from pygamine import ImagePath
from pygamine import load_image

RECIPES_PATH = Path("config/buildings.yaml")
PIECES_FOLDER = "buildings"
DOOR_SIDES = ("left", "right")


@cache
def recipes() -> dict:
    with open(RECIPES_PATH, encoding="utf-8") as file:
        return yaml.safe_load(file)


def level_count() -> int:
    """How many levels the recipes define."""
    return len(recipes()["levels"])


def checked_max_level(max_level: int) -> int:
    """`max_level` itself, if the recipes have a sprite for every level up to it."""
    if max_level > level_count():
        raise ValueError(
            f"max_building_level {max_level} is more than the {level_count()} levels "
            f"in {RECIPES_PATH.as_posix()}"
        )
    return max_level


def random_door_side() -> str:
    return choice(DOOR_SIDES)


def default_door_side(row: int, column: int) -> str:
    """A deterministic side for a building without a saved one (a save from before door sides)."""
    return DOOR_SIDES[(row + column) % 2]


def piece_names(age: str, level: int, door_side: str) -> tuple[list[str], str]:
    """The floor piece names (bottom to top) and the roof piece name of one sprite."""
    assert door_side in DOOR_SIDES, door_side
    config = recipes()
    prefixes = config["ages"][age]
    level_recipe = config["levels"][level - 1]
    floors = []
    for kind in level_recipe["floors"]:
        entry = config["floor_kinds"][kind]
        floors.append(
            prefixes["floor"] + (entry if isinstance(entry, str) else entry[door_side])
        )
    return floors, prefixes["roof"] + "Roof" + level_recipe["roof"]


def all_piece_names() -> set[str]:
    """Every piece file name (without extension) the recipes can ask for."""
    names: set[str] = set()
    for age in recipes()["ages"]:
        for level in range(1, level_count() + 1):
            for side in DOOR_SIDES:
                floors, roof = piece_names(age, level, side)
                names.update(floors, [roof])
    return names


def _piece(name: str) -> pygame.Surface:
    return load_image(ImagePath(name, PIECES_FOLDER))


@cache
def compose(age: str, level: int, door_side: str) -> pygame.Surface:
    """The full-size sprite: floors stacked and the roof on top, its foot at the bottom edge."""
    config = recipes()
    floor_names, roof_name = piece_names(age, level, door_side)
    floors = [_piece(name) for name in floor_names]
    roof = _piece(roof_name)
    width, floor_height = floors[0].get_size()
    # y of each piece's top, 0 = the ground floor's top, negative = higher
    floor_tops = [-i * config["floor_step"] for i in range(len(floors))]
    roof_top = floor_tops[-1] + config["roof_base"] - roof.get_height()
    top = min(roof_top, floor_tops[-1])
    sprite = pygame.Surface((width, floor_height - top), pygame.SRCALPHA)
    for image, y in [*zip(floors, floor_tops), (roof, roof_top)]:
        sprite.blit(image, (0, y - top))
    return sprite


@cache
def game_sprite(age: str, level: int, door_side: str) -> pygame.Surface:
    """The sprite at its size in the world (see `game_size` in the recipes)."""
    config = recipes()
    sprite = compose(age, level, door_side)
    floor = _piece(piece_names(age, level, door_side)[0][0])
    scale_x = config["game_size"][0] / floor.get_width()
    scale_y = config["game_size"][1] / floor.get_height()
    size = (round(sprite.get_width() * scale_x), round(sprite.get_height() * scale_y))
    return pygame.transform.scale(sprite, size)


def fit_sprite(
    age: str, level: int, door_side: str, box: tuple[int, int]
) -> pygame.Surface:
    """The full-size sprite shrunk to fit `box` (never enlarged, aspect kept), on a transparent
    surface of the box's size with the foot at the bottom center."""
    sprite = compose(age, level, door_side)
    factor = min(1.0, box[0] / sprite.get_width(), box[1] / sprite.get_height())
    size = (round(sprite.get_width() * factor), round(sprite.get_height() * factor))
    result = pygame.Surface(box, pygame.SRCALPHA)
    result.blit(
        pygame.transform.scale(sprite, size),
        ((box[0] - size[0]) // 2, box[1] - size[1]),
    )
    return result
