import pygame

from state_object.button import Button
from pygame_core.unity.components.transform import Transform
from ui_widgets.text_object import TextObject

from guiobject import GuiObject


def make_factory(assets):
    def make_gui_object(cfg: dict, parent: Transform) -> GuiObject:
        pos          = cfg["position"]
        size         = tuple(cfg["size"]) if cfg["size"] != "WINDOW" else parent
        asset        = cfg.get("asset")
        hover        = cfg.get("hover")
        extra_states = cfg.get("states", {})
        nine_slice   = cfg.get("nine_slice", 0)

        obj = GuiObject(parent, pos, size, asset, nine_slice, hover_image_path=hover)
        for state_key, state_cfg in extra_states.items():
            state_hover = assets.image_path(state_cfg["hover"]) if state_cfg.get("hover") else None
            obj.add_state(state_key, assets.image_path(state_cfg["asset"]), state_hover)
        return obj
    return make_gui_object


def make_text_factory(assets):
    def make_text_object(cfg: dict, parent: Transform) -> TextObject:
        font_key  = cfg.get("font", "Arial")
        font_size = cfg.get("font_size", 32)
        try:
            font = pygame.font.Font(str(assets.font_path(font_key)), font_size)
        except KeyError:
            font = pygame.font.SysFont(font_key, font_size)
        return TextObject(
            parent,
            cfg["position"],
            cfg["text"],
            font,
            cfg.get("color", [255, 255, 255]),
            cfg.get("background_color", None),
        )
    return make_text_object

def make_menu_factory(assets, screen_size, font_path):
    from menu import Menu
    btn_factory = make_button_factory(assets)

    def make_menu(cfg: dict, parent) -> Menu:
        return Menu(
            assets.image_path("blue_button"),
            cfg.get("title", ""),
            30, "white", font_path,
            assets.image_path("grey_panel"),
            (400, 60), "blue_button", "yellow_button",
            tuple(cfg.get("buttons", [])),
            30, "gray", "white", "kenvector_future",
            screen_size, btn_factory,
            panel_height=cfg.get("panel_height"),
        )
    return make_menu


def make_button_factory(assets):
    def make_button(cfg: dict, parent: Transform) -> Button:
        position = cfg["position"]
        size = tuple(cfg["size"]) if cfg["size"] != "WINDOW" else parent
        text = cfg.get("text", "")
        selected_text = cfg.get("selected_text", text)
        text_color = cfg.get("text_color", [255, 255, 255])
        selected_text_color = cfg.get("selected_text_color", text_color)
        paths = cfg.get("paths", {})
        paths_full = {}

        font_key  = cfg.get("font", "Arial")
        font_size = cfg.get("font_size", 32)
        try:
            font = pygame.font.Font(str(assets.font_path(font_key)), font_size)
        except KeyError:
            font = pygame.font.SysFont(font_key, font_size)

        for key, path in paths.items():
            paths_full[key] = assets.image_path(path)

        return Button(position,
                        size,
                        paths_full,
                        text,
                        selected_text,
                        font,
                        text_color,
                        selected_text_color,
                        parent=parent)
    return make_button