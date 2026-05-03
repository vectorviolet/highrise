#-# Importing Packages #-#
import pygame
from pygame_core.asset_path import ImagePath
from pygame_core.image import load_image

from object import Object
from pygame_core.color import White


class ButtonText(Object):
    def __init__(self,
                 position,
                 text,
                 font,
                 antialias=True,
                 color=White,
                 background_color=None,
                 is_centered=True,
                 state="default",
                 visible=True
         ) -> None:
        self.position = position
        self.isCentered = is_centered
        self.text_args = {}

        super().__init__(position, visible=visible)
        self.add_text(state, text, font, antialias, color, background_color)

    def add_text(self, state, text, font, antialias=True, color=White, background_color=None):
        super().add_text(state, text, font, antialias, color, background_color)
        self.text_args[state] = [text, font, antialias, color, background_color]

    def update_text(self, state, text) -> None:
        self.add_text(state, text, *self.text_args[state][1:])

    def update_size(self, state, size: int) -> None:
        old_font = self.text_args[state][1]
        try:
            new_font = pygame.font.Font(old_font.name, size)
        except (FileNotFoundError, OSError, TypeError):
            new_font = pygame.font.SysFont(old_font.name, size)
        self.add_text(state, self.text_args[state][0], new_font, *self.text_args[state][2:])

    def set_state(self, state: str, surface_position = (0, 0), surface_size = (0, 0)):
        super().set_state(state)

        if self.isCentered and state in self.states:
            c = (surface_position[0] + surface_size[0] / 2, surface_position[1] + surface_size[1] / 2)
            rect = self.states[state].get_rect(center=c)
            self.rect.set_position(rect.topleft)

class Button(Object):

    def __init__(self, position: tuple = ...,
                 size: tuple = ...,
                 image_paths=...,
                 text: str = "",
                 selected_text: str = "",
                 font: pygame.Font = None,
                 text_color: tuple = White,
                 selected_text_color: tuple = White,
                 screen_position: tuple = None,
                 visible=True,
                 parent=None
             ) -> None:

        super().__init__(position, size, image_paths, parent, screen_position, visible)

        self.text = None

        if text:
            if not selected_text:
                selected_text = text

            self.add_text("default", text, font, True, text_color, None)
            self.add_text("hover", selected_text, font, True, selected_text_color, None)

    def add_text(self, state, text: str, font: pygame.Font, antialias: bool, color: tuple, background_color) -> None:
        if self.text is None:
            self.text = ButtonText((0, 0), text, font, True, color, background_color, True, state)
        else:
            self.text.add_text(state, text, font, antialias, color, background_color)

    def draw(self, surface):
        super().draw(surface)

        if self.text is not None and self.visible:
            self.text.set_state(self.state, self.rect.topleft, self.size)
            self.text.draw(surface)

class MenuButton(Button):
    def __init__(
            self,
            color: str,
            position: tuple,
            selectedColor: str = None,
            text: str = None,
            selected_text: str = None,
            text_color: tuple = None,
            selected_text_color: tuple = None,
            text_size: int = 10,
            fontPath: str = None,
            size: tuple = None,
            selectedSize: tuple = None
        ) -> None:

        imagePath = ImagePath(color, "gui/buttons")
        if not selectedColor: selectedColor = color
        selectedImagePath = ImagePath(selectedColor, "gui/buttons")

        super().__init__(position, size, {"Unselected" : imagePath})
        self.add_surface("Selected", load_image(selectedImagePath, selectedSize or [0, 0]))
        self.state = "Unselected"

        if text:

            if not selected_text:

                selected_text = text

            self.add_text("Selected", text, text_size, True, text_color, None, fontPath)
            self.add_text("Unselected", selected_text, text_size, True, selected_text_color, None, fontPath)