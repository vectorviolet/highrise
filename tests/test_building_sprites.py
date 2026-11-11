"""Building sprites composed from the recipes in config/buildings.yaml."""

from pathlib import Path

import pygame
import pytest
import yaml

from gameplay.buildings import sprites
from gameplay.buildings.boosters import BoosterConfig
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


def test_every_floor_piece_has_the_recipe_floor_size(assets):
    floor_size = tuple(sprites.recipes()["floor_size"])
    for age in AGES:
        for level in range(1, sprites.level_count() + 1):
            for side in sprites.DOOR_SIDES:
                for name in sprites.piece_names(age, level, side)[0]:
                    assert sprites.piece(name).get_size() == floor_size, name


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
                assert sprites.compose(age, level, side).get_width() in (65, 66)


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
    first = Building(4, 2, Tile(1, 1), door_side="left", on_payout=None)
    second = Building(4, 2, Tile(2, 2), door_side="left", on_payout=None)
    assert first.sprite is second.sprite  # no compositing per building


def test_every_sprite_is_as_wide_as_its_widest_piece(assets):
    # Sand and stone RoofStraight are a pixel wider than the floors: nothing is clipped.
    widest = {}
    for age in AGES:
        for level in range(1, sprites.level_count() + 1):
            floors, roof = sprites.piece_names(age, level, "left")
            width = max(sprites.piece(n).get_width() for n in [*floors, roof])
            assert sprites.compose(age, level, "left").get_width() == width
            widest[age] = max(widest.get(age, 0), width)
    assert widest["sand"] == widest["stone"] == 66
    assert widest["wood"] == widest["rock"] == 65


def test_a_one_floor_sprite_is_75_tall_in_every_age(assets):
    for age in AGES:
        for level in (1, 2, 3):
            assert sprites.game_sprite(age, level, "left").get_size() == (50, 75), age


def test_taller_sprites_scale_by_the_same_factor_and_keep_the_width(assets):
    for age in AGES:
        for level in range(1, sprites.level_count() + 1):
            full = sprites.compose(age, level, "left")
            assert sprites.game_sprite(age, level, "left").get_size() == (
                50,
                round(full.get_height() * 75 / 89),
            )


def covered(surface: pygame.Surface) -> pygame.Rect:
    """The bounding box of the opaque pixels."""
    return (
        pygame.mask.from_surface(surface)
        .get_bounding_rects()[0]
        .unionall(pygame.mask.from_surface(surface).get_bounding_rects())
    )


def test_panel_sprite_is_the_board_sprite_at_one_scale_for_every_level(assets):
    for box in [(60, 185), (66, 204), (75, 231)]:  # the info image at 100%, 110%, 125%
        factor = box[1] / sprites.tallest_world_height()
        for age in AGES:
            for side in sprites.DOOR_SIDES:
                for level in range(1, sprites.level_count() + 1):
                    shown = sprites.panel_sprite(age, level, side, box)
                    world = sprites.game_sprite(age, level, side)
                    assert shown.get_size() == box
                    bounds = covered(shown)
                    assert bounds.height == pytest.approx(
                        world.get_height() * factor, abs=6
                    )
                    assert bounds.width == pytest.approx(
                        world.get_width() * factor, abs=6
                    )
                    assert bounds.top <= 2  # the roof tip is at the top
                    assert abs(bounds.centerx - box[0] / 2) <= 2


def test_the_tallest_building_fills_the_panel_box_height(assets):
    box = (60, 185)
    tallest = max(
        covered(sprites.panel_sprite(age, 11, "left", box)).height for age in AGES
    )
    assert tallest == pytest.approx(box[1], abs=4)


def test_panel_sprite_has_the_boards_door_side(assets):
    box = (60, 185)
    left = pygame.image.tobytes(sprites.panel_sprite("rock", 5, "left", box), "RGBA")
    right = pygame.image.tobytes(sprites.panel_sprite("rock", 5, "right", box), "RGBA")
    assert left != right


def test_panel_sprite_is_cached(assets):
    assert sprites.panel_sprite("rock", 5, "right", (60, 185)) is sprites.panel_sprite(
        "rock", 5, "right", (60, 185)
    )


def test_new_buildings_get_a_random_side_and_a_given_side_is_kept(assets, monkeypatch):
    buildings = Buildings(boosters=BoosterConfig.load(AGES))
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


def rgb_close(color, expected, tolerance=1):
    return all(abs(a - b) <= tolerance for a, b in zip(color[:3], expected))


