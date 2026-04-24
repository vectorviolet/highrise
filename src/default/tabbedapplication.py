from typing import override
from pygame_core.application import Application

try:
    import pygame, sys, os
    from pygame import mixer

    from src.default.buttonxx import Buttonxx
    from pygame_core.color import White
    from src.default.text import Text
    from src.default.object import Object
except Exception as error:
    print("An error occurred during importing packages:", error)

class TabbedApplication(dict[str: pygame.Surface], Application):
    def __init__(self, size: tuple[int, int] = (640, 480), title: str = "Game", fps: int = 60, background_colors: list = {}) -> None:
        super().__init__()
        Application.__init__(self, size, title, fps)
        self.set_size(size)
        self.open_window()
        self.set_background_color(background_colors)
        self.tab = ""

    @override
    def _handle_event(self, event: pygame.event.Event) -> None:
        Application._handle_event(self, event)

        if self.tab in self:
            for obj in self[self.tab].values():
                obj.handle_events(event, self.mouse.position)

    @staticmethod
    def play_sound(channel: int, sound_path, volume: float, loops=0) -> None:
        mixer.Channel(channel).play(mixer.Sound(sound_path), loops)
        TabbedApplication.set_volume(channel, volume)

    @staticmethod
    def set_volume(channel: int, volume: float):
        if volume < 0:
            volume = 0

        if volume > 1:
            volume = 1

        mixer.Channel(channel).set_volume(volume)

    def open_window(self) -> None:
        self.window = pygame.display.set_mode(self.size)

    @staticmethod
    def center_window() -> None:
        os.environ['SDL_VIDEO_CENTERED'] = '1'

    def set_background_color(self, colors: list = {}) -> None:
        self.background_colors = colors

    def add_object(self, tab: str, name: str, obj: Object) -> None:
        self.add_tab(tab)
        self[tab][name] = obj

    def create_object(self, tab: str, name: str, *args) -> None:
        new_object = Object(*args)
        self.add_object(tab, name, new_object)

    def create_button(self, tab: str, name: str, *args, **kwargs) -> None:
        self.add_tab(tab)
        new_button = Buttonxx(name, *args, **kwargs)
        self[tab][name] = new_button

    def create_text(self, tab: str, name: str, position, text, text_size, antialias=True, color=White, background_color=None, font_path=None, is_centered=False, status="Normal") -> None:
        self.add_tab(tab)
        new_text = Text(position, text, text_size, antialias, color, background_color, font_path, is_centered, status)
        self[tab][name] = new_text

    def add_tab(self, name: str) -> None:
        if name not in self:
            self[name] = {}

    def open_tab(self, tab: str) -> None:
        self.tab = tab

    @staticmethod
    def set_cursor_visible(value=True) -> None:
        pygame.mouse.set_visible(value)

    def set_cursor_image(self, image: Object) -> None:
        self.cursor = image

    def draw(self) -> None:
        if self.tab in self.background_colors:
            self.window.fill(self.background_colors[self.tab])

        if self.tab in self:
            for obj in self[self.tab].values():
                obj.draw(self.window)

        if hasattr(self, "cursor"):
            self.cursor.draw(self.window)

        pygame.display.update()
