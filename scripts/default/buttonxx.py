import pygame
from scripts.default.image import *
from scripts.default.object import *

class Buttonxx(Object):

	def __init__(
			self,
			Text="Button",
			position: tuple = ("CENTER", "CENTER"),
			size: tuple = (None, None),
			Color="white",
			ActiveColor="white",
			CornerRadius=0,
			BorderSize=2,
			BorderColor="black",
			FontSize=23,
			FontColor="white",
			ActiveFontColor="white",
			FontSide="Center",
			FontMargin=20,
			IconPath=None,
			IconSize=[10, 10],
			IconSide="LeftCenter",
			IconMargin=20,
			surfaceSize: tuple = None,
			show = True
			):

		super().__init__(position, size, {}, surfaceSize, None, show)
		
		#-# Button Proporties #-#
		self.rect = pygame.Rect(self.position[0] - CornerRadius, self.position[1] - CornerRadius, self.size[0] + CornerRadius*2, self.size[1] + CornerRadius*2)
		self.Color, self.ActiveColor, self.CornerRadius, self.BorderSize, self.BorderColor = pygame.Color(Color), pygame.Color(ActiveColor), CornerRadius, BorderSize, pygame.Color(BorderColor)

		#-# Text And Font Proporties #-#
		self.Text, self.Font, self.FontSize, self.FontColor, self.ActiveFontColor = Text, pygame.font.Font("fonts/comic.ttf", FontSize), FontSize, pygame.Color(FontColor), pygame.Color(ActiveFontColor)
		self.Text, self.Text2 = self.Font.render(self.Text, True, self.FontColor), self.Font.render(self.Text, True, self.ActiveFontColor)

		#-# Icon Proporties #-#
		self.IconPath, self.IconSize, self.IconMargin =  IconPath, IconSize, IconMargin

		#-# Sides #-#
		self.FontSide = self.GetSide(FontSide, self.Text.get_size(), FontMargin)
		if self.IconPath != None: self.IconSide = self.GetSide(IconSide, IconSize, IconMargin)

		#-# Creating Button #-#
		self.Surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
		self.MouseOverSurface = self.Surface.copy()
		
		pygame.draw.rect(self.Surface, self.Color, ((0, 0), self.rect.size), 0, self.CornerRadius)
		pygame.draw.rect(self.MouseOverSurface, self.ActiveColor, ((0, 0), self.rect.size), 0, self.CornerRadius)
		
		if self.BorderSize > 0:

			pygame.draw.rect(self.Surface, self.BorderColor, ((0, 0), (self.rect.width - self.BorderSize, self.rect.height - self.BorderSize)), self.BorderSize, self.CornerRadius)
			pygame.draw.rect(self.MouseOverSurface, self.BorderColor, ((0, 0), (self.rect.width - self.BorderSize, self.rect.height - self.BorderSize)), self.BorderSize, self.CornerRadius)
			
		if self.IconPath != None:

			Images((self.IconSide, self.IconSize), self.IconPath).Draw(self.Surface)
			Images((self.IconSide, self.IconSize), self.IconPath).Draw(self.MouseOverSurface)
		
		self.Surface.blit(self.Text, self.FontSide)
		self.MouseOverSurface.blit(self.Text2, self.FontSide)
		
		self.ActiveSurface = self.Surface.copy()
		self.MouseOverActiveSurface = self.MouseOverSurface.copy()
		
		pygame.draw.rect(self.ActiveSurface, self.FontColor, ((0, 0), self.rect.size), 1, self.CornerRadius)		
		pygame.draw.rect(self.MouseOverActiveSurface, self.FontColor, ((0, 0), self.rect.size), 1, self.CornerRadius)
		
		self.Active, self.status = False, "Normal"

		self.AddSurface("active", self.ActiveSurface)
		self.AddSurface("Normal", self.Surface)

	def GetSide(self, Side, Size, Margin):

		#-# Sides #-#
		self.Left = self.BorderSize + Margin
		self.CenterX = (self.rect.width - Size[0])/2
		self.Right = self.rect.width - Size[0] - self.BorderSize - Margin
		self.Top = self.BorderSize + Margin
		self.CenterY = (self.rect.height - Size[1])/2
		self.Bottom = self.rect.height - Size[1] - self.BorderSize - Margin

		return {"TopLeft" : (self.Left, self.Top),
		 "TopCenter" : (self.CenterX, self.Top),
		 "RightCenter" : (self.Right, self.Top),
		 "LeftCenter" : (self.Left, self.CenterY),
		 "Center" : (self.CenterX, self.CenterY),
		 "RightCenter" : (self.Right, self.CenterY),
		 "BottomLeft" : (self.Left , self.Bottom ),
		 "BottomCenter" : (self.CenterX, self.Bottom),
		 "BottomCenter" : (self.Right, self.Bottom)}.get(Side)

	def HandleEvents(self, event, MousePosition):

		if self.isMouseOver(MousePosition):
			
			self.status = "MouseOverActive" if self.status == "Active" else "MouseOver"

		else:
			
			self.status = "Active" if self.status == "MouseOverActive" else "Normal"		
			
		if event.type == pygame.MOUSEBUTTONUP:
			
			self.status = "Normal"

		if self.isMouseClick(event, MousePosition):
			
			self.status = "MouseOverActive" if self.status == "MouseOver" else "MouseOver"

	def Draw(self, surface):

		if self.show:

			if self.status == "Normal" or self.status == "Active":
				
				surface.blit(self.surfaces[self.status], self.rect)

			elif self.status == "MouseOver": surface.blit(self.MouseOverSurface, [self.rect.x, self.rect.y - 5])		
			elif self.status == "MouseOverActive": surface.blit(self.MouseOverActiveSurface, [self.rect.x, self.rect.y - 5])