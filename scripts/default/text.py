import pygame
from scripts.default.color import White
from scripts.default.object import *
from scripts.default.color import *

class Text(Object):

    def __init__(self, position, text, textSize, antialias=True, color=White, backgroundColor=None, fontPath = None, isCentered=True, status="Normal", show=True) -> None:
        
        self.position = position
        self.isCentered = isCentered
        self.textArgs = {}
        
        super().__init__(position, show=show)

        self.AddText(status, text, textSize, antialias, color, backgroundColor, fontPath)

    def AddText(self, status, text, textSize, antialias=True, color=White, backgroundColor=None, fontPath=None):

        super().AddText(status, text, textSize, antialias, color, backgroundColor, fontPath)
        
        self.textArgs[status] = [text, textSize, antialias, color, backgroundColor, fontPath]

    def UpdateText(self, status, text) -> None:

        self.AddText(status, text, *self.textArgs[status][1:])

    def UpdateSize(self, status, size: int) -> None:

        self.AddText(status, self.textArgs[status][0], size, *self.textArgs[status][2:])

    def SetStatus(self, status: str, surfacePosition = (0, 0), surfaceSize = (0, 0)):
        
        super().SetStatus(status)

        if self.isCentered and status in self:
            
            rect = self[status].get_rect(center=(surfacePosition[0] + surfaceSize[0]/2, surfacePosition[1] + surfaceSize[1]/2))

            self.SetPosition(rect.topleft)

    def HandleEvents(self, event: pygame.event.Event, surface: pygame.Surface) -> None:

        pass
