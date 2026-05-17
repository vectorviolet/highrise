import pygame

from state_object.button import Button
from pygame_core.font import load_font
from pygame_core.unity.components.transform import Transform
from ui_widgets.text_object import TextObject

from guiobject import GuiObject
from widget_settings import TextSettings, ButtonSettings, TitleSettings, MenuSettings


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
        settings = TextSettings(
            font=load_font(cfg, assets),
            color=cfg.get("color", [255, 255, 255]),
            background_color=cfg.get("background_color"),
        )
        return TextObject(
            parent,
            cfg["position"],
            cfg["text"],
            settings.font,
            settings.color,
            settings.background_color,
        )
    return make_text_object


def make_button_factory(assets):
    def make_button(cfg: dict, parent: Transform) -> Button:
        settings = ButtonSettings(
            paths={k: assets.image_path(v) for k, v in cfg.get("paths", {}).items()},
            font=load_font(cfg, assets),
            text_color=cfg.get("text_color", [255, 255, 255]),
            selected_text_color=cfg.get("selected_text_color"),
        )

        position = cfg["position"]
        size = tuple(cfg["size"]) if cfg["size"] != "WINDOW" else parent
        text = cfg.get("text", "")
        selected_text = cfg.get("selected_text", text)
        selected_color = settings.selected_text_color if settings.selected_text_color is not None else settings.text_color

        return Button(
            position, size, settings.paths,
            text, selected_text, settings.font,
            settings.text_color, selected_color,
            parent=parent,
        )
    return make_button


def make_menu_factory(assets, screen_size):
    from menu import Menu
    from menu_builder import MenuBuilder

    def make_menu(cfg: dict, parent) -> Menu:
        settings = MenuSettings(
            title=TitleSettings(
                image_path=assets.image_path(cfg["title_image"]),
                font=load_font(cfg, assets, "title_font", "title_text_size"),
                text_color=cfg["title_text_color"],
            ),
            button=ButtonSettings(
                paths={
                    "default": assets.image_path(cfg["button_image"]),
                    "hover":   assets.image_path(cfg["button_hover_image"]),
                },
                font=load_font(cfg, assets, "button_font", "button_text_size"),
                text_color=cfg["button_text_color"],
                selected_text_color=cfg["button_selected_text_color"],
            ),
            panel_image_path=assets.image_path(cfg["panel_image"]),
            button_size=tuple(cfg["button_size"]),
        )
        return MenuBuilder(
            settings=settings,
            title_text=cfg.get("title", ""),
            button_texts=tuple(cfg.get("buttons", [])),
            screen_size=screen_size,
            assets=assets,
            panel_height=cfg.get("panel_height"),
        ).build()
    return make_menu