"""Building sprites composed from the recipes in config/buildings.yaml."""

from pathlib import Path

import pygame
import pytest
import yaml

from gameplay.buildings import sprites
from gameplay.buildings.building import AGES, Building, Buildings
from gameplay.tiles.tile import Tile

ROOT = Path(__file__).resolve().parent.parent
PIECES = ROOT / "assets" / "images" / "buildings"


def pixels(surface: pygame.Surface) -> bytes:
    return pygame.image.tobytes(surface, "RGBA")


def test_every_piece_the_recipes_ask_for_exists_as_a_file():
    names = sprites.all_piece_names()
    assert names  # a recipe file that asks for nothing would pass the check below
    assert [n for n in sorted(names) if not (PIECES / f"{n}.png").is_file()] == []


def test_every_asset_piece_is_used_by_a_recipe():
    assert {p.stem for p in PIECES.glob("*.png")} == sprites.all_piece_names()


def test_recipes_cover_every_age_and_the_configured_max_level(assets):
    settings = yaml.safe_load(
        (ROOT / "config/settings.yaml").read_text(encoding="utf-8")
    )
    max_level = settings["gameplay"]["max_building_level"]
    assert max_level == 11
    assert sprites.level_count() == max_level
    assert set(sprites.recipes()["ages"]) == set(AGES)
    for age in AGES:
        for level in range(1, max_level + 1):
            for side in sprites.DOOR_SIDES:
                assert sprites.compose(age, level, side).get_width() == 65


def test_checked_max_level_rejects_a_level_without_a_recipe():
    assert sprites.checked_max_level(sprites.level_count()) == sprites.level_count()
    with pytest.raises(ValueError, match="levels"):
        sprites.checked_max_level(sprites.level_count() + 1)


def test_every_level_looks_different_from_the_one_before(assets):
    for age in AGES:
        looks = [
            pixels(sprites.compose(age, level, "left"))
            for level in range(1, sprites.level_count() + 1)
        ]
        assert len(set(looks)) == len(looks), age


def test_every_age_has_the_same_structure_at_each_level():
    ages = sprites.recipes()["ages"]
    for level in range(1, sprites.level_count() + 1):
        for side in sprites.DOOR_SIDES:
            structures = set()
            for age, prefixes in ages.items():
                floors, roof = sprites.piece_names(age, level, side)
                structures.add(
                    (
                        tuple(n.removeprefix(prefixes["floor"]) for n in floors),
                        roof.removeprefix(prefixes["roof"]),
                    )
                )
            assert len(structures) == 1, (level, side)


def test_door_side_mirrors_the_door_floor_and_leaves_symmetric_floors(assets):
    assert sprites.piece_names("wood", 5, "left")[0] == ["woodGateLeft", "woodWindows"]
    assert sprites.piece_names("wood", 5, "right")[0] == [
        "woodGateRight",
        "woodWindows",
    ]
    assert pixels(sprites.compose("wood", 5, "left")) != pixels(
        sprites.compose("wood", 5, "right")
    )


def test_the_pack_door_window_piece_has_its_door_on_the_right(assets):
    # The pack's DoorWindow has the door on the right face, so "left" is the mirror.
    assert sprites.piece_names("rock", 2, "left")[0] == ["rockDoorWindowMirror"]
    assert sprites.piece_names("rock", 2, "right")[0] == ["rockDoorWindow"]


def test_sprites_are_composed_once_per_age_level_and_side(assets):
    assert sprites.compose("sand", 4, "left") is sprites.compose("sand", 4, "left")
    assert sprites.game_sprite("sand", 4, "left") is sprites.game_sprite(
        "sand", 4, "left"
    )
    assert sprites.compose("sand", 4, "left") is not sprites.compose("sand", 4, "right")
    first = Building(4, 2, Tile(1, 1), on_payout=None)
    second = Building(4, 2, Tile(2, 2), on_payout=None)
    assert first.sprite is second.sprite  # no compositing per building


def test_game_sprite_is_the_one_floor_size_scaled_in_both_directions(assets):
    assert sprites.game_sprite("wood", 1, "left").get_size() == (50, 75)
    full = sprites.compose("wood", 11, "left")
    assert sprites.game_sprite("wood", 11, "left").get_size() == (
        50,
        round(full.get_height() * 75 / 89),
    )


def test_fit_sprite_keeps_the_aspect_and_stands_on_the_bottom_edge(assets):
    box = (65, 89)
    short = sprites.fit_sprite("wood", 1, "left", box)
    tall = sprites.fit_sprite("wood", 11, "left", box)
    assert short.get_size() == tall.get_size() == box
    full = sprites.compose("wood", 11, "left")
    # The tall sprite shrinks (never stretches): it is narrower than the box.
    columns = [
        x for x in range(box[0]) if any(tall.get_at((x, y)).a for y in range(box[1]))
    ]
    assert len(columns) == pytest.approx(box[0] * box[1] / full.get_height(), abs=2)
    assert any(tall.get_at((x, box[1] - 1)).a for x in range(box[0]))


def test_new_buildings_get_a_random_side_and_a_given_side_is_kept(assets, monkeypatch):
    buildings = Buildings()
    tile = Tile(1, 1)
    monkeypatch.setattr(sprites, "choice", lambda sides: sides[1])
    assert buildings.create(1, tile).door_side == "right"
    monkeypatch.setattr(sprites, "choice", lambda sides: sides[0])
    assert buildings.create(1, tile).door_side == "left"
    assert buildings.create(1, tile, door_side="right").door_side == "right"


def test_default_door_side_is_deterministic_and_uses_both_sides():
    assert sprites.default_door_side(1, 1) == sprites.default_door_side(1, 1)
    assert {sprites.default_door_side(r, c) for r in (1, 2) for c in (1, 2)} == set(
        sprites.DOOR_SIDES
    )
