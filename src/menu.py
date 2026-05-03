#-# Import Packages #-#
import pygame

from sound_manager import SoundManager
from pygame_core.asset_path import AssetPath, FontPath, SoundPath
from object import Object
from button import Button

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
            button_image: str,
            button_hover_image: str,
            button_texts: tuple,
            button_text_size: int,
            button_text_color: tuple,
            button_selected_text_color: tuple,
            button_font_key: str,

            screen_size: tuple,
            button_factory,
            *,
            panel_height: tuple = None,
            ) -> None:

        space = 20
        self.buttonCount = len(button_texts)

        self.titleSize = button_size[0] + space * 2, 70
        self.panelSize = button_size[0] + space * 2, button_size[1] * self.buttonCount + (self.buttonCount + 3) * space

        if panel_height:
            self.panelSize = self.panelSize[0], panel_height

        size = self.titleSize[0], self.titleSize[1] + self.panelSize[1] - space / 2

        self.position = (screen_size[0] - size[0]) / 2, (screen_size[1] - size[1]) / 2
        self.panelPosition = self.position[0], self.position[1] + self.titleSize[1] - space / 2

        self.switch_up_sound_path = SoundPath("switchUp")
        self.switch_down_sound_path = SoundPath("switchDown")

        title_font = pygame.font.Font(str(title_font_path), title_text_size)
        self.title = Button(self.position, self.titleSize, {"default": title_image_path},
                            title_text, title_text, title_font, title_text_color, title_text_color)

        self.panel = Object(self.panelPosition, self.panelSize, {"default": panel_image_path})

        self.buttons = {}

        if self.buttonCount:
            for i in range(self.buttonCount):
                button_position = pygame.math.Vector2(space, space * (i + 3 / 2) + button_size[1] * i)
                button_screen_position = button_position + self.panelPosition

                cfg = {
                    "position": list(button_screen_position),
                    "size": list(button_size),
                    "text": button_texts[i],
                    "selected_text": button_texts[i],
                    "text_color": button_text_color,
                    "selected_text_color": button_selected_text_color,
                    "font": button_font_key,
                    "font_size": button_text_size,
                    "paths": {
                        "default": button_image,
                        "hover": button_hover_image,
                    },
                }
                self.buttons[button_texts[i]] = button_factory(cfg, None)

            list(self.buttons.values())[0].set_state("hover")

        super().__init__(size, pygame.SRCALPHA)

    def handle_event(self, event, mouse_position) -> None:
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons.values()):
                if button.is_mouse_over(mouse_position) and button.state != "hover":
                    for j, button2 in enumerate(self.buttons.values()):
                        if button2.state == "hover":
                            if j > i:
                                SoundManager.play_sound(1, self.switch_down_sound_path)
                            else:
                                SoundManager.play_sound(1, self.switch_up_sound_path)

                            button.set_state("hover")
                            button2.set_state("default")
                            break

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                for i, button in enumerate(self.buttons.values()):
                    if button.state == "hover" and i != 0:
                        SoundManager.play_sound(1, self.switch_up_sound_path)
                        self.buttons[list(self.buttons.keys())[i - 1]].set_state("hover")
                        button.set_state("default")
                        break

            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                for i, button in enumerate(self.buttons.values()):
                    if button.state == "hover" and i != len(self.buttons) - 1:
                        SoundManager.play_sound(1, self.switch_down_sound_path)
                        self.buttons[list(self.buttons.keys())[i + 1]].set_state("hover")
                        button.set_state("default")
                        break

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self, self.position)
        self.title.draw(surface)
        self.panel.draw(surface)

        for button in self.buttons.values():
            button.draw(surface)