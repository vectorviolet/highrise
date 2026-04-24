try:
    import pygame, sys, os
    from pygame import mixer

    from src.default.buttonxx import Buttonxx
    from game_core.color import White
    from src.default.text import Text
    from src.default.object import Object
except Exception as error:
    print("An error occurred during importing packages:", error)

class Application(dict[str : pygame.Surface]):
    def __init__(self, title: str = "Game", size: tuple = (640, 480), background_colors: list = {}, fps: int = 60) -> None:
        super().__init__()
        self.init_pygame()
        self.init_clock()
        self.init_mixer()
        self.set_title(title)
        self.set_size(size)
        self.open_window()
        self.set_fps(fps)
        self.set_background_color(background_colors)
        self.tab = ""

    def run(self) -> None:
        self.is_running = True

        while self.is_running:
            self.clock.tick(self.fps)
            self.mouse_position = pygame.mouse.get_pos()
            self.keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                self.handle_events(event)

            if hasattr(self, "cursor"):
                self.cursor.set_position(self.mouse_position)

            self.draw()

    def handle_events(self, event: pygame.event.Event) -> None:
        if self.tab in self:
            for obj in self[self.tab].values():
                obj.handle_events(event, self.mouse_position)

        self.handle_exit_events(event)

    def handle_exit_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.exit()

    @staticmethod
    def init_pygame() -> None:
        pygame.init()

    @staticmethod
    def init_mixer() -> None:
        pygame.mixer.init()

    def init_clock(self) -> None:
        self.clock = pygame.time.Clock()

    @staticmethod
    def play_sound(channel: int, sound_path, volume: float, loops=0) -> None:
        mixer.Channel(channel).play(mixer.Sound(sound_path), loops)
        Application.set_volume(channel, volume)

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

    def set_fps(self, fps: int) -> None:
        self.fps = fps

    def set_title(self, title: str) -> None:
        self.title = title
        pygame.display.set_caption(self.title)

    def set_size(self, size: tuple) -> None:
        self.size = self.width, self.height = size

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

    def exit(self) -> None:
        self.is_running = False
        pygame.quit()
        sys.exit()

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
