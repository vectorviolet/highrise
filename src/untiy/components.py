from __future__ import annotations
import pygame
from pygame_core.utils import Centerable


class Component:
	def __init__(self):
		self.game_object = None

	def get_component(self, component_type: type[Component]) -> Component | None:
		return self.game_object.get_component(component_type)


class Behaviour(Component):
	def __init__(self):
		super().__init__()
		self.enabled: bool = True


class MonoBehaviour(Behaviour):
	def awake(self): ...
	def start(self): ...
	def update(self): ...
	def on_destroy(self): ...


class Transform(Component, pygame.Rect, Centerable):
	def __init__(self,
				 position: tuple = (0, 0),
				 size: tuple = (0, 0),
				 parent: Transform | None = None
				 ):
		Component.__init__(self)
		pygame.Rect.__init__(self, position, size)
		self.parent = parent

	def set_position(self, position: tuple):
		parent_size = self.parent.size if self.parent else self.size
		position = super().resolve_pos(position, parent_size, self.size)
		self.topleft = position

	def update(self): ...

