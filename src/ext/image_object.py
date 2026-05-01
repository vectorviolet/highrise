from typing import Union
import os
import pygame
from pygame_core.asset_path import ImagePath
from pygame_core.image import load_image
from pygame_core.utils import MouseInteractive

from ext.image import nine_slice_scale, scale_surface

PathLike = Union[str, ImagePath, os.PathLike]

class ImageObject(MouseInteractive):
	def __init__(self, path: PathLike, pos: tuple[int, int],
	             size: tuple[int, int] = (0, 0), nine_slice: int = 0) -> None:
		loaded = load_image(path)
		if size != (0, 0):
			self.image = nine_slice_scale(loaded, size, nine_slice) if nine_slice > 0 else scale_surface(loaded, size)
		else:
			self.image = loaded
		self.rect = self.image.get_rect(topleft=pos)

	def draw(self, surface: pygame.Surface) -> None:
		surface.blit(self.image, self.rect)
