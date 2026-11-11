"""Boosters: coverage shapes, the income they add, merging rules, age changes (issue #51).
The numbers come from `boosters` in config/settings.yaml, so these tests read them from the
buildings' own config instead of repeating them, except for the additive rule's worked example."""

import pytest

from gameplay.buildings import sprites
from gameplay.buildings.boosters import BoosterConfig
from gameplay.buildings.building import AGES, Building, Buildings
from gameplay.tilemap import Tilemap

MAX_LEVEL = 6


def make_grid(size=5) -> tuple[Buildings, Tilemap]:
    return Buildings(boosters=BoosterConfig.load(AGES)), Tilemap(
        size=size, max_size=size
    )


def place(
    buildings: Buildings,
    tilemap: Tilemap,
    row: int,
    col: int,
    *,
    level: int = 1,
    booster: bool = False,
) -> Building:
    b = buildings.create(level, tilemap[row - 1][col - 1], booster=booster)
    buildings.append(b)
    return b


def covered(buildings: Buildings, booster: Building, size: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(1, size + 1)
        for c in range(1, size + 1)
        if buildings.covers(booster, r, c)
    }


# ── coverage shapes ──────────────────────────────────────────────────────────

ALL_NINE = {(r, c) for r in (1, 2, 3) for c in (1, 2, 3)}


@pytest.mark.parametrize(
    ("age", "origin", "expected"),
    [
        # wood: the 4 orthogonal neighbors
        (0, (2, 2), {(1, 2), (3, 2), (2, 1), (2, 3)}),
        (0, (1, 1), {(1, 2), (2, 1)}),
        (0, (1, 2), {(1, 1), (1, 3), (2, 2)}),
        # rock: the 4 diagonals
        (1, (2, 2), {(1, 1), (1, 3), (3, 1), (3, 3)}),
        (1, (1, 1), {(2, 2)}),
        (1, (1, 2), {(2, 1), (2, 3)}),
        # sand: all 8 surrounding tiles
        (2, (2, 2), ALL_NINE - {(2, 2)}),
        (2, (3, 3), {(2, 2), (2, 3), (3, 2)}),
        (2, (1, 2), {(1, 1), (1, 3), (2, 1), (2, 2), (2, 3)}),
        # stone: its whole row and column
        (3, (2, 2), {(2, 1), (2, 3), (1, 2), (3, 2)}),
        (3, (1, 1), {(1, 2), (1, 3), (2, 1), (3, 1)}),
    ],
)
def test_coverage_shapes_per_age_at_the_edges_and_corners(age, origin, expected):
    buildings, tilemap = make_grid(3)
    buildings.age_number = age
    booster = place(buildings, tilemap, *origin, booster=True)

    assert covered(buildings, booster, 3) == expected


def test_stone_covers_its_whole_row_and_column_on_a_larger_board():
    buildings, tilemap = make_grid(5)
    buildings.age_number = 3
    booster = place(buildings, tilemap, 2, 4, booster=True)

    assert covered(buildings, booster, 5) == (
        {(2, c) for c in (1, 2, 3, 5)} | {(r, 4) for r in (1, 3, 4, 5)}
    )


def test_a_booster_never_covers_its_own_tile():
    buildings, tilemap = make_grid(3)
    for age in range(len(AGES)):
        buildings.age_number = age
        booster = place(buildings, tilemap, 2, 2, booster=True)
        assert not buildings.covers(booster, 2, 2)
        buildings.remove(booster)


def test_covers_is_only_for_boosters():
    buildings, tilemap = make_grid(3)
    plain = place(buildings, tilemap, 2, 2)

    with pytest.raises(AssertionError):
        buildings.covers(plain, 1, 2)


# ── income ───────────────────────────────────────────────────────────────────


def test_a_booster_earns_nothing_and_has_no_speed():
    buildings, tilemap = make_grid()
    paid = []
    buildings.on_payout = lambda _b, amount: paid.append(amount)
    booster = place(buildings, tilemap, 2, 2, booster=True)

    booster._payout()

    assert paid == []
    assert booster.speed == 0


