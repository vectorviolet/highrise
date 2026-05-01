from default.object import Object
from pygame_core.color import White


class Text(Object):
    def __init__(self,
                 position,
                 text,
                 text_size,
                 antialias=True,
                 color=White,
                 background_color=None,
                 font_path = None,
                 is_centered=True,
                 status="Normal",
                 visible=True
         ) -> None:
        self.position = position
        self.isCentered = is_centered
        self.text_args = {}

        super().__init__(position, visible=visible)
        self.add_text(status, text, text_size, antialias, color, background_color, font_path)

    def add_text(self, status, text, text_size, antialias=True, color=White, background_color=None, font_path=None):
        super().add_text(status, text, text_size, antialias, color, background_color, font_path)
        self.text_args[status] = [text, text_size, antialias, color, background_color, font_path]

    def update_text(self, status, text) -> None:
        self.add_text(status, text, *self.text_args[status][1:])

    def update_size(self, status, size: int) -> None:
        self.add_text(status, self.text_args[status][0], size, *self.text_args[status][2:])

    def set_status(self, status: str, surface_position = (0, 0), surface_size = (0, 0)):
        super().set_status(status)

        if self.isCentered and status in self.states:
            c = (surface_position[0] + surface_size[0] / 2, surface_position[1] + surface_size[1] / 2)
            rect = self.states[status].get_rect(center=c)
            self.transform.set_position(rect.topleft)