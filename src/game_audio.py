from sound_manager import SoundManager


class GameAudioMixin:
    def play_music(self, sound_path) -> None:
        SoundManager.play_sound(0, sound_path, -1)

    def play_sfx(self, sound_path) -> None:
        SoundManager.play_sound(1, sound_path)

    def set_music_volume(self, volume: float) -> None:
        SoundManager.set_volume(0, volume)

    def set_sfx_volume(self, volume: float) -> None:
        SoundManager.set_volume(1, volume)

    def set_sfx_label(self, volume: float) -> None:
        self.set_volume_label(volume, self.panel_manager["audio_settings"]["sfx_volume_entry"])

    def set_music_label(self, volume: float) -> None:
        self.set_volume_label(volume, self.panel_manager["audio_settings"]["music_volume_entry"])

    def set_volume_label(self, volume: float, label) -> None:
        volume = max(0.0, min(1.0, volume))
        label.text.update_text("default", "%" + str(round(volume * 100)))