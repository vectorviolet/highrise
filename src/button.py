import pygame
from state_object import StateObject
from pygame_core.color import White


class ButtonText(StateObject):
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
        self.add_surface(state, font.render(text, antialias, color, background_color))
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

class Button(StateObject):

    def __init__(self, position: tuple = ...,
                 size: tuple = ...,
                 image_paths=...,
                 text: str = "",
                 selected_text: str = "",
                 font: pygame.Font = None,
                 text_color: tuple = White,
                 selected_text_color: tuple = White,
                 visible=True,
                 parent=None
             ) -> None:

        super().__init__(position, size, image_paths, parent, visible)

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