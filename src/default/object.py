#-# Importing Packages #-#
import pygame
from pygame_core.path import *
from pygame_core.image import *
from pygame_core.color import *

#-# Object Class #-#
class Object(dict[str : pygame.Surface]):
	def __init__(self, position: tuple = ("CENTER", "CENTER"), size: tuple = (0, 0), imagePaths = {}, surfaceSize: tuple = None, screen_position: tuple = None, visible = True):
		super().__init__()

		self.surfaceSize = surfaceSize
		self.imagePaths = imagePaths
		self.visible = visible

		self.set_status(None)
		self.set_size(size)
		self.set_position(position)
		self.set_screen_position(screen_position)

	def add_text(self, status, text, text_size, antialias=True, color=White, background_color=None, fontPath = None):
		self.add_surface(status, pygame.font.Font(fontPath, text_size).render(text, antialias, color, background_color))

	def add_images(self, image_paths):
		for status, path in image_paths.items():
			self.add_image(status, path)

	def add_image(self, status, image_path):
		self.add_surface(status, load_image(image_path, self.size))

	def add_surface(self, status: str, surface: pygame.Surface):
		self[status] = surface
		if not self.status:
			if status == "Normal":
				self.set_status("Normal")

	def resize(self, size: tuple):
		self = Object(self.position, size, self.imagePaths, self.surfaceSize, self.visible)

	def set_size(self, size):
		if size and size[0] and size[1]:
			self.size = self.width, self.height = size
			self.add_images(self.imagePaths)
		else:
			self.size = [0, 0]
			self.add_images(self.imagePaths)

			if len(self) > 0:
				if "Normal" in self:
					size = self["Normal"].get_rect().size
				else:
					size = list(self.values())[0].get_rect().size

				self.size = self.width, self.height = size

	def set_position(self, position: tuple) -> None:
		self.position = pygame.math.Vector2(0, 0)
		self.set_x(position[0])
		self.set_y(position[1])

	def set_screen_position(self, screen_position: tuple):
		if not screen_position:
			self.screen_position = self.position
		else:
			self.screen_position = screen_position

		self.screen_rect = pygame.Rect(*self.screen_position, *self.size)

	def set_x(self, x: int) -> None:
		if x == "CENTER":
			self.position.x = (self.surfaceSize[0] - self.width) / 2
		else:
			self.position.x = x

		if hasattr(self, "rect"):
			self.rect.topleft = self.position
		else:
			self.rect = pygame.Rect(self.position, self.size)

	def set_y(self, y: int) -> None:
		if y == "CENTER":
			self.position.y = (self.surfaceSize[1] - self.height) / 2
		else:
			self.position.y = y

		if hasattr(self, "rect"):
			self.rect.topleft = self.position
		else:
			self.rect = pygame.Rect(self.position, self.size)

	def is_mouse_over(self, mouse_position: tuple) -> bool:
		return mouse_position is not None and self.screen_rect.collidepoint(mouse_position) and self.visible

	def is_mouse_click(self, event: pygame.event.Event, mouse_position: tuple) -> bool:
		return self.is_mouse_over(mouse_position) and event.type == pygame.MOUSEBUTTONUP

	def show(self):
		self.visible = True

	def hide(self):
		self.visible = False

	def handle_events(self, event, mouse_position):
		if "Mouse Click" in self and self.is_mouse_click(event, mouse_position):
			self.set_status("Mouse Click")

		elif "Mouse Over" in self and self.is_mouse_over(mouse_position):
			self.set_status("Mouse Over")

		elif "Normal" in self:
			self.set_status("Normal")

	def set_status(self, status: str):
		self.status = status

	def set_velocity(self, velocity: tuple):
		self.velocity = velocity

	def move(self, velocity: tuple):
		self.set_position((self.position + pygame.math.Vector2(velocity)))

	def __move(self):
		if hasattr(self, "velocity"):
			self.move(self.velocity)

	def draw(self, surface) -> None:
		self.__move()

		if self.visible and self.status in self:
			surface.blit(self[self.status], self.rect)