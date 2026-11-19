"""Text on a button that shows its yellow face (hover or keyboard focus) in dark navy.

Every button's hover face is `yellow_button` (#FFCC00). White on it is 1.5:1, navy
#1E1D3B is 10.7:1; text on the blue, red and green faces stays white. pygamine's TextObject
has one color, so a ButtonText asks its parent button, once a frame, which face it shows.
"""

from collections.abc import Callable

from pygamine import (
    AssetManager,
    SpriteRenderer2D,
    StateObject,
    TextObject,
    Transform,
    load_font,
)

# The text color on a yellow face (#1E1D3B).
YELLOW_TEXT_COLOR = (30, 29, 59)


class ButtonText(TextObject):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._normal_color = self.color

    def set_color(self, color) -> None:
        """The color on the button's normal face; a yellow face still shows navy."""
        self._normal_color = self._parse_color(color)
        self._apply_color()

    def update(self) -> None:
        super().update()
        self._apply_color()

    def _apply_color(self) -> None:
        color = YELLOW_TEXT_COLOR if self._yellow_face_showing() else self._normal_color
        if color != self.color:
            super().set_color(color)

    def _yellow_face_showing(self) -> bool:
        """True when the parent button shows a face other than its normal one: the hover face,
        for the mouse over it or the keyboard on it, whatever state (on/off) it is in."""
        parent = getattr(self.rect.parent, "game_object", None)
        if not isinstance(parent, StateObject):
            return False
        shown = parent.require_component(SpriteRenderer2D).image
        return shown is not None and shown is not parent.images.get(parent.state)


def make_button_text_factory(
    assets: AssetManager,
) -> Callable[[dict, Transform], ButtonText]:
    """A panels.yaml `type: button_text` object: pygamine's `text` type as a ButtonText.
    (The argument list repeats pygamine's make_text_factory, which builds a fixed class.)"""

    def make_button_text(cfg: dict, parent: Transform) -> ButtonText:
        return ButtonText(
            parent,
            cfg["position"],
            cfg.get("text", ""),
            load_font(cfg, assets),
            cfg.get("color", [255, 255, 255]),
            cfg.get("background_color"),
            padding=cfg.get("padding"),
            anchor=cfg.get("anchor", "top-left"),
            states=cfg.get("states"),
            text_key=cfg.get("text_key"),
            text_params=cfg.get("text_params"),
        )

    return make_button_text
