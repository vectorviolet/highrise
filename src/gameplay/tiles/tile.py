from typing import override

from pygame import Surface
from pygame.draw import polygon
from pygamine import ImagePath
from pygamine import load_image

from pygamine import SpriteRenderer2D
from pygamine import GameObject

from gameplay.tiles.geometry import is_point_in_quadrangle


class Tile(GameObject):
    GRID_COLOR = (128, 128, 128)
    GRID_HOVER_COLOR = "yellow"
    HOVER_SHIFT_Y = 10

    def __init__(self, row_number, column_number) -> None:
        super().__init__()
        self.selected = False
        self.is_empty = True

        self.row_number, self.column_number = row_number, column_number
        renderer = self.add_component(SpriteRenderer2D)
        renderer.set_image(load_image(ImagePath("tile")))
        assert renderer.image is not None

        self.rect.size = renderer.image.get_size()
        self.rect.set_position(self.get_position(row_number, column_number))

        self.unselected_rect = self.rect.copy()
        self.selected_rect = self.rect.copy()
        self.selected_rect.y -= self.HOVER_SHIFT_Y

        self.surface = self.unselected_surface = renderer.image
        self.selected_surface = self.unselected_surface.__copy__()

        local_corners = [
            (0, (self.rect.height / 2) - 16),
            (self.rect.width / 2, 0),
            (self.rect.width, (self.rect.height / 2) - 16),
            (self.rect.width / 2, self.rect.height - 34),
        ]

        polygon(self.selected_surface, self.GRID_HOVER_COLOR, local_corners, 1)
        polygon(self.unselected_surface, self.GRID_COLOR, local_corners, 1)

        self.corners_of_unselected_polygon = [
            (x + self.rect.x, y + self.rect.y) for x, y in local_corners
        ]
        self.corners_of_selected_polygon = [
            (x, y - self.HOVER_SHIFT_Y) for x, y in self.corners_of_unselected_polygon
        ]

    @staticmethod
    def get_position(row, column) -> tuple[int, int]:
        x = (column - row) * 65 + 655 + 240
        y = (column + row) * 32 + 200 + 90

        return x, y

    def is_mouse_over_selected(self, mouse_position) -> bool:
        return is_point_in_quadrangle(self.corners_of_selected_polygon, mouse_position)

    def is_mouse_over_unselected(self, mouse_position) -> bool:
        return is_point_in_quadrangle(
            self.corners_of_unselected_polygon, mouse_position
        )

    def is_mouse_over(self, mouse_position) -> bool:
        return self.is_mouse_over_selected(
            mouse_position
        ) or self.is_mouse_over_unselected(mouse_position)

    @override
    def draw(self, window: Surface) -> None:
        if not self.active:
            return
        window.blit(
            self.selected_surface if self.selected else self.unselected_surface,
            self.rect,
        )
