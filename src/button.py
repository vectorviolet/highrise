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
                 text_size,
                 antialias=True,
                 color=White,
                 background_color=None,
                 font_path = None,
                 is_centered=True,
                 status="Normal",
                 visible=True
         ) -> None:
        self.position = position
        self.isCentered = is_centered
        self.text_args = {}

        super().__init__(position, visible=visible)
        self.add_text(status, text, text_size, antialias, color, background_color, font_path)

    def add_text(self, status, text, text_size, antialias=True, color=White, background_color=None, font_path=None):
        super().add_text(status, text, text_size, antialias, color, background_color, font_path)
        self.text_args[status] = [text, text_size, antialias, color, background_color, font_path]

    def update_text(self, status, text) -> None:
        self.add_text(status, text, *self.text_args[status][1:])

    def update_size(self, status, size: int) -> None:
        self.add_text(status, self.text_args[status][0], size, *self.text_args[status][2:])

    def set_status(self, status: str, surface_position = (0, 0), surface_size = (0, 0)):
        super().set_status(status)

        if self.isCentered and status in self.states:
            c = (surface_position[0] + surface_size[0] / 2, surface_position[1] + surface_size[1] / 2)
            rect = self.states[status].get_rect(center=c)
            self.rect.set_position(rect.topleft)

class Button(Object):

    def __init__(self, position: tuple = ...,
                 size: tuple = ...,
                 image_paths=...,
                 text: str = "",
                 selected_text: str = "",
                 text_size: int = 20,
                 text_color: tuple = White,
                 selected_text_color: tuple = White,
                 text_font_path: pygame.font.Font = None,
                 surface_size: tuple = None,
                 screen_position: tuple = None,
                 visible=True,
                 parent=None
             ) -> None:

        super().__init__(position, size, image_paths, parent, screen_position, visible)
        self.text = None

        if text:
            if not selected_text:
                selected_text = text

            self.add_text("Normal", text, text_size, True, text_color, None, text_font_path)
            self.add_text("Mouse Over", selected_text, text_size, True, selected_text_color, None, text_font_path)

    def add_text(self, status, text: str, text_size: int, antialias: bool, color: tuple, background_color, fontPath: pygame.font.Font = None) -> None:
        if self.text is None:
            self.text = ButtonText((0, 0), text, text_size, True, color, background_color, fontPath, True, status)
        else:
            self.text.add_text(status, text, text_size, antialias, color, background_color, fontPath)

    def draw(self, surface):
        super().draw(surface)

        if self.text is not None and self.visible:
            self.text.set_status(self.status, self.rect.topleft, self.size)
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
        self.status = "Unselected"

        if text:

            if not selected_text:

                selected_text = text

            self.add_text("Selected", text, text_size, True, text_color, None, fontPath)
            self.add_text("Unselected", selected_text, text_size, True, selected_text_color, None, fontPath)