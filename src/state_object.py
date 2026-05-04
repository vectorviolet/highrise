import pygame
from pygame import Vector2
from pygame_core.image import load_image
from pygame_core.utils import MouseInteractive
from pygame_core.unity.components.rigidbody2d import Rigidbody2D
from pygame_core.unity.gameobject import GameObject
from ext.image import nine_slice_scale


class StateObject(GameObject, MouseInteractive):
    def __init__(self,
                 position: tuple = ("CENTER", "CENTER"),
                 size: tuple | Vector2 = (0, 0),
                 image_paths=None,
                 parent=None,
                 visible=True,
                 nine_slice: int = 0):

        super().__init__()
        super().add_component(Rigidbody2D)
        self.rect.size = size
        self.rect.set_parent(parent)
        self.rect.set_position(position)

        self.states = {}
        self._hover_states: dict = {}
        self._hovered = False
        self._nine_slice = nine_slice
        self.image_paths = image_paths if image_paths is not None else {"default": None}
        self.visible = visible
        self.state = None

        if size and size[0] and size[1]:
            self.size = self.width, self.height = size
            self.add_images(self.image_paths)
            return

        self.size = [0, 0]
        self.add_images(self.image_paths)

        if len(self.states) > 0:
            if "default" in self.states:
                size = self.states["default"].get_rect().size
            else:
                size = list(self.states.values())[0].get_rect().size

            self.size = self.width, self.height = size

    def add_images(self, image_paths: dict):
        for state, path in image_paths.items():
            if path is None or state is None: continue
            self.add_image(state, path)

    def _load_surface(self, image_path) -> pygame.Surface:
        if self._nine_slice > 0 and self.size and self.size[0] and self.size[1]:
            return nine_slice_scale(load_image(image_path), tuple(self.size), self._nine_slice)
        return load_image(image_path, self.size)

    def add_image(self, state, image_path):
        self.add_surface(state, self._load_surface(image_path))

    def add_hover_image(self, state, image_path):
        if image_path is None:
            return
        self._hover_states[state] = self._load_surface(image_path)

    def add_surface(self, state: str | None, surface: pygame.Surface):
        self.states[state] = surface
        if not self.state and state == "default":
            self.set_state("default")

    def handle_event(self, event, mouse_position):
        self._hovered = self.is_mouse_over(mouse_position)
        if "mouse_click" in self.states and self.is_clicked(event, mouse_position):
            self.state = "mouse_click"
        elif "hover" in self.states and self._hovered:
            self.state = "hover"
        elif "default" in self.states:
            self.state = "default"

    def draw(self, surface) -> None:
        if not (self.visible and self.state in self.states):
            return
        if self._hovered and self.state in self._hover_states:
            surface.blit(self._hover_states[self.state], self.rect)
        else:
            surface.blit(self.states[self.state], self.rect)

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def set_state(self, state: str):
        self.state = state