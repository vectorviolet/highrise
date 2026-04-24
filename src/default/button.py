#-# Importing Packages #-#
import pygame
from src.default.object import *
from src.default.text import *

#-# Button Class #-#
class Button(Object):

    def __init__(self, position: tuple = ..., size: tuple = ..., imagePaths=..., text: str = "", selectedText: str = "", textSize: int = 20, textColor: tuple = White, selectedTextColor: tuple = White, textFontPath: pygame.font.Font = None, surfaceSize: tuple = None, screen_position: tuple = None, visible=True):

        super().__init__(position, size, imagePaths, surfaceSize, screen_position, visible)

        if text:

            if not selectedText:

                selectedText = text

            self.add_text("Normal", text, textSize, True, textColor, None, textFontPath)
            self.add_text("Mouse Over", selectedText, textSize, True, selectedTextColor, None, textFontPath)

    def add_text(self, status, text: str, text_size: int, antialias: bool, color: tuple, background_color, fontPath: pygame.font.Font = None) -> None:

        if not hasattr(self, "text"):

            self.text = Text((0, 0), text, text_size, True, color, background_color, fontPath, True, status)

        else:

            self.text.add_text(status, text, text_size, antialias, color, background_color, fontPath)

    def draw(self, surface):

        super().draw(surface)

        if hasattr(self, "text") and self.visible:

            self.text.set_status(self.status, self.position, self.size)

            self.text.draw(surface)

#-# Menu Button Class #-#
class MenuButton(Button):

    def __init__(
            self,
            color: str,
            position: tuple,
            selectedColor: str = None,
            text: str = None,
            selectedText: str = None,
            textColor: tuple = None,
            selectedTextColor: tuple = None,
            textSize: int = 10,
            fontPath: str = None,
            size: tuple = None,
            selectedSize: tuple = [0, 0]
        ) -> None:

        imagePath = ImagePath(color, "gui/buttons")
        if not selectedColor: selectedColor = color
        selectedImagePath = ImagePath(selectedColor, "gui/buttons")

        super().__init__(position, size, {"Unselected" : imagePath})
        self.add_surface("Selected", load_image(selectedImagePath, selectedSize))
        self.status = "Unselected"

        if text:

            if not selectedText:

                selectedText = text

            self.add_text("Selected", text, textSize, True, textColor, None, fontPath)
            self.add_text("Unselected", selectedText, textSize, True, selectedTextColor, None, fontPath)