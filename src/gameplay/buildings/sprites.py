"""Building sprites composed from pack pieces by the recipes in config/buildings.yaml.

A sprite is cached per (age, level, door side, booster), so composing happens once per
combination, never per frame. `compose` builds the full-size sprite, `game_sprite` the one drawn
in the world. A booster (`booster=True`) uses the `boosters` recipes instead of the building
levels; its sprite has no door, so the door side makes no difference to it.

Every sprite the game draws (world and info panel) gets a thin outline, applied once when the
sprite is built and cached with it. It is drawn inside the sprite's own surface, on the silhouette's
outermost pixels, so size, anchor and click area stay what they were (see `outline`).
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


def level_count(booster: bool = False) -> int:
    """How many levels the recipes define (for the building ladder, or the booster's)."""
    return len(_level_recipes(booster))


def _level_recipes(booster: bool) -> list[dict]:
    config = recipes()
    return config["boosters"]["levels"] if booster else config["levels"]


def _age_prefixes(age: str, booster: bool) -> dict:
    config = recipes()
    return (config["boosters"] if booster else config)["ages"][age]


def checked_max_level(max_level: int) -> int:
    """`max_level` itself, if the recipes have a sprite for every level up to it."""
    if max_level > level_count():
        raise ValueError(
            f"max_building_level {max_level} is more than the {level_count()} levels "
            f"in {RECIPES_PATH.as_posix()}"
        )
    return max_level


def outline_settings() -> tuple[int, float]:
    """The outline's width in pixels (0 = none) and the factor its edge pixels' color is multiplied
    by (`outline` in the recipes)."""
    config = recipes()["outline"]
    width, factor = config["width"], config["darken"]
    if not isinstance(width, int) or isinstance(width, bool) or width < 0:
        raise ValueError(
            f"outline width in {RECIPES_PATH.as_posix()} must be a whole number, 0 or more"
        )
    if isinstance(factor, bool) or not isinstance(factor, (int, float)):
        raise ValueError(
            f"outline darken in {RECIPES_PATH.as_posix()} must be a number"
        )
    if not 0 < factor <= 1:
        raise ValueError(
            f"outline darken in {RECIPES_PATH.as_posix()} must be in (0, 1]"
        )
    return width, float(factor)


def _eroded(solid: pygame.Mask) -> pygame.Mask:
    """`solid` without the pixels that have a non-solid 4-neighbor (the surface's edge counts as
    non-solid)."""
    size = solid.get_size()
    result = solid
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        shifted = pygame.Mask(size)
        shifted.draw(solid, (dx, dy))
        result = result.overlap_mask(shifted, (0, 0))
    return result


def outline(sprite: pygame.Surface) -> pygame.Surface:
    """A copy of `sprite` with an outline that follows its alpha silhouette. The outline is the
    outermost `width` pixels of the silhouette (also where it touches the surface's edge),
    recolored to a darker shade of their own color (each channel times `darken`), so it stays
    part of the art instead of being black or gray. Alpha is kept, so the size, the anchor and the
    opaque area are exactly the sprite's. Width 0 returns the sprite unchanged. Built from masks
    and one blit, but still a pass over the sprite: only call it when a sprite is built, never
    per frame."""
    width, factor = outline_settings()
    if width == 0:
        return sprite
    core = pygame.mask.from_surface(sprite, 127)  # alpha 128 or more is solid
    for _ in range(width):
        core = _eroded(core)
    # Every visible pixel (soft edge included) that is not in the core is the outline.
    rim = pygame.mask.from_surface(sprite, 0)
    rim.erase(core, (0, 0))
    shade = round(255 * factor)
    darker = sprite.copy()
    darker.fill((shade, shade, shade, 255), special_flags=pygame.BLEND_RGBA_MULT)
    result = sprite.copy()
    rim.to_surface(result, setsurface=darker, unsetcolor=None)
    return result


def random_door_side() -> str:
    return choice(DOOR_SIDES)


def default_door_side(row: int, column: int) -> str:
    """A deterministic side for a building without a saved one (a save from before door sides)."""
    return DOOR_SIDES[(row + column) % 2]


def piece_names(
    age: str, level: int, door_side: str, booster: bool = False
) -> tuple[list[str], str]:
    """The floor piece names (bottom to top) and the roof piece name of one sprite."""
    assert door_side in DOOR_SIDES, door_side
    config = recipes()
    prefixes = _age_prefixes(age, booster)
    level_recipe = _level_recipes(booster)[level - 1]
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
    for booster in (False, True):
        for age in recipes()["ages"]:
            for level in range(1, level_count(booster) + 1):
                for side in DOOR_SIDES:
                    floors, roof = piece_names(age, level, side, booster)
                    names.update(floors, [roof])
    return names


def piece(name: str) -> pygame.Surface:
    return load_image(ImagePath(name, PIECES_FOLDER))


@cache
def compose(
    age: str, level: int, door_side: str, booster: bool = False
) -> pygame.Surface:
    """The full-size sprite: floors stacked and the roof on top, its foot at the bottom edge."""
    config = recipes()
    floor_names, roof_name = piece_names(age, level, door_side, booster)
    floors = [piece(name) for name in floor_names]
    roof = piece(roof_name)
    # y of each piece's top, 0 = a full-height (floor_size) ground floor's top, negative =
    # higher. A shorter piece (the ring) keeps its foot on the same line as the others.
    floor_tops = [
        floor_height_gap(image) - i * config["floor_step"]
        for i, image in enumerate(floors)
    ]
    roof_base = _age_prefixes(age, booster)["roof_base"]
    roof_top = floor_tops[-1] + roof_base - roof.get_height()
    top = min(roof_top, *floor_tops)
    pieces = [*zip(floors, floor_tops), (roof, roof_top)]
    # Some pieces are a pixel wider than the floors: the sprite fits the widest, pieces centered.
    width = max(image.get_width() for image, _ in pieces)
    sprite = pygame.Surface((width, config["floor_size"][1] - top), pygame.SRCALPHA)
    for image, y in pieces:
        sprite.blit(image, ((width - image.get_width()) // 2, y - top))
    return sprite


def floor_height_gap(image: pygame.Surface) -> int:
    """How much shorter than a full floor (`floor_size`) a floor piece is."""
    return recipes()["floor_size"][1] - image.get_height()


def world_size(sprite: pygame.Surface) -> tuple[int, int]:
    """A full-size sprite's size in the world: always `game_size` wide, and the height scaled by
    the same factor as a one-floor sprite's (75 / 89), so floors keep their proportions."""
    config = recipes()
    width, height = config["game_size"]
    return width, round(sprite.get_height() * height / config["floor_size"][1])


@cache
def game_sprite(
    age: str, level: int, door_side: str, booster: bool = False
) -> pygame.Surface:
    """The sprite at its size in the world (see `game_size` in the recipes)."""
    sprite = compose(age, level, door_side, booster)
    return outline(pygame.transform.scale(sprite, world_size(sprite)))


@cache
def tallest_world_height() -> int:
    """The height of the tallest sprite in the world, over every age and level (boosters too)."""
    # Heights come from the un-outlined sprites: reading a size must not outline all of them.
    return max(
        world_size(compose(age, level, "left", booster))[1]
        for booster in (False, True)
        for age in recipes()["ages"]
        for level in range(1, level_count(booster) + 1)
    )


@cache
def panel_sprite(
    age: str, level: int, door_side: str, box: tuple[int, int], booster: bool = False
) -> pygame.Surface:
    """The building as the info panel shows it: the board's own sprite, enlarged by one factor
    for every level (the tallest sprite just fits the box's height, so level growth shows like
    on the board), on a transparent surface of the box's size, centered, its roof tip at the
    top (every building hangs from the same line)."""
    world = world_size(compose(age, level, door_side, booster))
    factor = min(box[1] / tallest_world_height(), box[0] / recipes()["game_size"][0])
    size = (round(world[0] * factor), round(world[1] * factor))
    result = pygame.Surface(box, pygame.SRCALPHA)
    result.blit(
        # Scaled once from the full-size sprite (not the board's already scaled one), to the
        # board's proportions times the panel factor, so it stays as sharp as it can.
        outline(pygame.transform.scale(compose(age, level, door_side, booster), size)),
        ((box[0] - size[0]) // 2, 0),
    )
    return result
