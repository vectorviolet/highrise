from typing import Union, Any
import os
import pygame
from pygame_core.asset_path import ImagePath
from pygame_core.utils import Centerable
from ext.image_object import ImageObject
from untiy.components.transform import Transform

PathLike = Union[str, ImagePath, os.PathLike]


class GuiObject(Centerable):
	def __init__(self, parent: Transform = None,
	             pos=("CENTER", "CENTER"),
	             size=(None, None),
	             image_path: PathLike = None,
	             nine_slice: int = 0) -> None:
		self._pos = self.resolve_pos(pos, parent.size, size)
		self._size = size
		self._nine_slice = nine_slice
		self._state: Any = None
		self.images: dict[Any, ImageObject] = {}
		if image_path is not None:
			self.images[None] = ImageObject(image_path, self._pos, self._size, nine_slice)

	def add_state(self, state: Any, image_path: PathLike) -> None:
		self.images[state] = ImageObject(image_path, self._pos, self._size, self._nine_slice)

	def set_state(self, state: Any) -> None:
		self._state = state

	@property
	def _active_image(self) -> ImageObject:
		return self.images[self._state]

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
			self._hover_images[None] = ImageObject(hover_image_path, self._pos, self._size, nine_slice)

	def add_state(self, state: Any, image_path: PathLike, hover_image_path: PathLike = None) -> None:
		super().add_state(state, image_path)
		if hover_image_path is not None:
			self._hover_images[state] = ImageObject(hover_image_path, self._pos, self._size, self._nine_slice)

	@property
	def _active_image(self) -> ImageObject:
		if self._hovered and self._state in self._hover_images:
			return self._hover_images[self._state]
		return self.images[self._state]

	def handle_event(self, event, mouse_pos: tuple) -> None:
		self._hovered = self.images[self._state].is_mouse_over(mouse_pos)