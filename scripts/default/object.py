#-# Importing Packages #-#
import pygame
from scripts.default.path import *
from scripts.default.image import *
from scripts.default.color import *

#-# Object Class #-#
class Object(dict[str : pygame.Surface]):

	def __init__(self, position: tuple = ("CENTER", "CENTER"), size: tuple = (0, 0), imagePaths = {}, surfaceSize: tuple = None, screenPosition: tuple = None, show = True):
		
		super().__init__()
		self.SetStatus(None)
		
		self.surfaceSize = surfaceSize
		self.imagePaths = imagePaths
		self.show = show

		self.SetSize(size)
		self.SetPosition(position)

		self.SetScreenPosition(screenPosition)

	def AddText(self, status, text, textSize, antialias=True, color=White, backgroundColor=None, fontPath = None):

		self.AddSurface(status, pygame.font.Font(fontPath, textSize).render(text, antialias, color, backgroundColor))

	def AddImages(self, imagePaths):

		for status, path in imagePaths.items():
			
			self.AddImage(status, path)

	def AddImage(self, status, imagePath):

		self.AddSurface(status, GetImage(imagePath, self.size))

	def AddSurface(self, status: str, surface: pygame.Surface):
		
		self[status] = surface

		if not self.status:

			if status == "Normal":
			
				self.SetStatus("Normal")

	def Resize(self, size: tuple):

		self = Object(self.position, size, self.imagePaths, self.surfaceSize, self.show)

	def SetSize(self, size):
		
		if size and size[0] and size[1]:

			self.size = self.width, self.height = size

			self.AddImages(self.imagePaths)

		else:

			self.size = [0, 0]

			self.AddImages(self.imagePaths)

			if len(self) > 0:

				if "Normal" in self:

					size = self["Normal"].get_rect().size
				
				else:

					size = list(self.values())[0].get_rect().size

				self.size = self.width, self.height = size
			
	def SetPosition(self, position: tuple) -> None:

		self.position = pygame.math.Vector2(0, 0)
		self.SetX(position[0])
		self.SetY(position[1])
		
	def SetScreenPosition(self, screenPosition: tuple):

		if not screenPosition:

			self.screenPosition = self.position

		else:

			self.screenPosition = screenPosition

		self.screenRect = pygame.Rect(*self.screenPosition, *self.size)
	
	def SetX(self, x: int) -> None:

		if x == "CENTER":
		
			self.position.x = (self.surfaceSize[0] - self.width) / 2

		else:

			self.position.x = x

		if hasattr(self, "rect"):
		
			self.rect.topleft = self.position

		else:

			self.rect = pygame.Rect(self.position, self.size)

	def SetY(self, y: int) -> None:
		
		if y == "CENTER":
			
			self.position.y = (self.surfaceSize[1] - self.height) / 2
		
		else:

			self.position.y = y
		
		if hasattr(self, "rect"):
			
			self.rect.topleft = self.position

		else:

			self.rect = pygame.Rect(self.position, self.size)

	def isMouseOver(self, mousePosition: tuple) -> bool:
		
		if mousePosition != None and self.screenRect.collidepoint(mousePosition) and self.show:

			return True
		
		return False

	def isMouseClick(self, event: pygame.event.Event, mousePosition: tuple) -> bool:

		if self.isMouseOver(mousePosition) and event.type == pygame.MOUSEBUTTONUP:

			return True
		
		return False

	def Show(self):
		
		self.show = True

	def Hide(self):

		self.show = False

	def HandleEvents(self, event, mousePosition):
		
		if "Mouse Click" in self and self.isMouseClick(event, mousePosition):
			
			self.SetStatus("Mouse Click")

		elif "Mouse Over" in self and self.isMouseOver(mousePosition):

			self.SetStatus("Mouse Over")

		elif "Normal" in self:

			self.SetStatus("Normal")

	def SetStatus(self, status: str):

		self.status = status

	def SetVelocity(self, velocity: tuple):
		
		self.velocity = velocity

	def Move(self, velocity: tuple):
		
		self.SetPosition((self.position + pygame.math.Vector2(velocity)))

	def __Move(self):

		if hasattr(self, "velocity"):

			self.Move(self.velocity)

	def Draw(self, surface) -> None:

		self.__Move()

		if self.show and self.status in self:
				
			surface.blit(self[self.status], self.rect)

		