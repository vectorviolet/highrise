"""The sounds of the main actions: build (one per age), NEXT AGE and sell.

`action_sounds` in config/settings.yaml names a manifest sound (config/assets.yaml) for each,
so the owner can swap a sound, or give every age the same one, without touching code. Each plays
through `GameAudio.play_sfx`: a free channel of the SFX pool, at the master and SFX volumes,
leaving the music channel and the reserved channels alone.
"""

from dataclasses import dataclass

from gameplay.buildings.building import AGES
from pygamine import AssetManager, SoundPath


@dataclass(frozen=True)
class ActionSounds:
    build_by_age: dict[str, SoundPath]  # keyed by the age's name, as in AGES
    next_age: SoundPath
    sell: SoundPath

    @classmethod
    def from_config(cls, values: dict, assets: AssetManager) -> "ActionSounds":
        """Looks up the configured manifest keys; raises ValueError if an age has no
        build sound, or KeyError if a key is not in the manifest."""
        build = values["build"]
        missing = [age for age in AGES if age not in build]
        if missing:
            raise ValueError(f"action_sounds.build has no sound for: {missing}")
        return cls(
            build_by_age={age: assets.sound_path(build[age]) for age in AGES},
            next_age=assets.sound_path(values["next_age"]),
            sell=assets.sound_path(values["sell"]),
        )

    def build(self, age_number: int) -> SoundPath:
        """The build sound of the age with this number (0 is the first age)."""
        return self.build_by_age[AGES[age_number]]
