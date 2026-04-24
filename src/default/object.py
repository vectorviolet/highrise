#-# Importing Packages #-#
import pygame
from game_core.path import *
from game_core.image import *
from game_core.color import *

#-# Object Class #-#
class Object(dict[str : pygame.Surface]):

	def __init__(self, position: tuple = ("CENTER", "CENTER"), size: tuple = (0, 0), imagePaths = {}, surfaceSize: tuple = None, screenPosition: tuple = None, visible = True):

		super().__init__()
		self.set_status(None)

		self.surfaceSize = surfaceSize
		self.imagePaths = imagePaths
		self.visible = visible

		self.set_size(size)
		self.set_position(position)

		self.set_screen_position(screenPosition)

	def add_text(self, status, text, textSize, antialias=True, color=White, backgroundColor=None, fontPath = None):

		self.add_surface(status, pygame.font.Font(fontPath, textSize).render(text, antialias, color, backgroundColor))

	def add_images(self, imagePaths):

		for status, path in imagePaths.items():

			self.add_image(status, path)

	def add_image(self, status, imagePath):

		self.add_surface(status, load_image(imagePath, self.size))

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

	def set_screen_position(self, screenPosition: tuple):

		if not screenPosition:

			self.screenPosition = self.position

		else:

			self.screenPosition = screenPosition

		self.screenRect = pygame.Rect(*self.screenPosition, *self.size)

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

	def is_mouse_over(self, mousePosition: tuple) -> bool:

		if mousePosition != None and self.screenRect.collidepoint(mousePosition) and self.visible:

			return True

		return False

	def is_mouse_click(self, event: pygame.event.Event, mousePosition: tuple) -> bool:

		if self.is_mouse_over(mousePosition) and event.type == pygame.MOUSEBUTTONUP:

			return True

		return False

	def show(self):

		self.visible = True

	def hide(self):

		self.visible = False

	def handle_events(self, event, mousePosition):

		if "Mouse Click" in self and self.is_mouse_click(event, mousePosition):

			self.set_status("Mouse Click")

		elif "Mouse Over" in self and self.is_mouse_over(mousePosition):

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