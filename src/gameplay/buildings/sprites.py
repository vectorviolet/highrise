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


def piece(name: str) -> pygame.Surface:
    return load_image(ImagePath(name, PIECES_FOLDER))


@cache
def compose(age: str, level: int, door_side: str) -> pygame.Surface:
    """The full-size sprite: floors stacked and the roof on top, its foot at the bottom edge."""
    config = recipes()
    floor_names, roof_name = piece_names(age, level, door_side)
    floors = [piece(name) for name in floor_names]
    roof = piece(roof_name)
    # y of each piece's top, 0 = the ground floor's top, negative = higher
    floor_tops = [-i * config["floor_step"] for i in range(len(floors))]
    roof_base = config["ages"][age]["roof_base"]
    roof_top = floor_tops[-1] + roof_base - roof.get_height()
    top = min(roof_top, floor_tops[-1])
    pieces = [*zip(floors, floor_tops), (roof, roof_top)]
    # Some pieces are a pixel wider than the floors: the sprite fits the widest, pieces centered.
    width = max(image.get_width() for image, _ in pieces)
    sprite = pygame.Surface((width, config["floor_size"][1] - top), pygame.SRCALPHA)
    for image, y in pieces:
        sprite.blit(image, ((width - image.get_width()) // 2, y - top))
    return sprite


def world_size(sprite: pygame.Surface) -> tuple[int, int]:
    """A full-size sprite's size in the world: always `game_size` wide, and the height scaled by
    the same factor as a one-floor sprite's (75 / 89), so floors keep their proportions."""
    config = recipes()
    width, height = config["game_size"]
    return width, round(sprite.get_height() * height / config["floor_size"][1])


@cache
def game_sprite(age: str, level: int, door_side: str) -> pygame.Surface:
    """The sprite at its size in the world (see `game_size` in the recipes)."""
    sprite = compose(age, level, door_side)
    return pygame.transform.scale(sprite, world_size(sprite))


@cache
def tallest_world_height() -> int:
    """The height of the tallest sprite in the world, over every age and level."""
    return max(
        game_sprite(age, level, "left").get_height()
        for age in recipes()["ages"]
        for level in range(1, level_count() + 1)
    )


@cache
def panel_sprite(
    age: str, level: int, door_side: str, box: tuple[int, int]
) -> pygame.Surface:
    """The building as the info panel shows it: the board's own sprite, enlarged by one factor
    for every level (the tallest sprite just fits the box's height, so level growth shows like
    on the board), on a transparent surface of the box's size, centered, its roof tip at the
    top (every building hangs from the same line)."""
    world = game_sprite(age, level, door_side).get_size()
    factor = min(box[1] / tallest_world_height(), box[0] / recipes()["game_size"][0])
    size = (round(world[0] * factor), round(world[1] * factor))
    result = pygame.Surface(box, pygame.SRCALPHA)
    result.blit(
        # Scaled once from the full-size sprite (not the board's already scaled one), to the
        # board's proportions times the panel factor, so it stays as sharp as it can.
        pygame.transform.scale(compose(age, level, door_side), size),
        ((box[0] - size[0]) // 2, 0),
    )
    return result
