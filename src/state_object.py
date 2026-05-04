import pygame
from pygame import Vector2
from pygame_core.image import load_image
from pygame_core.color import White
from pygame_core.utils import MouseInteractive
from pygame_core.unity.components.rigidbody2d import Rigidbody2D
from pygame_core.unity.gameobject import GameObject


class StateObject(GameObject, MouseInteractive):
	def __init__(self,
	             position: tuple = ("CENTER", "CENTER"),
	             size: tuple | Vector2 = (0, 0),
	             image_paths = None,
	             parent = None,
				 visible = True):

		super().__init__()
		super().add_component(Rigidbody2D)
		self.rect.size = size
		self.rect.set_parent(parent)
		self.rect.set_position(position)

		self.states = {}
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

	def add_image(self, state, image_path: str):
		self.add_surface(state, load_image(image_path, self.size))

	def add_surface(self, state: str | None, surface: pygame.Surface):
		self.states[state] = surface
		if not self.state and state == "default":
			self.set_state("default")

	def handle_event(self, event, mouse_position):
		if "mouse_click" in self.states and self.is_clicked(event, mouse_position):
			self.state = "mouse_click"
		elif "hover" in self.states and self.is_mouse_over(mouse_position):
			self.state = "hover"
		elif "default" in self.states:
			self.state = "default"

	def draw(self, surface) -> None:
		if self.visible and self.state in self.states:
			surface.blit(self.states[self.state], self.rect)

	def show(self):
		self.visible = True

	def hide(self):
		self.visible = False

	def set_state(self, state: str):
		self.state = state