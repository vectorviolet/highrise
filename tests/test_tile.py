from gameplay.tiles.tile import Tile


def test_get_position_is_a_pure_function_of_row_and_column():
    assert Tile.get_position(1, 1) == Tile.get_position(1, 1)
    # Moving one column right shifts x by +65 and y by +32 (isometric step).
    x0, y0 = Tile.get_position(1, 1)
    x1, y1 = Tile.get_position(1, 2)
    assert (x1 - x0, y1 - y0) == (65, 32)
    # Moving one row down shifts x by -65 and y by +32.
    x2, y2 = Tile.get_position(2, 1)
    assert (x2 - x0, y2 - y0) == (-65, 32)


def test_new_tile_is_empty_and_unselected(assets):
    tile = Tile(3, 4)
    assert tile.is_empty is True
    assert tile.selected is False
    assert tile.row_number == 3
    assert tile.column_number == 4


def test_selected_rect_is_shifted_up_from_unselected(assets):
    tile = Tile(1, 1)
    assert tile.selected_rect.y == tile.unselected_rect.y - Tile.HOVER_SHIFT_Y
    assert tile.selected_rect.x == tile.unselected_rect.x


def test_own_center_registers_as_mouse_over_unselected(assets):
    tile = Tile(2, 2)
    center = tile.unselected_rect.center
    assert tile.is_mouse_over_unselected(center) is True
    far_away = (center[0] + 10_000, center[1] + 10_000)
    assert tile.is_mouse_over_unselected(far_away) is False
