"""The pure geometry behind the isometric tile hit-test."""

import pytest

from gameplay.tiles.geometry import (
    get_area_of_triangle,
    is_point_in_quadrangle,
    is_point_in_triangle,
)

# A convenient large right triangle/square -- independent of any real tile's
# own diamond-shaped corners.
SQUARE = [(0, 0), (10, 0), (10, 10), (0, 10)]
TRIANGLE = [(0, 0), (10, 0), (0, 10)]


def test_area_of_triangle_matches_known_shape():
    # Right triangle with legs 10 and 10 -> area 50.
    assert get_area_of_triangle(TRIANGLE) == pytest.approx(50.0)


def test_area_of_triangle_ignores_winding_order():
    assert get_area_of_triangle(TRIANGLE[::-1]) == pytest.approx(50.0)


def test_area_of_degenerate_triangle_is_zero():
    collinear = [(0, 0), (5, 0), (10, 0)]
    assert get_area_of_triangle(collinear) == pytest.approx(0.0)


def test_is_point_in_triangle():
    assert is_point_in_triangle(TRIANGLE, (2, 2)) is True
    assert is_point_in_triangle(TRIANGLE, (9, 9)) is False  # outside the hypotenuse
    assert is_point_in_triangle(TRIANGLE, (-1, -1)) is False


def test_points_on_a_triangle_edge_or_corner_count_as_inside():
    assert is_point_in_triangle(TRIANGLE, (5, 0)) is True
    assert is_point_in_triangle(TRIANGLE, (0, 0)) is True


def test_is_point_in_quadrangle_covers_both_halves():
    assert is_point_in_quadrangle(SQUARE, (5, 5)) is True  # center
    assert is_point_in_quadrangle(SQUARE, (9, 1)) is True  # first half
    assert is_point_in_quadrangle(SQUARE, (1, 9)) is True  # second half
    assert is_point_in_quadrangle(SQUARE, (20, 20)) is False
    assert is_point_in_quadrangle(SQUARE, (-1, 5)) is False


def test_is_point_in_quadrangle_handles_a_diamond():
    # The shape real tiles use: left, top, right, bottom corners.
    diamond = [(0, 5), (10, 0), (20, 5), (10, 10)]
    assert is_point_in_quadrangle(diamond, (10, 5)) is True
    assert is_point_in_quadrangle(diamond, (1, 1)) is False  # outside top-left edge
    assert is_point_in_quadrangle(diamond, (19, 9)) is False
