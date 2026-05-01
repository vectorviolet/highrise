#-# Import Packages #-#
import pygame
from default.sound_manager import SoundManager
from pygame_core.asset_path import AssetPath, FontPath, SoundPath
from pygame_core.color import White
from default.object import Object
from default.button import Button, MenuButton

#-# Menu Class #-#
class Menu(pygame.Surface):

    def __init__(
            self,
            title_image_path: AssetPath,
            title_text: str,
            title_text_size: int,
            title_text_color: tuple,
            title_font_path: FontPath,
            panel_image_path: AssetPath,

            button_size: tuple,
            button_color: tuple,
            button_selected_color,
            button_texts: tuple,
            button_text_size: int,
            button_text_color: tuple,
            button_selected_text_color: tuple,
            button_text_font_path: str,

            screen_size: tuple,
            panel_height: tuple = None,
            sfx_volume: int = 100

            ) -> None:

        self.sfx_volume = sfx_volume
        space = 20
        button_additional_size = 15
        self.buttonCount = len(button_texts)

        self.titleSize = button_size[0] + space * 2, 70
        self.panelSize = button_size[0] + space * 2, button_size[1] * self.buttonCount + (self.buttonCount + 3) * space

        if panel_height:

            self.panelSize = self.panelSize[0], panel_height

        size = self.titleSize[0], self.titleSize[1] + self.panelSize[1] - space/2

        self.position = (screen_size[0] - size[0]) / 2, (screen_size[1] - size[1]) / 2
        self.panelPosition = self.position[0], self.position[1] + self.titleSize[1] - space/2

        self.switch_up_sound_path = SoundPath("switchUp")
        self.switch_down_sound_path = SoundPath("switchDown")

        self.title = Button(self.position, self.titleSize, {"Normal" : title_image_path}, title_text, "", title_text_size, title_text_color, White, title_font_path)

        self.panel = Object(self.panelPosition, self.panelSize, {"Normal" : panel_image_path})

        self.buttons = {}

        if self.buttonCount:

            button_selected_size = button_size[0], button_size[1] + button_additional_size

            for i in range(self.buttonCount):
                button_position = pygame.math.Vector2(space, space * (i+3/2) + button_size[1] * i)
                button_screen_position = button_position + self.panelPosition

                self.buttons[button_texts[i]] = MenuButton(button_color, button_screen_position, button_selected_color, button_texts[i], button_texts[i], button_text_color, button_selected_text_color
                                                           , button_text_size, button_text_font_path, button_size, button_selected_size)

            list(self.buttons.values())[0].set_status("Selected")

        super().__init__(size, pygame.SRCALPHA)

    def handle_event(self, event, mouse_position) -> None:
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons.values()):
                if button.is_mouse_over(mouse_position) and button.status != "Selected":
                    for j, button2 in enumerate(self.buttons.values()):
                        if button2.status == "Selected":
                            if j > i:
                                SoundManager.play_sound(1, self.switch_down_sound_path, self.sfx_volume)
                            else:
                                SoundManager.play_sound(1, self.switch_up_sound_path, self.sfx_volume)

                            button.set_status("Selected")
                            button2.set_status("Unselected")
                            break

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                for i, button in enumerate(self.buttons.values()):
                    if button.status == "Selected" and i != 0:
                        SoundManager.play_sound(1, self.switch_up_sound_path, self.sfx_volume)
                        self.buttons[list(self.buttons.keys())[i-1]].set_status("Selected")
                        button.set_status("Unselected")
                        break

            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                for i, button in enumerate(self.buttons.values()):
                    if button.status == "Selected" and i != len(self.buttons) - 1:
                        SoundManager.play_sound(1, self.switch_down_sound_path, self.sfx_volume)
                        self.buttons[list(self.buttons.keys())[i+1]].set_status("Selected")
                        button.set_status("Unselected")
                        break

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self, self.position)
        self.title.draw(surface)
        self.panel.draw(surface)

        for button in self.buttons.values():
            button.draw(surface)
