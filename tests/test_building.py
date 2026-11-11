from pygame import Vector2
import pytest

from gameplay.buildings.building import AGES, Building
from gameplay.tiles.tile import Tile


def make_building(level=1, age_number=0, row=1, col=1) -> Building:
    return Building(level, age_number, Tile(row, col), door_side="left", on_payout=None)


def test_speed_scales_with_level_and_age(assets):
    # speed = (level * 2 * (age_number + 1)) - 1
    assert make_building(level=1, age_number=0).speed == 1
    assert make_building(level=2, age_number=0).speed == 3
    assert make_building(level=1, age_number=1).speed == 3
    assert make_building(level=3, age_number=2).speed == 17


def test_sell_price_scales_with_level_and_age(assets):
    # sell_price = level * (age_number + 1) * 70
    assert make_building(level=1, age_number=0).sell_price == 70
    assert make_building(level=2, age_number=0).sell_price == 140
    assert make_building(level=1, age_number=3).sell_price == 280


def test_age_name_comes_from_the_ages_list(assets):
    for age_number, name in enumerate(AGES):
        assert make_building(age_number=age_number).age == name


def test_size_follows_the_composed_sprite_and_the_foot_stays_put(assets):
    # A one-floor sprite is 50x75 in the world; taller ones scale by the same factors.
    heights = [make_building(level=level).height for level in range(1, 12)]
    assert make_building(level=1).size == (50, 75)
    assert heights == sorted(heights)  # never shorter than the level before
    assert heights[3] > heights[2]  # level 4 adds a floor
    for level in range(1, 12):
        b = make_building(level=level)
        assert b.rect.width == 50
        assert (
            b.rect.bottom == b.tile.rect.y + 52
        )  # the foot is 52 px below the tile top


def test_payout_calls_on_payout_with_cooldown_times_speed(assets):
    b = make_building(level=2, age_number=0)  # speed == 3
    payouts = []
    b.on_payout = lambda building, amount: payouts.append((building, amount))

    b._payout()

    assert payouts == [(b, b.cooldown * b.speed)]


def test_payout_is_a_no_op_without_a_listener(assets):
    b = make_building()
    b.on_payout = None
    b._payout()  # must not raise


def test_level_up_moves_the_sacrificial_building_and_marks_it_for_destruction(assets):
    survivor = make_building(level=2, row=1, col=1)
    sacrificial = make_building(level=2, row=2, col=2)

    survivor.level_up(sacrificial)

    assert sacrificial.tile is survivor.tile
    assert sacrificial.should_destroy is True
    assert sacrificial.merge_target is survivor
    assert sacrificial.rigidbody.velocity != Vector2(0, 0)


@pytest.mark.parametrize(
    "velocity, position, arrived",
    [
        ((1, 0), (99, 50), False),
        ((1, 0), (100, 50), True),
        ((1, 0), (101, 50), True),
        ((-1, 0), (101, 50), False),
        ((-1, 0), (100, 50), True),
        ((-1, 0), (99, 50), True),
        ((0, 1), (50, 99), False),
        ((0, 1), (50, 100), True),
        ((0, -1), (50, 101), False),
        ((0, -1), (50, 100), True),
        ((1, -1), (100, 101), False),
        ((1, -1), (101, 99), True),
    ],
)
def test_arrival_requires_each_moving_axis_to_reach_or_pass_target(
    assets, velocity, position, arrived
):
    building = make_building()
    building.target_position = Vector2(100, 100)
    building.rect.topleft = position
    building.rigidbody.set_velocity(velocity)

    assert building.has_arrived() is arrived


def test_levels_seven_to_eleven_follow_the_same_income_and_price_curve(assets):
    # Placeholders until the owner tunes them: the formulas are not capped at level 6.
    for age_number in range(len(AGES)):
        for level in range(7, 12):
            b = make_building(level=level, age_number=age_number)
            assert b.speed == level * 2 * (age_number + 1) - 1
            assert b.sell_price == level * (age_number + 1) * 70


def test_boosted_income_keeps_the_cents_a_payout_cannot_pay(assets):
    b = make_building()

    paid = [b.boosted_income(2, 1.2) for _ in range(5)]

    assert paid == [2, 2, 3, 2, 3]  # 2.4 each: 12 in all
    assert sum(paid) == 12


def test_boosted_income_without_a_boost_is_the_amount(assets):
    b = make_building()

    assert [b.boosted_income(7, 1) for _ in range(3)] == [7, 7, 7]
