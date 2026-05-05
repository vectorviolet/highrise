import pygame

from sound_manager import SoundManager
from pygame_core.asset_path import AssetPath, FontPath, SoundPath
from state_object.state_object import StateObject
from state_object.button import Button
from unity.gameobject import GameObject


class Menu(GameObject):
    def __init__(
            self,
            title_image_path: AssetPath,
            title_text: str,
            title_text_size: int,
            title_text_color: tuple | str,
            title_font_path: FontPath,
            panel_image_path: AssetPath,

            button_size: tuple,
            button_image: str,
            button_hover_image: str,
            button_texts: tuple,
            button_text_size: int,
            button_text_color: tuple | str,
            button_selected_text_color: tuple | str,
            button_font_key: str,

            screen_size: tuple,
            button_factory,
            *,
            panel_height: int = None,
            ) -> None:

        super().__init__()

        space = 20
        button_count = len(button_texts)

        self.title_size = button_size[0] + space * 2, 70
        self.panel_size = button_size[0] + space * 2, button_size[1] * button_count + (button_count + 3) * space

        if panel_height:
            self.panel_size = self.panel_size[0], panel_height

        size = self.title_size[0], self.title_size[1] + self.panel_size[1] - space / 2

        self.position = (screen_size[0] - size[0]) / 2, (screen_size[1] - size[1]) / 2
        self.panel_position = self.position[0], self.position[1] + self.title_size[1] - space / 2

        self.switch_up_sound_path = SoundPath("switchUp")
        self.switch_down_sound_path = SoundPath("switchDown")

        title_font = pygame.font.Font(str(title_font_path), title_text_size)
        self.title = Button(self.position, self.title_size, {"default": title_image_path},
                            title_text, title_text, title_font, title_text_color, title_text_color)

        self.panel = StateObject(self.panel_position, self.panel_size, {"default": panel_image_path})

        self.buttons = {}

        for i, text in enumerate(button_texts):
            button_position = pygame.math.Vector2(space, space * (i + 3 / 2) + button_size[1] * i)
            button_screen_position = button_position + self.panel_position

            cfg = {
                "position": list(button_screen_position),
                "size": list(button_size),
                "text": text,
                "selected_text": text,
                "text_color": button_text_color,
                "selected_text_color": button_selected_text_color,
                "font": button_font_key,
                "font_size": button_text_size,
                "paths": {
                    "default": button_image,
                    "hover": button_hover_image,
                },
            }
            self.buttons[text] = button_factory(cfg, None)

        if self.buttons:
            next(iter(self.buttons.values())).set_state("hover")

    def handle_event(self, event, mouse_position) -> None:
        if not self.active:
            return
        buttons = list(self.buttons.values())

        if event.type == pygame.MOUSEMOTION:
            target_i = next((i for i, b in enumerate(buttons) if b.is_mouse_over(mouse_position) and b.state != "hover"), None)
            hover_i  = next((i for i, b in enumerate(buttons) if b.state == "hover"), None)
            if target_i is None or hover_i is None:
                return
            sound = self.switch_down_sound_path if hover_i > target_i else self.switch_up_sound_path
            SoundManager.play_sound(1, sound)
            buttons[target_i].set_state("hover")
            buttons[hover_i].set_state("default")

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_w, pygame.K_UP):
                delta, sound = -1, self.switch_up_sound_path
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                delta, sound = 1, self.switch_down_sound_path
            else:
                return

            hover_i = next((i for i, b in enumerate(buttons) if b.state == "hover"), None)
            if hover_i is not None and 0 <= hover_i + delta < len(buttons):
                SoundManager.play_sound(1, sound)
                buttons[hover_i + delta].set_state("hover")
                buttons[hover_i].set_state("default")

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        self.title.draw(surface)
        self.panel.draw(surface)

        for button in self.buttons.values():
            button.draw(surface)