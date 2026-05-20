import pygame
from pygame_core.asset_manager import AssetManager
from ui.button import Button
from ui.menu import Menu
from ui.state_object import StateObject
from ui.widget_settings import MenuSettings


class MenuBuilder:
    """Computes menu geometry and constructs the title, panel and button widgets."""

    SPACE = 20

    def __init__(
            self,
            settings: MenuSettings,
            title_text: str,
            button_texts: tuple,
            screen_size: tuple,
            assets: AssetManager,
            *,
            panel_height: int = None
            ) -> None:

        self._settings = settings
        self._title_text = title_text
        self._button_texts = button_texts
        self.assets = assets

        space = self.SPACE
        button_count = len(button_texts)
        button_size = settings.button_size

        self._title_size = button_size[0] + space * 2, 70
        panel_size = button_size[0] + space * 2, button_size[1] * button_count + (button_count + 3) * space
        self._panel_size = (panel_size[0], panel_height) if panel_height else panel_size

        size = self._title_size[0], self._title_size[1] + self._panel_size[1] - space / 2
        self._position = (screen_size[0] - size[0]) / 2, (screen_size[1] - size[1]) / 2
        self._panel_position = self._position[0], self._position[1] + self._title_size[1] - space / 2

    def _button_position(self, index: int) -> pygame.math.Vector2:
        button_size = self._settings.button_size
        offset = pygame.math.Vector2(
            self.SPACE,
            self.SPACE * (index + 3 / 2) + button_size[1] * index,
        )
        return offset + self._panel_position

    def _build_title(self) -> Button:
        ts = self._settings.title
        return Button(self._position, self._title_size, {"default": ts.image_path},
                      self._title_text, self._title_text, ts.font,
                      ts.text_color, ts.text_color)

    def _build_buttons(self) -> dict:
        bs = self._settings.button
        button_size = list(self._settings.button_size)
        selected_color = bs.selected_text_color if bs.selected_text_color is not None else bs.text_color
        buttons = {}
        for i, text in enumerate(self._button_texts):
            buttons[text] = Button(
                list(self._button_position(i)),
                button_size,
                dict(bs.paths),
                text, text,
                bs.font,
                bs.text_color, selected_color,
            )
        return buttons

    def build(self) -> "Menu":
        title = self._build_title()
        panel = StateObject(self._panel_position, self._panel_size, {"default": self._settings.panel_image_path})
        buttons = self._build_buttons()
        return Menu(title, panel, buttons, self.assets)

