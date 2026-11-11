"""The sell effect: a burst spawns, ages, is drawn and is dropped when over."""

import random
from pathlib import Path

import pygame
import pytest
import yaml

from ui.dust_effect import DustBursts, DustConfig


def _values() -> dict:
    return yaml.safe_load(Path("config/settings.yaml").read_text())["sell_effect"]


@pytest.fixture
def effect() -> DustBursts:
    return DustBursts(DustConfig.from_dict(_values()), random.Random(1))


RECT = pygame.Rect(300, 200, 50, 75)


def test_a_sale_spawns_a_burst_of_puffs_and_chips_over_the_building(effect):
    effect.spawn(RECT, 1000)

    (burst,) = effect.bursts
    cfg = effect.config
    assert burst.born_ms == 1000
    assert sum(not p.is_debris for p in burst.particles) == cfg.dust_count
    assert sum(p.is_debris for p in burst.particles) == cfg.debris_count
    assert all(RECT.inflate(1, 1).collidepoint(p.origin) for p in burst.particles)


def test_a_burst_is_removed_once_its_life_is_over(effect):
    effect.spawn(RECT, 1000)
    life = effect.config.lifetime_ms

    effect.update(1000 + life - 1)
    assert len(effect.bursts) == 1
    effect.update(1000 + life)
    assert effect.bursts == []


def test_drawing_paints_pixels_while_alive_and_none_when_over(effect):
    surface = pygame.Surface((600, 500), pygame.SRCALPHA)
    effect.spawn(RECT, 0)

    effect.draw(surface, effect.config.lifetime_ms // 4)
    assert pygame.mask.from_surface(surface).count() > 0

    surface.fill((0, 0, 0, 0))
    effect.draw(surface, effect.config.lifetime_ms)
    assert pygame.mask.from_surface(surface).count() == 0


def test_chips_fall_and_puffs_drift_up(effect):
    effect.spawn(RECT, 0)
    puff = next(p for p in effect.bursts[0].particles if not p.is_debris)
    chip = next(p for p in effect.bursts[0].particles if p.is_debris)

    assert effect.position(puff, 1.0).y < puff.origin.y
    # A chip with no lift ends below where it started: gravity wins.
    still = type(chip)(chip.origin, 0, 0, chip.size, chip.color, True)
    assert effect.position(still, 1.0).y > still.origin.y


def test_drawing_reuses_cached_pictures_instead_of_making_new_ones(effect):
    surface = pygame.Surface((600, 500), pygame.SRCALPHA)
    effect.spawn(RECT, 0)
    effect.draw(surface, 100)
    cached = dict(effect._images)

    effect.draw(surface, 100)

    assert all(effect._images[k] is v for k, v in cached.items())
    assert len(effect._images) == len(cached)


def test_the_oldest_bursts_are_dropped_beyond_max_bursts():
    values = _values() | {"max_bursts": 2}
    effect = DustBursts(DustConfig.from_dict(values), random.Random(1))

    for now in (0, 10, 20):
        effect.spawn(RECT, now)

    assert [b.born_ms for b in effect.bursts] == [10, 20]


def test_clear_removes_every_burst(effect):
    effect.spawn(RECT, 0)
    effect.clear()
    assert effect.bursts == []


@pytest.mark.parametrize(
    "change",
    [
        {"lifetime_ms": 0},
        {"max_bursts": 0},
        {"dust_radius": [0, 5]},
        {"debris_size": [6, 3]},
        {"debris_colors": []},
    ],
)
def test_a_bad_config_is_rejected(change):
    with pytest.raises(ValueError):
        DustConfig.from_dict(_values() | change)
