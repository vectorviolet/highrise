from typing import Union, Any
import os
import pygame
from pygame_core.asset_path import ImagePath
from pygame_core.utils import Centerable
from ext.image_object import ImageObject
from untiy.components.transform import Transform
from untiy.gameobject import GameObject

PathLike = Union[str, ImagePath, os.PathLike]


class GuiObject(GameObject, Centerable):
	def __init__(self, parent: Transform = None,
	             pos=("CENTER", "CENTER"),
	             size=(None, None),
	             image_path: PathLike = None,
	             nine_slice: int = 0) -> None:
		super().__init__()
		self.rect.parent = parent
		self.rect.size = size
		self.rect.set_position(pos)
		self._nine_slice = nine_slice
		self.state: Any = None
		self.images: dict[Any, ImageObject] = {}
		if image_path is not None:
			self.images[None] = ImageObject(image_path, self.rect.topleft, self.rect.size, nine_slice)

	def add_state(self, state: Any, image_path: PathLike) -> None:
		self.images[state] = ImageObject(image_path, self.rect.topleft, self.rect.size, self._nine_slice)

	def set_state(self, state: Any) -> None:
		self.state = state

	@property
	def _active_image(self) -> ImageObject:
		return self.images[self.state]

	def is_mouse_over(self, mouse_pos) -> bool:
		return self._active_image.is_mouse_over(mouse_pos)

	def is_clicked(self, event, mouse_pos) -> bool:
		return self._active_image.is_clicked(event, mouse_pos)

	def draw(self, surface: pygame.Surface) -> None:
		self._active_image.draw(surface)


class HoverableGuiObject(GuiObject):
	def __init__(self, parent: Transform = None,
	             pos=("CENTER", "CENTER"),
	             size=(None, None),
	             image_path: PathLike = None,
	             hover_image_path: PathLike = None,
	             nine_slice: int = 0) -> None:
		super().__init__(parent, pos, size, image_path, nine_slice)
		self._hovered = False
		self._hover_images: dict[Any, ImageObject] = {}
		if hover_image_path is not None:
			self._hover_images[None] = ImageObject(hover_image_path, self.rect.topleft, self.rect.size, nine_slice)

	def add_state(self, state: Any, image_path: PathLike, hover_image_path: PathLike = None) -> None:
		super().add_state(state, image_path)
		if hover_image_path is not None:
			self._hover_images[state] = ImageObject(hover_image_path, self.rect.topleft, self.rect.size, self._nine_slice)

	@property
	def _active_image(self) -> ImageObject:
		if self._hovered and self.state in self._hover_images:
			return self._hover_images[self.state]
		return self.images[self.state]

	def handle_event(self, event, mouse_pos: tuple) -> None:
		self._hovered = self.images[self.state].is_mouse_over(mouse_pos)