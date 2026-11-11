"""ui/task_list.py: the rows of the checklist and the surface painted from them."""

import pygame

from ui.task_list import TaskRow, render_task_list


def test_progress_shows_current_over_target():
    assert TaskRow("Own a level 3 building", 2, 3, False).progress == "2/3"


def test_progress_is_held_at_the_target():
    assert TaskRow("Earn 20$ per second", 35, 20, False).progress == "20/20"


def test_a_done_task_shows_full_even_if_the_board_fell_behind():
    assert TaskRow("Earn 20$ per second", 4, 20, True).progress == "20/20"


def _surface(assets, rows, scale=1.0) -> pygame.Surface:
    return render_task_list(rows, str(assets.font_path("titillium_black")), scale)


def test_the_list_grows_with_its_rows(assets):
    two = [TaskRow("a", 0, 1, False), TaskRow("b", 0, 1, False)]
    three = two + [TaskRow("c", 0, 1, False)]

    assert _surface(assets, three).get_height() > _surface(assets, two).get_height()


def test_the_list_grows_with_the_ui_scale(assets):
    rows = [TaskRow("Own a level 3 building", 0, 3, False)]

    assert _surface(assets, rows, 2.0).get_width() > _surface(assets, rows).get_width()


def test_a_done_row_is_painted_differently_from_an_open_one(assets):
    open_row = [TaskRow("Own a level 3 building", 0, 3, False)]
    done_row = [TaskRow("Own a level 3 building", 3, 3, True)]

    open_pixels = pygame.image.tobytes(_surface(assets, open_row), "RGBA")
    done_pixels = pygame.image.tobytes(_surface(assets, done_row), "RGBA")

    assert open_pixels != done_pixels