def square(size=8, inset=1, side=6, color=(200, 100, 50, 255)):
    """A transparent surface with one opaque square (side x side) at (inset, inset)."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (inset, inset, side, side))
    return surface


def test_the_outline_settings_are_a_width_and_a_darkening_factor(assets):
    assert sprites.outline_settings() == (1, 0.55)


@pytest.mark.parametrize("booster", [False, True])
def test_outlined_sprites_are_cached_and_keep_size_and_foot(assets, booster):
    for fetch in (
        lambda: sprites.game_sprite("stone", 3, "left", booster),
        lambda: sprites.panel_sprite("stone", 3, "left", (60, 185), booster),
    ):
        assert fetch() is fetch()
    full = sprites.compose("stone", 3, "left", booster)
    plain = pygame.transform.scale(full, sprites.world_size(full))
    outlined = sprites.game_sprite("stone", 3, "left", booster)
    assert outlined.get_size() == plain.get_size()
    # The outline recolors pixels but never adds or removes any: the alpha mask (so the click
    # area and the foot on the bottom row) is the plain sprite's.
    assert pixels(outlined)[3::4] == pixels(plain)[3::4]


@pytest.mark.parametrize("booster", [False, True])
def test_real_sprites_get_a_darker_but_colored_rim(assets, booster):
    full = sprites.compose("rock", 4, "right", booster)
    plain = pygame.transform.scale(full, sprites.world_size(full))
    outlined = sprites.game_sprite("rock", 4, "right", booster)
    changed = [
        (x, y)
        for x in range(plain.get_width())
        for y in range(plain.get_height())
        if outlined.get_at((x, y)) != plain.get_at((x, y))
    ]
    assert changed
    # Every changed pixel is darker (never brighter) and keeps its alpha.
    for pos in changed:
        assert sum(outlined.get_at(pos)[:3]) < sum(plain.get_at(pos)[:3])
        assert outlined.get_at(pos).a == plain.get_at(pos).a
    # Colored, not gray: some rim pixel keeps a clear hue (its channels differ).
    assert any(
        max(outlined.get_at(p)[:3]) - min(outlined.get_at(p)[:3]) > 15 for p in changed
    )


def test_outline_of_a_square_darkens_exactly_its_rim(assets):
    result = sprites.outline(square())  # solid 1..6 in x and y
    rim = {
        (x, y) for x in range(1, 7) for y in range(1, 7) if x in (1, 6) or y in (1, 6)
    }
    for x in range(8):
        for y in range(8):
            color = result.get_at((x, y))
            if (x, y) in rim:
                assert rgb_close(color, (110, 55, 27), 2) and color.a == 255, (x, y)
            elif 1 <= x <= 6 and 1 <= y <= 6:
                assert color == (200, 100, 50, 255), (x, y)
            else:
                assert color.a == 0, (x, y)


def test_outline_on_the_surface_edge_counts_as_a_rim(assets):
    result = sprites.outline(square(size=4, inset=0, side=4))  # fills the whole surface
    assert rgb_close(result.get_at((0, 0)), (110, 55, 27), 2)
    assert rgb_close(result.get_at((3, 1)), (110, 55, 27), 2)
    assert result.get_at((1, 1)) == (200, 100, 50, 255)
    assert result.get_at((2, 2)) == (200, 100, 50, 255)


def test_outline_width_two_is_two_pixels_deep(assets, monkeypatch):
    monkeypatch.setitem(sprites.recipes()["outline"], "width", 2)
    result = sprites.outline(square(size=10, inset=1, side=8))  # solid 1..8
    for pos in [(1, 4), (2, 4), (7, 4), (8, 4), (4, 1), (4, 2), (4, 7), (4, 8)]:
        assert rgb_close(result.get_at(pos), (110, 55, 27), 2), pos
    for pos in [(3, 4), (4, 4), (6, 4), (4, 3), (4, 6)]:
        assert result.get_at(pos) == (200, 100, 50, 255), pos
    assert result.get_at((0, 4)).a == 0


def test_the_panel_sprite_is_outlined_too(assets, monkeypatch):
    box = (60, 185)
    shown = sprites.panel_sprite("wood", 5, "left", box)
    monkeypatch.setitem(sprites.recipes()["outline"], "width", 0)
    plain = sprites.panel_sprite.__wrapped__("wood", 5, "left", box)  # not cached
    assert shown.get_size() == plain.get_size() == box
    assert pixels(shown)[3::4] == pixels(plain)[3::4]  # same alpha mask
    changed = [
        (x, y)
        for x in range(box[0])
        for y in range(box[1])
        if shown.get_at((x, y)) != plain.get_at((x, y))
    ]
    assert changed
    assert all(sum(shown.get_at(p)[:3]) < sum(plain.get_at(p)[:3]) for p in changed)
    center = (box[0] // 2, plain.get_bounding_rect().centery)
    assert shown.get_at(center) == plain.get_at(center)  # the inside is untouched


def test_outline_width_zero_returns_the_sprite_unchanged(assets, monkeypatch):
    surface = square()
    soft = pygame.Surface((4, 4), pygame.SRCALPHA)
    soft.fill((200, 100, 50, 60))  # alpha 1..127: the soft edge of a scaled sprite
    monkeypatch.setitem(sprites.recipes()["outline"], "width", 0)
    for source in (surface, soft):
        assert pixels(sprites.outline(source)) == pixels(source)


@pytest.mark.parametrize("width", [-1, 1.0, 1.5, True, "1", None])
def test_a_width_that_is_not_a_whole_number_is_rejected(assets, monkeypatch, width):
    monkeypatch.setitem(sprites.recipes()["outline"], "width", width)
    with pytest.raises(ValueError, match="outline width"):
        sprites.outline_settings()


@pytest.mark.parametrize("darken", [0, 1.5, True, "0.5"])
def test_bad_darken_is_rejected(assets, monkeypatch, darken):
    monkeypatch.setitem(sprites.recipes()["outline"], "darken", darken)
    with pytest.raises(ValueError, match="outline darken"):
        sprites.outline_settings()


def test_reading_the_tallest_height_does_not_outline_every_sprite(assets):
    sprites.tallest_world_height.cache_clear()
    sprites.game_sprite.cache_clear()
    sprites.tallest_world_height()
    assert sprites.game_sprite.cache_info().currsize == 0
