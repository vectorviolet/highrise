from pygame import mixer

class SoundManager:
    @staticmethod
    def play_sound(channel: int, sound_path, volume: float, loops=0) -> None:
        mixer.Channel(channel).play(mixer.Sound(sound_path), loops)
        SoundManager.set_volume(channel, volume)

    @staticmethod
    def set_volume(channel: int, volume: float) -> None:
        mixer.Channel(channel).set_volume(max(0.0, min(1.0, volume)))
