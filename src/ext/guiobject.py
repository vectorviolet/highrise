from typing import Union, Any
import os
from pygame_core.asset_path import ImagePath
from pygame_core.unity.components.transform import Transform
from state_object import StateObject

PathLike = Union[str, ImagePath, os.PathLike]


class GuiObject(StateObject):
    def __init__(self, parent: Transform = None,
                 pos=("CENTER", "CENTER"),
                 size=(0, 0),
                 image_path: PathLike = None,
                 nine_slice: int = 0,
                 hover_image_path: PathLike = None) -> None:
        if not isinstance(size, tuple) or not all(isinstance(v, (int, float)) for v in size):
            size = (0, 0)
        super().__init__(pos, size, None, parent, True, nine_slice)
        if image_path is not None:
            self.add_image(None, image_path)
        if hover_image_path is not None:
            self.add_hover_image(None, hover_image_path)

    def add_state(self, state: Any, image_path: PathLike, hover_image_path: PathLike = None) -> None:
        self.add_image(state, image_path)
        if hover_image_path is not None:
            self.add_hover_image(state, hover_image_path)

    def handle_event(self, event, mouse_pos: tuple) -> None:
        self._hovered = self.is_mouse_over(mouse_pos)