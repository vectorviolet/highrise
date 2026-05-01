import pygame

from ext.guiobject import GuiObject, HoverableGuiObject
from ext.text_object import TextObject


def make_factory(assets):
    def make_gui_object(cfg: dict, window_size: tuple) -> GuiObject:
        pos          = cfg["position"]
        size         = tuple(cfg["size"]) if cfg["size"] != "WINDOW" else window_size
        asset        = cfg["asset"]
        hover        = cfg.get("hover")
        extra_states = cfg.get("states", {})
        nine_slice   = cfg.get("nine_slice", 0)

        if hover is not None or extra_states:
            obj = HoverableGuiObject(window_size, pos, size, asset, hover, nine_slice)
            for state_key, state_cfg in extra_states.items():
                state_hover = assets.image_path(state_cfg["hover"]) if state_cfg.get("hover") else None
                obj.add_state(state_key, assets.image_path(state_cfg["asset"]), state_hover)
            return obj
        return GuiObject(window_size, pos, size, asset, nine_slice)
    return make_gui_object


def make_text_factory(assets):
    def make_text_object(cfg: dict, window_size: tuple) -> TextObject:
        font_key  = cfg.get("font", "Arial")
        font_size = cfg.get("font_size", 32)
        try:
            font = pygame.font.Font(str(assets.font_path(font_key)), font_size)
        except KeyError:
            font = pygame.font.SysFont(font_key, font_size)
        return TextObject(
            window_size,
            cfg["position"],
            cfg["text"],
            font,
            cfg.get("color", [255, 255, 255]),
        )
    return make_text_object