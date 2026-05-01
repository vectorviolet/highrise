import pygame
from pygame_core.utils import Centerable


class TextObject(Centerable):
    """A GUI-compatible text label loaded from panel YAML.

    Implements the same minimal interface as GuiObject (draw / handle_event /
    is_clicked / set_state) so PanelManager can treat it uniformly.
    """

    def __init__(
        self,
        surface_size: tuple[int, int],
        pos,
        text: str,
        font: pygame.font.Font,
        color,
    ) -> None:
        self._surface = font.render(text, True, self._parse_color(color))

        text_size = self._surface.get_size()
        self._pos = super().resolve_pos(pos, surface_size, text_size)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._surface, self._pos)

    @staticmethod
    def _parse_color(color) -> tuple:
        if isinstance(color, (list, tuple)):
            return tuple(color)
        return tuple(pygame.Color(str(color)))