"""The checklist of the current age's tasks (issue #52): a title, then one row per task with a
check box (ticked when done), its text and its progress ("2/3").

`render_task_list` only paints the list onto a surface; where it is shown (over the NEXT AGE
button on hover, or as an always-visible panel) is decided by `Game`, see `ui` in
config/tasks.yaml.
"""

from dataclasses import dataclass
from functools import lru_cache

import pygame

from pygamine.util.localization import tr

BACKGROUND = (20, 24, 32, 220)
BORDER = (255, 255, 255, 90)
TEXT = (255, 255, 255)
DONE_TEXT = (120, 220, 130)
TITLE_SIZE = 20
ROW_SIZE = 18
PADDING = 12
ROW_GAP = 6
BOX_GAP = 8
COLUMN_GAP = 18


@lru_cache(maxsize=None)
def _font(path: str, size: int) -> pygame.font.Font:
    return pygame.font.Font(path, size)


@dataclass(frozen=True)
class TaskRow:
    text: str
    current: int
    target: int
    done: bool

    @property
    def progress(self) -> str:
        # A finished task shows full, even if the board has fallen behind since.
        current = self.target if self.done else min(self.current, self.target)
        return f"{current}/{self.target}"


def _draw_check_box(surface: pygame.Surface, rect: pygame.Rect, done: bool) -> None:
    color = DONE_TEXT if done else TEXT
    pygame.draw.rect(
        surface, color, rect, width=max(1, rect.width // 8), border_radius=3
    )
    if done:
        w, h = rect.size
        points = [
            (rect.x + w * 0.22, rect.y + h * 0.52),
            (rect.x + w * 0.43, rect.y + h * 0.74),
            (rect.x + w * 0.80, rect.y + h * 0.26),
        ]
        pygame.draw.lines(surface, color, False, points, max(2, w // 6))


def render_task_list(
    rows: list[TaskRow], font_path: str, scale: float
) -> pygame.Surface:
    """The checklist as a surface, sized for UI scale `scale` (1.0 = 100%)."""
    title_font = _font(font_path, round(TITLE_SIZE * scale))
    row_font = _font(font_path, round(ROW_SIZE * scale))
    pad = round(PADDING * scale)
    gap = round(ROW_GAP * scale)
    box_gap = round(BOX_GAP * scale)
    column_gap = round(COLUMN_GAP * scale)
    box = row_font.get_height() - 2

    title = title_font.render(tr("tasks.title"), True, TEXT)
    colors = [DONE_TEXT if row.done else TEXT for row in rows]
    texts = [row_font.render(r.text, True, c) for r, c in zip(rows, colors)]
    progresses = [row_font.render(r.progress, True, c) for r, c in zip(rows, colors)]
    text_width = max((t.get_width() for t in texts), default=0)
    progress_width = max((p.get_width() for p in progresses), default=0)
    row_width = box + box_gap + text_width + column_gap + progress_width
    width = pad * 2 + max(title.get_width(), row_width)
    row_height = row_font.get_height()
    height = pad * 2 + title.get_height() + len(rows) * (row_height + gap)

    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surface, BACKGROUND, surface.get_rect(), border_radius=pad)
    pygame.draw.rect(surface, BORDER, surface.get_rect(), width=2, border_radius=pad)
    surface.blit(title, (pad, pad))
    y = pad + title.get_height() + gap
    for row, text, progress in zip(rows, texts, progresses):
        _draw_check_box(surface, pygame.Rect(pad, y + 1, box, box), row.done)
        surface.blit(text, (pad + box + box_gap, y))
        surface.blit(progress, (width - pad - progress.get_width(), y))
        y += row_height + gap
    return surface
