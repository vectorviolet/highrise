from gameobject.tile import Tile
from state_object.building import Building, Buildings


class TileSelector:
    def __init__(self, tilemap, mouse, buildings: Buildings) -> None:
        self.tilemap = tilemap
        self.mouse = mouse
        self.buildings = buildings
        self.is_active = False

    def update_selection(self) -> None:
        hovered = self.get_hovered_tile()
        for row in self.tilemap:
            for tile in row:
                tile.selected = tile is hovered
                tile.rect = tile.selected_rect if tile.selected and self.is_active else tile.unselected_rect

    def get_hovered_tile(self) -> Tile | None:
        for row in self.tilemap:
            for tile in row:
                if tile.is_mouse_over(self.mouse.position):
                    return tile
        return None

    def get_selected_tile(self) -> Tile | None:
        for row in self.tilemap:
            for tile in row:
                if tile.selected:
                    return tile
        return None

    def get_selected_building(self) -> Building | None:
        tile = self.get_selected_tile()
        if tile is None:
            return None
        for building in self.buildings:
            if building.tile == tile:
                return building
        return None