def test_a_building_on_a_covered_tile_gets_the_boosters_multiplier():
    buildings, tilemap = make_grid()
    booster = place(buildings, tilemap, 2, 2, level=3, booster=True)
    beside = place(buildings, tilemap, 2, 3)
    far = place(buildings, tilemap, 5, 5)

    assert buildings.income_multiplier(beside) == pytest.approx(
        buildings.boosters.multiplier(3)
    )
    assert buildings.income_multiplier(far) == 1
    assert booster.booster_multiplier == buildings.boosters.multiplier(3)


def test_overlapping_boosters_add_their_bonuses():
    buildings, tilemap = make_grid()
    place(buildings, tilemap, 2, 2, level=1, booster=True)  # x1.1
    place(buildings, tilemap, 2, 4, level=2, booster=True)  # x1.2
    between = place(buildings, tilemap, 2, 3)

    # x1.1 and x1.2 make x1.3 (0.1 + 0.2 on top of 1), not x1.32
    assert buildings.income_multiplier(between) == pytest.approx(1.3)


def test_sliding_into_range_changes_the_income():
    buildings, tilemap = make_grid(3)
    place(buildings, tilemap, 1, 1, booster=True)  # wood: (1, 2) and (2, 1)
    building = place(buildings, tilemap, 1, 3)
    assert buildings.income_multiplier(building) == 1

    buildings.move("left", tilemap, MAX_LEVEL)  # the building stops at (1, 2)

    assert (building.tile.row_number, building.tile.column_number) == (1, 2)
    assert buildings.income_multiplier(building) > 1


def test_sliding_the_booster_away_ends_the_boost():
    buildings, tilemap = make_grid(3)
    booster = place(buildings, tilemap, 1, 2, booster=True)
    place(buildings, tilemap, 2, 1, level=2)  # blocks the row below: it can't slide
    building = place(buildings, tilemap, 2, 2)
    assert buildings.income_multiplier(building) > 1

    buildings.move("left", tilemap, MAX_LEVEL)  # the booster goes to (1, 1)

    assert (booster.tile.row_number, booster.tile.column_number) == (1, 1)
    assert (building.tile.row_number, building.tile.column_number) == (2, 2)
    assert buildings.income_multiplier(building) == 1


def test_a_merged_building_keeps_the_boost_of_its_tile():
    buildings, tilemap = make_grid(3)
    place(buildings, tilemap, 1, 1, booster=True)
    place(buildings, tilemap, 2, 2)
    place(buildings, tilemap, 2, 3)

    buildings.move(
        "left", tilemap, MAX_LEVEL
    )  # row 2 merges at (2, 1), under the booster
    buildings.finish_pending_merges()

    merged = next(b for b in buildings if not b.is_booster)
    assert merged.level == 2
    assert (merged.tile.row_number, merged.tile.column_number) == (2, 1)
    assert buildings.income_multiplier(merged) > 1


def test_a_booster_waiting_to_merge_is_not_counted_twice():
    buildings, tilemap = make_grid(3)
    survivor = place(buildings, tilemap, 1, 1, booster=True)
    sacrificial = place(buildings, tilemap, 1, 3, booster=True)
    building = place(buildings, tilemap, 2, 1)
    survivor.level_up(sacrificial)

    assert buildings.income_multiplier(building) == pytest.approx(
        survivor.booster_multiplier
    )


def test_next_age_changes_the_shape_and_so_the_income():
    buildings, tilemap = make_grid(3)
    place(buildings, tilemap, 2, 2, booster=True)
    place(buildings, tilemap, 1, 2)  # orthogonal to the booster
    place(buildings, tilemap, 1, 1)  # diagonal to it
    by_tile = {(b.tile.row_number, b.tile.column_number): b for b in buildings}
    assert buildings.income_multiplier(by_tile[(1, 2)]) > 1
    assert buildings.income_multiplier(by_tile[(1, 1)]) == 1

    buildings.set_age(1)  # rock: diagonals

    by_tile = {(b.tile.row_number, b.tile.column_number): b for b in buildings}
    assert buildings.income_multiplier(by_tile[(1, 2)]) == 1
    assert buildings.income_multiplier(by_tile[(1, 1)]) > 1


# ── merging ──────────────────────────────────────────────────────────────────


