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
		self.image_paths = image_paths if image_paths is not None else {"Normal": None}
		self.visible = visible
		self.status = None

		self.set_size(size)
		self.set_screen_position(screen_position)

	def add_text(self, status, text, text_size, antialias=True, color=White, background_color=None, fontPath = None):
		self.add_surface(status, pygame.font.Font(fontPath, text_size).render(text, antialias, color, background_color))

	def add_images(self, image_paths):
		for status, path in image_paths.items():
			if path is None or status is None: continue

			self.add_image(status, path)

	def add_image(self, status, image_path):
		self.add_surface(status, load_image(image_path, self.size))

	def add_surface(self, status: str | None, surface: pygame.Surface):
		self.states[status] = surface
		if not self.status and status == "Normal":
			self.set_status("Normal")

	def set_size(self, size):
		if size and size[0] and size[1]:
			self.size = self.width, self.height = size
			self.add_images(self.image_paths)
		else:
			self.size = [0, 0]
			self.add_images(self.image_paths)

			if len(self.states) > 0:
				if "Normal" in self.states:
					size = self.states["Normal"].get_rect().size
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
			self.status = "Mouse Click"
		elif "Mouse Over" in self.states and self.is_mouse_over(mouse_position):
			self.status = "Mouse Over"
		elif "Normal" in self.states:
			self.status = "Normal"

	def draw(self, surface) -> None:
		if self.visible and self.status in self.states:
			surface.blit(self.states[self.status], self.rect)

	def set_status(self, status: str):
		self.status = status