from dataclasses import dataclass, field
import pygame
from pygame_core.asset_path import AssetPath


@dataclass
class TextSettings:
    font: pygame.Font
    color: tuple | str | list = field(default_factory=lambda: [255, 255, 255])
    background_color: tuple | str | list | None = None


@dataclass
class ButtonSettings:
    paths: dict
    font: pygame.Font
    text_color: tuple | str | list = field(default_factory=lambda: [255, 255, 255])
    selected_text_color: tuple | str | list | None = None


@dataclass
class TitleSettings:
    image_path: AssetPath
    font: pygame.Font
    text_color: tuple | str | list = field(default_factory=lambda: [255, 255, 255])


@dataclass
class MenuSettings:
    title: TitleSettings
    button: ButtonSettings
    panel_image_path: AssetPath
    button_size: tuple