def test_two_boosters_of_the_same_level_merge_into_the_next_booster_level():
    buildings, tilemap = make_grid(3)
    place(buildings, tilemap, 1, 1, level=2, booster=True)
    place(buildings, tilemap, 1, 2, level=2, booster=True)

    buildings.move("left", tilemap, MAX_LEVEL)
    buildings.finish_pending_merges()

    (merged,) = buildings
    assert merged.is_booster
    assert merged.level == 3
    assert merged.booster_multiplier == buildings.boosters.multiplier(3)


def test_a_booster_never_merges_with_a_building_of_the_same_level():
    buildings, tilemap = make_grid(3)
    place(buildings, tilemap, 1, 1, level=1, booster=True)
    place(buildings, tilemap, 1, 2, level=1)

    buildings.move("left", tilemap, MAX_LEVEL)

    assert not any(b.should_destroy for b in buildings)
    assert len(buildings) == 2


def test_boosters_of_different_levels_do_not_merge():
    buildings, tilemap = make_grid(3)
    place(buildings, tilemap, 1, 1, level=1, booster=True)
    place(buildings, tilemap, 1, 2, level=2, booster=True)

    buildings.move("left", tilemap, MAX_LEVEL)

    assert not any(b.should_destroy for b in buildings)


def test_boosters_stop_merging_at_their_own_maximum_level():
    buildings, tilemap = make_grid(3)
    top = buildings.boosters.max_level
    place(buildings, tilemap, 1, 1, level=top, booster=True)
    place(buildings, tilemap, 1, 2, level=top, booster=True)

    # The building maximum (6) is above the booster's (5): the booster's own cap rules.
    buildings.move("left", tilemap, MAX_LEVEL)

    assert not any(b.should_destroy for b in buildings)


def test_a_building_may_reach_a_level_a_booster_cannot():
    buildings, tilemap = make_grid(3)
    top = buildings.boosters.max_level
    place(buildings, tilemap, 1, 1, level=top)
    place(buildings, tilemap, 1, 2, level=top)

    buildings.move("left", tilemap, MAX_LEVEL)

    assert any(b.should_destroy for b in buildings)


def test_boosters_slide_with_the_buildings():
    buildings, tilemap = make_grid(3)
    booster = place(buildings, tilemap, 1, 3, booster=True)
    building = place(buildings, tilemap, 2, 3)

    buildings.move("left", tilemap, MAX_LEVEL)

    assert booster.tile.column_number == 1
    assert building.tile.column_number == 1


# ── ages and prices ──────────────────────────────────────────────────────────


def test_next_age_converts_a_booster_to_the_new_age_and_keeps_its_level():
    buildings, tilemap = make_grid(3)
    place(buildings, tilemap, 2, 2, level=3, booster=True)

    buildings.set_age(2)

    (booster,) = buildings
    assert booster.is_booster
    assert (booster.age, booster.level) == ("sand", 3)
    assert booster.booster_multiplier == buildings.boosters.multiplier(3)
    assert booster.on_payout is None


def test_the_booster_price_follows_the_age():
    buildings, _ = make_grid(3)
    prices = []
    for age in range(len(AGES)):
        buildings.age_number = age
        prices.append(buildings.get_booster_cost())

    assert prices == [buildings.boosters.price[age] for age in AGES]
    assert prices == sorted(prices)


# ── sprites ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("age", AGES)
def test_the_booster_look_grows_over_its_levels(age):
    heights = [
        sprites.game_sprite(age, level, "left", True).get_height()
        for level in range(1, sprites.level_count(booster=True) + 1)
    ]

    assert heights == sorted(heights)
    assert heights[-1] > heights[0]


def test_a_booster_has_as_many_looks_as_multipliers():
    assert sprites.level_count(booster=True) == BoosterConfig.load(AGES).max_level


def test_the_ring_keeps_its_foot_on_the_same_line_as_a_full_floor():
    ring = sprites.compose("wood", 1, "left", True)
    house = sprites.compose("wood", 1, "left")

    def lowest_opaque_row(surface) -> int:
        return max(
            y
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a > 0
        )

    # Both sprites end at their bottom edge: the ring's piece is 13 pixels shorter, not lower.
    assert lowest_opaque_row(ring) == ring.get_height() - 1
    assert lowest_opaque_row(house) == house.get_height() - 1


# ── config ───────────────────────────────────────────────────────────────────


