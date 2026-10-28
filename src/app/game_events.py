from typing import TYPE_CHECKING, Any

import pygame
import webbrowser

# Game-panel keys that move every building one step (KEYUP).
MOVE_KEYS = {
    pygame.K_RIGHT: "right",
    pygame.K_d: "right",
    pygame.K_LEFT: "left",
    pygame.K_a: "left",
    pygame.K_UP: "up",
    pygame.K_w: "up",
    pygame.K_DOWN: "down",
    pygame.K_s: "down",
}

# Audio-settings volume buttons: (button name, channel, volume change).
MUSIC_STEPPERS = (
    ("music_volume_plus_button", "music", 0.1),
    ("music_volume_minus_button", "music", -0.1),
)
SFX_STEPPERS = (
    ("sfx_volume_plus_button", "sfx", 0.1),
    ("sfx_volume_minus_button", "sfx", -0.1),
)


class GameEventsMixin:
    if TYPE_CHECKING:
        # Attributes / methods supplied by the host class (Game).
        def __getattr__(self, name: str) -> Any: ...

    def _activate(self, button, event) -> bool:
        """True when the button was activated (click or focused-Space/Enter).
        Plays the button's `on_click_sound` (or the default click) on success."""
        activated = button.is_clicked(event, self.mouse.position) or (
            event.type == pygame.KEYUP
            and event.key in (pygame.K_SPACE, pygame.K_RETURN)
            and getattr(button, "focused", False)
        )
        if activated:
            sound = getattr(button, "on_click_sound", None) or self.click_sound_path
            if sound is not None:
                self.audio.play_sfx(str(sound))
        return activated

    def handle_menu_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["menu"]
        if self._activate(panel["play_button"], event):
            self.play()
            return
        navigations = (
            ("settings_button", "settings"),
            ("developer_button", "developer"),
            ("exit_button", "exit"),
        )
        for button_name, dest in navigations:
            if self._activate(panel[button_name], event):
                self.open_panel(dest)

    def handle_play_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["play"]
        if self._activate(panel["new_game_button"], event):
            self.new_game()
        elif self._activate(panel["continue_button"], event):
            self.open_panel("game")
        elif self._activate(panel["play_back_button"], event):
            self.open_panel("menu")

    def handle_settings_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["settings"]
        navigations = (
            ("display_settings_button", "display_settings"),
            ("audio_settings_button", "audio_settings"),
            ("game_settings_button", "game_settings"),
            ("settings_back_button", "menu"),
        )
        for button_name, dest in navigations:
            if self._activate(panel[button_name], event):
                if dest == "audio_settings":
                    self._snapshot_audio_settings()
                self.open_panel(dest)

    def handle_display_settings_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["display_settings"]
        # Steppers use raw is_clicked: no click sound, no keyboard activation.
        steppers = (
            ("window_mode_minus_button", self._step_window_mode, -1),
            ("window_mode_plus_button", self._step_window_mode, 1),
            ("window_size_minus_button", self._step_resolution, -1),
            ("window_size_plus_button", self._step_resolution, 1),
        )
        for button_name, step, delta in steppers:
            if panel[button_name].is_clicked(event, self.mouse.position):
                step(delta)
                return
        if self._activate(panel["display_back_button"], event):
            self.open_panel("settings")

    def _step_window_mode(self, delta: int) -> None:
        self.cycle_window_mode(delta)
        self.set_window_mode_label()
        self.set_window_size_label()

    def _step_resolution(self, delta: int) -> None:
        self.cycle_resolution(delta)
        self.set_window_size_label()

    def handle_audio_settings_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["audio_settings"]
        # Steppers use raw is_clicked: no click sound, no keyboard activation.
        # The music controls are hidden (and ignored) when there's no music.
        has_music = self.background_music_sound_path is not None
        steppers = (MUSIC_STEPPERS if has_music else ()) + SFX_STEPPERS
        for button_name, channel, delta in steppers:
            if panel[button_name].is_clicked(event, self.mouse.position):
                self._step_volume(channel, delta)
                return
        if self._activate(panel["cancel_button"], event):
            self._revert_audio_settings()
            self.open_panel("settings")
        elif self._activate(panel["save_button"], event):
            self.save_audio_settings()
            self.open_panel("settings")

    def _step_volume(self, channel: str, delta: float) -> None:
        """Changes the "music" or "sfx" volume by `delta` and updates its label."""
        volume = getattr(self.audio, f"{channel}_volume")() + delta
        getattr(self.audio, f"set_{channel}_volume")(volume)
        getattr(self, f"set_{channel}_label")(volume)

    def _snapshot_audio_settings(self) -> None:
        """Remembers the volumes so Cancel or Escape can restore them."""
        self.old_music_volume = self.audio.music_volume()
        self.old_sfx_volume = self.audio.sfx_volume()

    def _revert_audio_settings(self) -> None:
        """Restores the volumes from the last snapshot, with their labels."""
        self.audio.set_music_volume(self.old_music_volume)
        self.set_music_label(self.old_music_volume)
        self.audio.set_sfx_volume(self.old_sfx_volume)
        self.set_sfx_label(self.old_sfx_volume)

    def handle_game_settings_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["game_settings"]
        if self._activate(panel["game_settings_back_button"], event):
            self.open_panel("settings")

    def handle_developer_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["developer"]
        if self._activate(panel["github_button"], event):
            webbrowser.open("https://www.github.com/umutcanekinci/")
        elif self._activate(panel["itch_button"], event):
            webbrowser.open("https://umutcanekinci.itch.io/")
        elif self._activate(panel["developer_back_button"], event):
            self.open_panel("menu")

    def handle_game_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["game"]

        if self.tile_selector.is_active:
            self.tile_selector.update_selection()

        # While the info panel is open it owns the input.
        if panel["info_panel"].active:
            self._handle_info_panel_event(panel, event)
            return

        if self._activate(panel["selection_mode_button"], event):
            self._toggle_selection_mode(panel["selection_mode_button"])

        if self.tile_selector.is_active and event.type == pygame.MOUSEBUTTONUP:
            self._pick_tile()

        self._handle_toolbar(panel, event)

        if event.type == pygame.KEYUP:
            self._handle_move_keys(event.key)

    def _handle_info_panel_event(self, panel, event: pygame.event.Event) -> None:
        if self._activate(panel["sell_button"], event):
            self.buildings.remove(self.info_panel.building)
            self.player.earn(self.info_panel.building.sell_price)
            self.info_panel.close()
            self.update_button_texts()
        elif self._activate(panel["close_button"], event):
            self.info_panel.close()

    def _toggle_selection_mode(self, button) -> None:
        self.tile_selector.is_active = not self.tile_selector.is_active
        button.set_base_state("on" if self.tile_selector.is_active else "off")

    def _pick_tile(self) -> None:
        """Opens the info panel for the building under the mouse, if any."""
        building = self.tile_selector.get_selected_building()
        if building:
            self.info_panel.refresh(building)
            self.info_panel.open()
            self.audio.play_sfx(str(self.click_sound_path))

    def _handle_toolbar(self, panel, event: pygame.event.Event) -> None:
        # expand/build/next_age call methods that play their own sfx, so
        # these use raw is_clicked (not _activate) to avoid double-playing.
        if panel["expand_button"].is_clicked(event, self.mouse.position):
            self.expand()
        elif panel["build_button"].is_clicked(event, self.mouse.position):
            self.create_building()
        elif panel["next_age_button"].is_clicked(event, self.mouse.position):
            self.next_age()

    def _handle_move_keys(self, key: int) -> None:
        """Space builds; the arrow keys and WASD move the buildings."""
        if key == pygame.K_SPACE:
            self.create_building()
        elif key in MOVE_KEYS:
            self.move_buildings(MOVE_KEYS[key])
