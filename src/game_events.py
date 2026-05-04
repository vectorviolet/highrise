import pygame
import webbrowser

from sound_manager import SoundManager


class GameEventsMixin:
    def handle_menu_events(self, event: pygame.event.Event) -> None:
        buttons = self.panel_manager["menu"]["menu"].buttons
        navigations = {
            "START":     "game",
            "SETTINGS":  "settings",
            "DEVELOPER": "developer",
            "EXIT":      "exit",
        }

        for label, panel in navigations.items():
            button = buttons[label]
            if (button.is_clicked(event, self.mouse.position) or
                    (event.type == pygame.KEYUP and event.key == pygame.K_SPACE) and button.state == "hover"):
                sound_path = self.go_back_sound_path if label == "EXIT" else self.click_sound_path
                self.play_sfx(sound_path)
                self.open_panel(panel)

    def handle_settings_events(self, event: pygame.event.Event) -> None:
        buttons = self.panel_manager["settings"]["menu"].buttons
        navigations = {
            "display_settings": "display_settings",
            "audio_settings":   "audio_settings",
            "game_settings":    "game_settings",
            "GO BACK":          "menu",
        }

        for label, panel in navigations.items():
            button = buttons[label]
            if (button.is_clicked(event, self.mouse.position) or
                    (event.type == pygame.KEYUP and event.key == pygame.K_SPACE) and button.state == "hover"):

                if label == "audio_settings":
                    self.old_music_volume = SoundManager.get_volume(0)
                    self.old_sfx_volume = SoundManager.get_volume(1)

                self.play_sfx(self.click_sound_path)
                self.open_panel(panel)

    def handle_display_settings_events(self, event: pygame.event.Event) -> None:
        if self.panel_manager["display_settings"]["go_back_button"].is_clicked(event, self.mouse.position):
            self.play_sfx(self.click_sound_path)
            self.open_panel("settings")

    def handle_audio_settings_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["audio_settings"]

        if panel["music_volume_plus_button"].is_clicked(event, self.mouse.position):
            new_vol = SoundManager.get_volume(0) + 0.1
            self.set_music_volume(new_vol); self.set_music_label(new_vol)
        elif panel["music_volume_minus_button"].is_clicked(event, self.mouse.position):
            new_vol = SoundManager.get_volume(0) - 0.1
            self.set_music_volume(new_vol); self.set_music_label(new_vol)
        elif panel["sfx_volume_plus_button"].is_clicked(event, self.mouse.position):
            new_vol = SoundManager.get_volume(1) + 0.1
            self.set_sfx_volume(new_vol); self.set_sfx_label(new_vol)
        elif panel["sfx_volume_minus_button"].is_clicked(event, self.mouse.position):
            new_vol = SoundManager.get_volume(1) - 0.1
            self.set_sfx_volume(new_vol); self.set_sfx_label(new_vol)
        elif panel["cancel_button"].is_clicked(event, self.mouse.position):
            self.set_music_volume(self.old_music_volume); self.set_music_label(self.old_music_volume)
            self.set_sfx_volume(self.old_sfx_volume);   self.set_sfx_label(self.old_sfx_volume)
            self.play_sfx(self.go_back_sound_path)
            self.open_panel("settings")
        elif panel["save_button"].is_clicked(event, self.mouse.position):
            self.save_audio_settings()
            self.play_sfx(self.go_back_sound_path)
            self.open_panel("settings")

    def handle_game_settings_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["game_settings"]
        if panel["delete_data_button"].is_clicked(event, self.mouse.position):
            self.delete_data(); self.load_data(); self.add_objects()
            self.play_sfx(self.click_sound_path); self.open_panel("menu")
        elif panel["go_back_button"].is_clicked(event, self.mouse.position):
            self.play_sfx(self.click_sound_path); self.open_panel("settings")

    def handle_developer_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["developer"]
        if panel["github"].is_clicked(event, self.mouse.position):
            self.play_sfx(self.click_sound_path)
            webbrowser.open("https://www.github.com/umutcanekinci/")
        elif panel["linkedin"].is_clicked(event, self.mouse.position):
            self.play_sfx(self.click_sound_path)
            webbrowser.open("https://www.linkedin.com/in/umutcanekinci/")
        elif panel["go_back_button"].is_clicked(event, self.mouse.position):
            self.play_sfx(self.click_sound_path); self.open_panel("menu")

    def handle_game_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["game"]

        if self.is_selection_mode:
            self.control_selecting_tile()

        if panel["info_panel"].active:
            if panel["sell_button"].is_clicked(event, self.mouse.position):
                self.buildings.remove(self.info_building)
                self.money += self.info_building.sell_price
                self.close_info_panel()
                self.play_sfx(self.go_back_sound_path)
                self.update_button_texts()
            elif panel["close_button"].is_clicked(event, self.mouse.position):
                self.close_info_panel()
                self.play_sfx(self.go_back_sound_path)
            return

        info_button = panel["selection_mode_button"]
        if info_button.is_clicked(event, self.mouse.position):
            self.is_selection_mode = not self.is_selection_mode
            info_button.set_state("on" if self.is_selection_mode else "off")
            self.play_sfx(self.click_sound_path)

        if self.is_selection_mode and event.type == pygame.MOUSEBUTTONUP:
            building = self.get_selected_building()
            if building:
                self.refresh_info_panel(building)
                self.open_info_panel()
                self.play_sfx(self.click_sound_path)

        if panel["expand_button"].is_clicked(event, self.mouse.position):
            self.expand()
        elif panel["build_button"].is_clicked(event, self.mouse.position):
            self.create_building()
        elif panel["next_age_button"].is_clicked(event, self.mouse.position):
            self.next_age()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                self.create_building()
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.move_buildings("right")
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.move_buildings("left")
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.move_buildings("up")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.move_buildings("down")