def _config(**changes) -> dict:
    data = {
        "price": dict.fromkeys(AGES, 100),
        "multipliers": [1.1, 1.2],
        "shapes": dict.fromkeys(AGES, "around"),
        "placed_highlight_ms": 1500,
    }
    data.update(changes)
    return data


def test_a_config_without_a_price_for_an_age_is_refused():
    with pytest.raises(ValueError, match="price and shape"):
        BoosterConfig.from_dict(_config(price={"wood": 1}), AGES, 2)


def test_an_unknown_shape_is_refused():
    with pytest.raises(ValueError, match="unknown shape"):
        BoosterConfig.from_dict(_config(shapes=dict.fromkeys(AGES, "spiral")), AGES, 2)


def test_a_multiplier_that_does_not_boost_is_refused():
    with pytest.raises(ValueError, match="above 1"):
        BoosterConfig.from_dict(_config(multipliers=[0.9]), AGES, 1)


def test_more_multipliers_than_booster_looks_is_refused():
    with pytest.raises(ValueError, match="6 multipliers.*5 booster levels"):
        BoosterConfig.from_dict(_config(multipliers=[1.1] * 6), AGES, 5)


def test_fewer_multipliers_than_booster_looks_is_refused():
    with pytest.raises(ValueError, match="booster levels"):
        BoosterConfig.from_dict(_config(), AGES, 5)


def test_a_booster_level_outside_the_multipliers_fails_loudly():
    config = BoosterConfig.load(AGES)

    for level in (0, config.max_level + 1):
        with pytest.raises(AssertionError):
            config.multiplier(level)


def test_a_booster_has_no_payout_timer(monkeypatch):
    scheduled = []
    monkeypatch.setattr(
        Building, "invoke_repeating", lambda self, *a, **k: scheduled.append(self)
    )
    buildings, tilemap = make_grid(3)
    buildings.on_payout = lambda _b, _amount: None

    booster = place(buildings, tilemap, 1, 1, booster=True)
    building = place(buildings, tilemap, 1, 2)

    assert scheduled == [building]
    assert booster not in scheduled


def test_held_back_cents_are_carried_into_a_merged_building():
    buildings, tilemap = make_grid(3)
    first = place(buildings, tilemap, 1, 1)
    second = place(buildings, tilemap, 1, 2)
    first.income_fraction, second.income_fraction = 0.25, 0.5

    buildings.move("left", tilemap, MAX_LEVEL)
    buildings.finish_pending_merges()

    (merged,) = buildings
    assert merged.income_fraction == pytest.approx(0.75)


def test_held_back_cents_survive_a_next_age():
    buildings, tilemap = make_grid(3)
    building = place(buildings, tilemap, 1, 1)
    building.income_fraction = 0.4

    buildings.set_age(1)

    assert buildings[0].income_fraction == pytest.approx(0.4)


def test_the_booster_list_follows_the_collection():
    buildings, tilemap = make_grid(3)
    booster = place(buildings, tilemap, 2, 2, booster=True)
    beside = place(buildings, tilemap, 2, 3)
    assert buildings.income_multiplier(beside) > 1

    buildings.remove(booster)
    assert buildings.income_multiplier(beside) == 1
    buildings.append(booster)
    assert buildings.income_multiplier(beside) > 1
    buildings.set_age(1)  # replaces every building in place: the diagonal shape
    assert buildings.income_multiplier(buildings[1]) == 1


def test_a_price_that_is_not_a_positive_integer_is_refused():
    for bad in (0, -5, 2.5, "100", True, None):
        price = {**dict.fromkeys(AGES, 100), "wood": bad}
        with pytest.raises(ValueError, match="positive integer"):
            BoosterConfig.from_dict(_config(price=price), AGES, 2)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), "1.5", None, True, 1])
def test_a_multiplier_that_is_not_a_finite_number_above_1_is_refused(bad):
    with pytest.raises(ValueError, match="finite numbers above 1"):
        BoosterConfig.from_dict(_config(multipliers=[1.1, bad]), AGES, 2)


def test_the_placed_highlight_time_must_be_a_whole_number_of_ms():
    for bad in (-1, 1.5, "1500", None):
        with pytest.raises(ValueError, match="placed_highlight_ms"):
            BoosterConfig.from_dict(_config(placed_highlight_ms=bad), AGES, 2)
