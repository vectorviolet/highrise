import pygame
from pygame_core.image import load_image
from pygame_core.color import White
from pygame_core.utils import MouseInteractive
from untiy.rigidbody2d import Rigidbody2D
from untiy.gameobject import GameObject


class Object(MouseInteractive, GameObject):
	def __init__(self,
	             position: tuple = ("CENTER", "CENTER"),
	             size: tuple = (0, 0),
	             image_paths = {},
	             surface_size: tuple = None,
	             screen_position: tuple = None,
				 visible = True):

		super().__init__()
		super().add_component(Rigidbody2D)
		#super().transform.parent =
		self.transform.set_position(position)

		self.states = {}
		self.image_paths = image_paths
		self.visible = visible
		self.status = None

		self.set_size(size)
		self.set_screen_position(screen_position)

	def add_text(self, status, text, text_size, antialias=True, color=White, background_color=None, fontPath = None):
		self.add_surface(status, pygame.font.Font(fontPath, text_size).render(text, antialias, color, background_color))

	def add_images(self, image_paths):
		for status, path in image_paths.items():
			self.add_image(status, path)

	def add_image(self, status, image_path):
		self.add_surface(status, load_image(image_path, self.size))

	def add_surface(self, status: str | None, surface: pygame.Surface):
		self.states[status] = surface
		if not self.status and status == "Normal":
			self.set_status("Normal")

	def resize(self, size: tuple):
		self = Object(self.position, size, self.image_paths, self.surface_size, self.visible)

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

	def set_screen_position(self, screen_position: tuple):
		if not screen_position:
			self.screen_position = self.transform.topleft
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
			surface.blit(self.states[self.status], self.transform)

	def set_status(self, status: str):
		self.status = status