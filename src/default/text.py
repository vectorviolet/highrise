import pygame
from game_core.color import White
from src.default.object import *
from game_core.color import *

class Text(Object):

    def __init__(self, position, text, textSize, antialias=True, color=White, backgroundColor=None, fontPath = None, isCentered=True, status="Normal", visible=True) -> None:

        self.position = position
        self.isCentered = isCentered
        self.textArgs = {}

        super().__init__(position, visible=visible)

        self.add_text(status, text, textSize, antialias, color, backgroundColor, fontPath)

    def add_text(self, status, text, textSize, antialias=True, color=White, backgroundColor=None, fontPath=None):

        super().add_text(status, text, textSize, antialias, color, backgroundColor, fontPath)

        self.textArgs[status] = [text, textSize, antialias, color, backgroundColor, fontPath]

    def update_text(self, status, text) -> None:

        self.add_text(status, text, *self.textArgs[status][1:])

    def update_size(self, status, size: int) -> None:

        self.add_text(status, self.textArgs[status][0], size, *self.textArgs[status][2:])

    def set_status(self, status: str, surfacePosition = (0, 0), surfaceSize = (0, 0)):

        super().set_status(status)

        if self.isCentered and status in self:

            rect = self[status].get_rect(center=(surfacePosition[0] + surfaceSize[0]/2, surfacePosition[1] + surfaceSize[1]/2))

            self.set_position(rect.topleft)

    def handle_events(self, event: pygame.event.Event, surface: pygame.Surface) -> None:

        pass