import pygame
from pygame import Vector2
from pygame_core.image import load_image
from pygame_core.color import White
from pygame_core.utils import MouseInteractive
from untiy.components.rigidbody2d import Rigidbody2D
from untiy.gameobject import GameObject


class Object(GameObject, MouseInteractive):
	def __init__(self,
	             position: tuple = ("CENTER", "CENTER"),
	             size: tuple | Vector2 = (0, 0),
	             image_paths = None,
	             parent = None,
	             screen_position: tuple = None,
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

		self.set_size(size)
		self.set_screen_position(screen_position)

	def add_text(self, state, text, font, antialias=True, color=White, background_color=None):
		self.add_surface(state, font.render(text, antialias, color, background_color))

	def add_images(self, image_paths):
		for state, path in image_paths.items():
			if path is None or state is None: continue

			self.add_image(state, path)

	def add_image(self, state, image_path):
		self.add_surface(state, load_image(image_path, self.size))

	def add_surface(self, state: str | None, surface: pygame.Surface):
		self.states[state] = surface
		if not self.state and state == "default":
			self.set_state("default")

	def set_size(self, size):
		if size and size[0] and size[1]:
			self.size = self.width, self.height = size
			self.add_images(self.image_paths)
		else:
			self.size = [0, 0]
			self.add_images(self.image_paths)

			if len(self.states) > 0:
				if "default" in self.states:
					size = self.states["default"].get_rect().size
				else:
					size = list(self.values())[0].get_rect().size

				self.size = self.width, self.height = size

	def set_screen_position(self, screen_position: tuple | None):
		if not screen_position:
			self.screen_position = self.rect.topleft
		else:
			self.screen_position = screen_position

		self.screen_rect = pygame.Rect(*self.screen_position, *self.size)

	def is_mouse_over(self, mouse_position: tuple) -> bool:
		return mouse_position is not None and self.screen_rect.collidepoint(mouse_position) and self.visible

	def show(self):
		self.visible = True

	def hide(self):
		self.visible = False

	def handle_event(self, event, mouse_position):
		if "Mouse Click" in self.states and self.is_clicked(event, mouse_position):
			self.state = "Mouse Click"
		elif "hover" in self.states and self.is_mouse_over(mouse_position):
			self.state = "hover"
		elif "default" in self.states:
			self.state = "default"

	def draw(self, surface) -> None:
		if self.visible and self.state in self.states:
			surface.blit(self.states[self.state], self.rect)

	def set_state(self, state: str):
		self.state = state