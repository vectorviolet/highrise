#-# Import Packages #-#
import pygame
from pygame.math import Vector2
from scripts.default.color import *
from scripts.default.object import *

class Tile(object):
	
	def __init__(self, width, height, rowNumber, columnNumber):

		self.rowNumber, self.columnNumber = rowNumber, columnNumber
		
		self.position = self.x, self.y = self.GetPosition(self.rowNumber, self.columnNumber)
		self.image = Object(self.position, (0, 0), {"Normal" : ImagePath("tile")})
		
		self.selected = False
		self.rect = self.image.rect
		self.selectedRect = self.rect.copy()
		self.unselectedRect = self.rect.copy()
		self.selectedRect.y -= 10

		self.position = Vector2(self.x, self.y)


		self.size = self.width, self.height = width, height
		
		
		self.surface = self.unselectedSurface = self.image["Normal"]
		self.selectedSurface = self.unselectedSurface.__copy__()
		self.isEmpty = True

		self.cornersOfUnselectedPolygon =  [(0, (self.rect.height/2) - 16),
		    (self.rect.width/2, 0),
			(self.rect.width, (self.rect.height/2) - 16),
			(self.rect.width/2, self.rect.height - 34)]
		
		pygame.draw.polygon(self.selectedSurface, White, self.cornersOfUnselectedPolygon, 1)
		pygame.draw.polygon(self.unselectedSurface, Gray, self.cornersOfUnselectedPolygon, 1)

		#-# real coordinates of polyon #-#
		self.cornersOfUnselectedPolygon[0] = self.cornersOfUnselectedPolygon[0][0] + self.rect.x, self.cornersOfUnselectedPolygon[0][1] + self.rect.y
		self.cornersOfUnselectedPolygon[1] = self.cornersOfUnselectedPolygon[1][0] + self.rect.x, self.cornersOfUnselectedPolygon[1][1] + self.rect.y
		self.cornersOfUnselectedPolygon[2] = self.cornersOfUnselectedPolygon[2][0] + self.rect.x, self.cornersOfUnselectedPolygon[2][1] + self.rect.y
		self.cornersOfUnselectedPolygon[3] = self.cornersOfUnselectedPolygon[3][0] + self.rect.x, self.cornersOfUnselectedPolygon[3][1] + self.rect.y

		#-# real coordinates of polygon of selected tile #-#
		self.cornersOfSelectedPolygon = self.cornersOfUnselectedPolygon
		self.cornersOfSelectedPolygon[0] = self.cornersOfSelectedPolygon[0][0], self.cornersOfSelectedPolygon[0][1] - self.y + self.selectedRect.y
		self.cornersOfSelectedPolygon[1] = self.cornersOfSelectedPolygon[1][0], self.cornersOfSelectedPolygon[1][1] - self.y + self.selectedRect.y
		self.cornersOfSelectedPolygon[2] = self.cornersOfSelectedPolygon[2][0], self.cornersOfSelectedPolygon[2][1] - self.y + self.selectedRect.y
		self.cornersOfSelectedPolygon[3] = self.cornersOfSelectedPolygon[3][0], self.cornersOfSelectedPolygon[3][1] - self.y + self.selectedRect.y

	def GetPosition(self, row, column) -> tuple:
		
		x = (column-row)*65 + 655 + 240
		y = (column+row)*32 + 200 + 90

		return x, y

	def getAreaOfTriangle(self, pointsOfTriangle) -> float:
		x1, y1 = pointsOfTriangle[0]
		x2, y2 = pointsOfTriangle[1]
		x3, y3 = pointsOfTriangle[2]
		return abs(x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1-y2))/2

	def isPointInTriangle(self, pointsOfTriangle, point) -> bool:
		areaOfABC = self.getAreaOfTriangle(pointsOfTriangle)
		areaOfAPB = self.getAreaOfTriangle([pointsOfTriangle[0], point, pointsOfTriangle[1]])
		areaOfAPC = self.getAreaOfTriangle([pointsOfTriangle[0], point, pointsOfTriangle[2]])
		areaOfBPC = self.getAreaOfTriangle([pointsOfTriangle[1], point, pointsOfTriangle[2]])
		return (areaOfABC == areaOfAPB + areaOfAPC + areaOfBPC)

	def isPointInQuadrangle(self, pointsOfQuadrangle, point) -> bool:
		isMouseOverTopTriangle = self.isPointInTriangle([pointsOfQuadrangle[0], pointsOfQuadrangle[1], pointsOfQuadrangle[2]], point)
		isMouseOverBotTriangle = self.isPointInTriangle([pointsOfQuadrangle[2], pointsOfQuadrangle[3], pointsOfQuadrangle[0]], point)

		return isMouseOverTopTriangle or isMouseOverBotTriangle

	def isMouseOverSelected(self, mousePosition) -> bool:
		return self.isPointInQuadrangle(self.cornersOfSelectedPolygon, mousePosition)

	def isMouseOverUnselected(self, mousePosition) -> bool:
		return self.isPointInQuadrangle(self.cornersOfUnselectedPolygon, mousePosition)

	def isMouseOver(self, mousePosition) -> bool:
		return self.isMouseOverSelected(mousePosition) or self.isMouseOverUnselected(mousePosition)

	def Draw(self, Window: pygame.Surface) -> None:

		if self.selected:
			Window.blit(self.selectedSurface, self.rect)
		else:
			Window.blit(self.unselectedSurface, self.rect)
		
class Tiles(list[Tile]):

	def __init__(self, size, maxSize) -> None:
		
		self.size = self.rowCount = self.columnCount = size
		self.maxSize = self.maxRowCount = self.maxColumnCount = maxSize

		self.Create()

	def Create(self) -> None:

		super().__init__()

		for rowNumber in range(self.rowCount):

			row = []

			for columnNumber in range(self.columnCount):

				row.append(Tile(132, 99, rowNumber + 1, columnNumber + 1))

			self.append(row)
	
	def isThereSelectedTile(self) -> bool:

		for row in self:

			for tile in row:

				if tile.selected:

					return True
				
		return False

	def GetExpandCost(self):
		
		return (self.rowCount + 1) * 100

	def Expand(self):

		if not self.isMaxSize():

			self.size = self.rowCount, self.columnCount = self.rowCount + 1, self.columnCount + 1
			self.Create()

	def isMaxSize(self) -> bool:

		return (self.rowCount == self.maxRowCount) or (self.columnCount == self.maxColumnCount)

	def ExpandRows(self):

		if self.rowCount < self.maxRowCount:

			self.size = self.rowCount, self.columnCount = self.rowCount + 1, self.columnCount
			self.Create()

	def ExpandColumns(self):

		if self.columnCount < self.maxColumnCount:

			self.size = self.rowCount, self.columnCount = self.rowCount, self.columnCount + 1
			self.Create()

	def HandleEvents(self, event: pygame.event.Event, mouesPosition: tuple):

		pass

	def Draw(self, surface: pygame.Surface) -> None:

		for row in self:

			for tile in row:
				
				tile.Draw(surface)

