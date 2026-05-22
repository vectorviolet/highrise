import pygame

from pygame_core.font import load_font
from pygame_core.ui_widgets.text_object import TextObject
from pygame_core.ecs.components.transform import Transform

from ui.guiobject import GuiObject


def make_factory(assets):
    def make_gui_object(cfg: dict, parent: Transform) -> GuiObject:
        pos          = cfg["position"]
        size         = tuple(cfg["size"]) if cfg["size"] != "WINDOW" else parent
        asset        = cfg.get("asset")
        hover        = cfg.get("hover")
        extra_states = cfg.get("states", {})
        nine_slice   = cfg.get("nine_slice", 0)
        anchor       = cfg.get("anchor", "top-left")

        obj = GuiObject(parent, pos, size, asset, nine_slice, hover_image_path=hover, anchor=anchor)
        for state_key, state_cfg in extra_states.items():
            state_hover = assets.image_path(state_cfg["hover"]) if state_cfg.get("hover") else None
            obj.add_state(state_key, assets.image_path(state_cfg["asset"]), state_hover)
        return obj
    return make_gui_object


def make_text_factory(assets):
    def make_text_object(cfg: dict, parent: Transform) -> TextObject:
        return TextObject(
            parent,
            cfg["position"],
            cfg.get("text", ""),
            load_font(cfg, assets),
            cfg.get("color", [255, 255, 255]),
            cfg.get("background_color"),
            padding=cfg.get("padding"),
            anchor=cfg.get("anchor", "top-left"),
            states=cfg.get("states"),
        )
    return make_text_object