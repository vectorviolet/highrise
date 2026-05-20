from pygame import Surface

from gameplay.tiles.tile import Tile


class Tilemap(list[list[Tile]]):
	def __init__(self, size, max_size) -> None:
		super().__init__()
		self.size = self.row_count = self.column_count = size
		self.max_size = self.max_row_count = self.max_column_count = max_size
		self.create()

	def create(self) -> None:
		self.clear()
		for row_number in range(self.row_count):
			row = []
			for column_number in range(self.column_count):
				row.append(Tile(row_number + 1, column_number + 1))

			self.append(row)

	def is_there_selected_tile(self) -> bool:

		for row in self:
			for tile in row:
				if tile.selected:
					return True
		return False

	def get_expand_cost(self):
		return (self.row_count + 1) * 100

	def expand(self):
		if self.is_max_size(): return

		self.size = self.row_count, self.column_count = self.row_count + 1, self.column_count + 1
		self.create()

	def is_max_size(self) -> bool:

		return (self.row_count == self.max_row_count) or (self.column_count == self.max_column_count)

	def expand_rows(self):
		if self.row_count < self.max_row_count:
			self.size = self.row_count, self.column_count = self.row_count + 1, self.column_count
			self.create()

	def expand_columns(self):
		if self.column_count < self.max_column_count:
			self.size = self.row_count, self.column_count = self.row_count, self.column_count + 1
			self.create()

	def draw(self, surface: Surface) -> None:
		for row in self:
			for tile in row:
				tile.draw(surface)
