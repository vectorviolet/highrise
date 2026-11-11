"""The sounds of build, NEXT AGE and sell: the config lookup per action and age, and that they
play on free SFX channels at the master and SFX volumes."""

from pathlib import Path

import pygame
import pytest
import yaml

from app.action_sounds import ActionSounds
from gameplay.buildings.building import AGES
from pygamine import GameAudio, RESERVED_CHANNELS


def _config() -> dict:
    return yaml.safe_load(Path("config/settings.yaml").read_text())["action_sounds"]


@pytest.fixture
def sounds(assets) -> ActionSounds:
    return ActionSounds.from_config(_config(), assets)


def test_build_looks_up_the_sound_of_each_age_from_the_config(assets, sounds):
    config = _config()["build"]
    for number, age in enumerate(AGES):
        assert sounds.build(number) == assets.sound_path(config[age])


def test_each_age_gets_the_sound_configured_for_it(assets):
    config = _config()
    config["build"] = dict(zip(AGES, ("build_wood", "build_rock", "sell", "next_age")))

    custom = ActionSounds.from_config(config, assets)

    for number, age in enumerate(AGES):
        assert custom.build(number) == assets.sound_path(config["build"][age])


def test_next_age_and_sell_have_their_own_sounds(assets, sounds):
    config = _config()
    assert sounds.next_age == assets.sound_path(config["next_age"])
    assert sounds.sell == assets.sound_path(config["sell"])
    own = {sounds.next_age, sounds.sell, *sounds.build_by_age.values()}
    assert assets.sound_path("click") not in own  # not the UI click


def test_the_config_can_give_every_age_the_same_build_sound(assets):
    config = _config()
    config["build"] = dict.fromkeys(AGES, "build_wood")

    shared = ActionSounds.from_config(config, assets)

    assert {shared.build(n) for n in range(len(AGES))} == {
        assets.sound_path("build_wood")
    }


def test_an_age_without_a_build_sound_is_rejected(assets):
    config = _config()
    del config["build"]["sand"]
    with pytest.raises(ValueError, match="sand"):
        ActionSounds.from_config(config, assets)


def test_an_unknown_manifest_key_is_rejected(assets):
    config = _config()
    config["sell"] = "no_such_sound"
    with pytest.raises(KeyError):
        ActionSounds.from_config(config, assets)


def test_the_action_sounds_play_on_a_pool_channel_at_master_times_sfx_volume(
    sounds, monkeypatch
):
    monkeypatch.setattr(GameAudio, "_master_volume", 0.5)
    monkeypatch.setattr(GameAudio, "_sfx_volume", 0.4)
    audio = GameAudio()
    for path in (sounds.build(0), sounds.next_age, sounds.sell):
        channel = audio.play_sfx(path)
        assert channel is not None
        assert channel.get_busy()
        assert channel.get_volume() == pytest.approx(0.2, abs=0.01)
    # The music and reserved channels are left alone.
    assert not any(pygame.mixer.Channel(i).get_busy() for i in range(RESERVED_CHANNELS))
    pygame.mixer.stop()
