"""Pure 2D geometry for the isometric tile hit-test (no pygame, no state)."""

from collections.abc import Sequence

Point = tuple[float, float]


def get_area_of_triangle(points_of_triangle: Sequence[Point]) -> float:
    x1, y1 = points_of_triangle[0]
    x2, y2 = points_of_triangle[1]
    x3, y3 = points_of_triangle[2]
    return abs(x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2


def is_point_in_triangle(points_of_triangle: Sequence[Point], point: Point) -> bool:
    area_abc = get_area_of_triangle(points_of_triangle)
    area_apb = get_area_of_triangle(
        [points_of_triangle[0], point, points_of_triangle[1]]
    )
    area_apc = get_area_of_triangle(
        [points_of_triangle[0], point, points_of_triangle[2]]
    )
    area_bpc = get_area_of_triangle(
        [points_of_triangle[1], point, points_of_triangle[2]]
    )
    return abs(area_abc - (area_apb + area_apc + area_bpc)) < 0.5


def is_point_in_quadrangle(points_of_quadrangle: Sequence[Point], point: Point) -> bool:
    top = is_point_in_triangle(
        [points_of_quadrangle[0], points_of_quadrangle[1], points_of_quadrangle[2]],
        point,
    )
    bot = is_point_in_triangle(
        [points_of_quadrangle[2], points_of_quadrangle[3], points_of_quadrangle[0]],
        point,
    )
    return top or bot
