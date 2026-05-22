import pygame
import webbrowser


def _activate_on_click_or_space(button, event, mouse_position) -> bool:
    if button.is_clicked(event, mouse_position):
        return True
    if event.type == pygame.KEYUP and event.key in (pygame.K_SPACE, pygame.K_RETURN) and getattr(button, "focused", False):
        return True
    return False


class GameEventsMixin:
    def handle_menu_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["menu"]
        navigations = (
            ("start_button",     "game"),
            ("settings_button",  "settings"),
            ("developer_button", "developer"),
            ("exit_button",      "exit"),
        )
        for button_name, dest in navigations:
            button = panel[button_name]
            if _activate_on_click_or_space(button, event, self.mouse.position):
                sound_path = self.go_back_sound_path if dest == "exit" else self.click_sound_path
                self.audio.play_sfx(sound_path)
                self.open_panel(dest)

    def handle_settings_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["settings"]
        navigations = (
            ("display_settings_button", "display_settings"),
            ("audio_settings_button",   "audio_settings"),
            ("game_settings_button",    "game_settings"),
            ("settings_back_button",    "menu"),
        )
        for button_name, dest in navigations:
            button = panel[button_name]
            if _activate_on_click_or_space(button, event, self.mouse.position):
                if dest == "audio_settings":
                    self.old_music_volume = self.audio.music_volume()
                    self.old_sfx_volume = self.audio.sfx_volume()
                self.audio.play_sfx(self.click_sound_path)
                self.open_panel(dest)

    def handle_display_settings_events(self, event: pygame.event.Event) -> None:
        if self.panel_manager["display_settings"]["display_back_button"].is_clicked(event, self.mouse.position):
            self.audio.play_sfx(self.click_sound_path)
            self.open_panel("settings")

    def handle_audio_settings_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["audio_settings"]

        if panel["music_volume_plus_button"].is_clicked(event, self.mouse.position):
            new_vol = self.audio.music_volume() + 0.1
            self.audio.set_music_volume(new_vol); self.set_music_label(new_vol)
        elif panel["music_volume_minus_button"].is_clicked(event, self.mouse.position):
            new_vol = self.audio.music_volume() - 0.1
            self.audio.set_music_volume(new_vol); self.set_music_label(new_vol)
        elif panel["sfx_volume_plus_button"].is_clicked(event, self.mouse.position):
            new_vol = self.audio.sfx_volume() + 0.1
            self.audio.set_sfx_volume(new_vol); self.set_sfx_label(new_vol)
        elif panel["sfx_volume_minus_button"].is_clicked(event, self.mouse.position):
            new_vol = self.audio.sfx_volume() - 0.1
            self.audio.set_sfx_volume(new_vol); self.set_sfx_label(new_vol)
        elif panel["cancel_button"].is_clicked(event, self.mouse.position):
            self.audio.set_music_volume(self.old_music_volume); self.set_music_label(self.old_music_volume)
            self.audio.set_sfx_volume(self.old_sfx_volume);   self.set_sfx_label(self.old_sfx_volume)
            self.audio.play_sfx(self.go_back_sound_path)
            self.open_panel("settings")
        elif panel["save_button"].is_clicked(event, self.mouse.position):
            self.save_audio_settings()
            self.audio.play_sfx(self.go_back_sound_path)
            self.open_panel("settings")

    def handle_game_settings_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["game_settings"]
        if panel["delete_data_button"].is_clicked(event, self.mouse.position):
            self.delete_data(); self.load_data(); self.add_objects()
            self.audio.play_sfx(self.click_sound_path); self.open_panel("menu")
        elif panel["game_settings_back_button"].is_clicked(event, self.mouse.position):
            self.audio.play_sfx(self.click_sound_path); self.open_panel("settings")

    def handle_developer_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["developer"]
        if panel["github_button"].is_clicked(event, self.mouse.position):
            self.audio.play_sfx(self.click_sound_path)
            webbrowser.open("https://www.github.com/umutcanekinci/")
        elif panel["linkedin_button"].is_clicked(event, self.mouse.position):
            self.audio.play_sfx(self.click_sound_path)
            webbrowser.open("https://www.linkedin.com/in/umutcanekinci/")
        elif panel["developer_back_button"].is_clicked(event, self.mouse.position):
            self.audio.play_sfx(self.click_sound_path); self.open_panel("menu")

    def handle_game_events(self, event: pygame.event.Event) -> None:
        panel = self.panel_manager["game"]

        if self.tile_selector.is_active:
            self.tile_selector.update_selection()

        if panel["info_panel"].active:
            if panel["sell_button"].is_clicked(event, self.mouse.position):
                self.buildings.remove(self.info_panel.building)
                self.player.earn(self.info_panel.building.sell_price)
                self.info_panel.close()
                self.audio.play_sfx(self.go_back_sound_path)
                self.update_button_texts()
            elif panel["close_button"].is_clicked(event, self.mouse.position):
                self.info_panel.close()
                self.audio.play_sfx(self.go_back_sound_path)
            return

        info_button = panel["selection_mode_button"]
        if info_button.is_clicked(event, self.mouse.position):
            self.tile_selector.is_active = not self.tile_selector.is_active
            info_button.set_base_state("on" if self.tile_selector.is_active else "off")
            self.audio.play_sfx(self.click_sound_path)

        if self.tile_selector.is_active and event.type == pygame.MOUSEBUTTONUP:
            building = self.tile_selector.get_selected_building()
            if building:
                self.info_panel.refresh(building)
                self.info_panel.open()
                self.audio.play_sfx(self.click_sound_path)

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