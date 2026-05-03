from pygame.math import Vector2

from pygame_core.color import White, Gray
from pygame_core.asset_path import ImagePath

from object import Object
from pygame import Surface
from pygame.event import Event
from pygame.draw import polygon

class Tile:

	def __init__(self, width, height, row_number, column_number):
		self.row_number, self.column_number = row_number, column_number
		self.position = self.x, self.y = self.get_position(self.row_number, self.column_number)
		self.image = Object(self.position, (0, 0), {"default" : ImagePath("tile")})
		self.selected = False
		self.rect = self.image.rect
		self.selected_rect = self.rect.copy()
		self.unselected_rect = self.rect.copy()
		self.selected_rect.y -= 10
		self.position = Vector2(self.x, self.y)
		self.size = self.width, self.height = width, height
		self.surface = self.unselected_surface = self.image.states["default"]
		self.selected_surface = self.unselected_surface.__copy__()
		self.is_empty = True

		self.corners_of_unselected_polygon = [(0, (self.rect.height / 2) - 16),
		                                      (self.rect.width/2, 0),
		                                      (self.rect.width, (self.rect.height/2) - 16),
		                                      (self.rect.width/2, self.rect.height - 34)]

		polygon(self.selected_surface, White, self.corners_of_unselected_polygon, 1)
		polygon(self.unselected_surface, Gray, self.corners_of_unselected_polygon, 1)

		self.corners_of_unselected_polygon[0] = self.corners_of_unselected_polygon[0][0] + self.rect.x, self.corners_of_unselected_polygon[0][1] + self.rect.y
		self.corners_of_unselected_polygon[1] = self.corners_of_unselected_polygon[1][0] + self.rect.x, self.corners_of_unselected_polygon[1][1] + self.rect.y
		self.corners_of_unselected_polygon[2] = self.corners_of_unselected_polygon[2][0] + self.rect.x, self.corners_of_unselected_polygon[2][1] + self.rect.y
		self.corners_of_unselected_polygon[3] = self.corners_of_unselected_polygon[3][0] + self.rect.x, self.corners_of_unselected_polygon[3][1] + self.rect.y

		self.corners_of_selected_polygon = self.corners_of_unselected_polygon.copy()
		self.corners_of_selected_polygon[0] = self.corners_of_selected_polygon[0][0], self.corners_of_selected_polygon[0][1] - self.y + self.selected_rect.y
		self.corners_of_selected_polygon[1] = self.corners_of_selected_polygon[1][0], self.corners_of_selected_polygon[1][1] - self.y + self.selected_rect.y
		self.corners_of_selected_polygon[2] = self.corners_of_selected_polygon[2][0], self.corners_of_selected_polygon[2][1] - self.y + self.selected_rect.y
		self.corners_of_selected_polygon[3] = self.corners_of_selected_polygon[3][0], self.corners_of_selected_polygon[3][1] - self.y + self.selected_rect.y

	@staticmethod
	def get_position(row, column) -> tuple:
		x = (column-row)*65 + 655 + 240
		y = (column+row)*32 + 200 + 90

		return x, y

	@staticmethod
	def get_area_of_triangle(points_of_triangle) -> float:
		x1, y1 = points_of_triangle[0]
		x2, y2 = points_of_triangle[1]
		x3, y3 = points_of_triangle[2]
		return abs(x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1-y2))/2

	def is_point_in_triangle(self, points_of_triangle, point) -> bool:
		area_abc = self.get_area_of_triangle(points_of_triangle)
		area_apb = self.get_area_of_triangle([points_of_triangle[0], point, points_of_triangle[1]])
		area_apc = self.get_area_of_triangle([points_of_triangle[0], point, points_of_triangle[2]])
		area_bpc = self.get_area_of_triangle([points_of_triangle[1], point, points_of_triangle[2]])
		return abs(area_abc - (area_apb + area_apc + area_bpc)) < 0.5

	def is_point_in_quadrangle(self, points_of_quadrangle, point) -> bool:
		top = self.is_point_in_triangle([points_of_quadrangle[0], points_of_quadrangle[1], points_of_quadrangle[2]], point)
		bot = self.is_point_in_triangle([points_of_quadrangle[2], points_of_quadrangle[3], points_of_quadrangle[0]], point)
		return top or bot

	def is_mouse_over_selected(self, mouse_position) -> bool:
		return self.is_point_in_quadrangle(self.corners_of_selected_polygon, mouse_position)

	def is_mouse_over_unselected(self, mouse_position) -> bool:
		return self.is_point_in_quadrangle(self.corners_of_unselected_polygon, mouse_position)

	def is_mouse_over(self, mouse_position) -> bool:
		return self.is_mouse_over_selected(mouse_position) or self.is_mouse_over_unselected(mouse_position)

	def draw(self, window: Surface) -> None:

		if self.selected:
			window.blit(self.selected_surface, self.rect)
		else:
			window.blit(self.unselected_surface, self.rect)

class Tiles(list[Tile]):
	def __init__(self, size, max_size) -> None:
		self.size = self.rowCount = self.columnCount = size
		self.maxSize = self.maxRowCount = self.maxColumnCount = max_size
		self.create()

	def create(self) -> None:
		super().__init__()
		for row_number in range(self.rowCount):

			row = []
			for column_number in range(self.columnCount):
				row.append(Tile(132, 99, row_number + 1, column_number + 1))

			self.append(row)

	def is_there_selected_tile(self) -> bool:

		for row in self:
			for tile in row:
				if tile.selected:
					return True
		return False

	def get_expand_cost(self):
		return (self.rowCount + 1) * 100

	def expand(self):
		if self.is_max_size(): return

		self.size = self.rowCount, self.columnCount = self.rowCount + 1, self.columnCount + 1
		self.create()

	def is_max_size(self) -> bool:

		return (self.rowCount == self.maxRowCount) or (self.columnCount == self.maxColumnCount)

	def expand_rows(self):

		if self.rowCount < self.maxRowCount:

			self.size = self.rowCount, self.columnCount = self.rowCount + 1, self.columnCount
			self.create()

	def expand_columns(self):
		if self.columnCount < self.maxColumnCount:
			self.size = self.rowCount, self.columnCount = self.rowCount, self.columnCount + 1
			self.create()

	def handle_event(self, event: Event, mouse_position: tuple):
		pass

	def draw(self, surface: Surface) -> None:
		for row in self:
			for tile in row:
				tile.draw(surface)
