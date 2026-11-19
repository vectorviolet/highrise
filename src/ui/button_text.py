"""Text on a button that shows its yellow face (hover or keyboard focus) in dark navy.

Every button's hover face is `yellow_button` (#FFCC00). White on it is 1.5:1, navy
#1E1D3B is 10.7:1; text on the blue, red and green faces stays white. pygamine's TextObject
has one color, but it already switches *state* with its button's hover, so a ButtonText has a
"hover" state whose text mirrors the default one and takes the navy color there.
"""

from collections.abc import Callable

from pygamine import AssetManager, TextObject, Transform, load_font

# The text color on a yellow face (#1E1D3B).
YELLOW_TEXT_COLOR = (30, 29, 59)


class ButtonText(TextObject):
    def __init__(self, *args, hover_color=YELLOW_TEXT_COLOR, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._normal_color = self.color
        self._hover_color = self._parse_color(hover_color)
        # A text with its own hover text (a price) keeps it; the others show the same text.
        self.states.setdefault("hover", self.states["default"])

    def _set_state_text(self, target: str, text: str) -> None:
        mirrored = (
            target == "default" and self.states.get("hover") == self.states["default"]
        )
        super()._set_state_text(target, text)
        if mirrored:
            super()._set_state_text("hover", text)

    def set_state(self, state: str | None) -> None:
        # The color first: set_state() re-renders the text once, with it.
        self.color = self._hover_color if state == "hover" else self._normal_color
        super().set_state(state)

    def _resolve_state_from(self, parent) -> str | None:
        # The button's yellow face also shows while the keyboard has it focused.
        if getattr(parent, "focused", False):
            return "hover"
        return super()._resolve_state_from(parent)


def make_button_text_factory(
    assets: AssetManager,
) -> Callable[[dict, Transform], ButtonText]:
    """A panels.yaml `type: button_text` object: like pygamine's `text` type, plus an optional
    `hover_color` (default YELLOW_TEXT_COLOR)."""

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
            hover_color=cfg.get("hover_color", YELLOW_TEXT_COLOR),
        )

    return make_button_text
