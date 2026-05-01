from pygame import Vector2
from untiy.components import Component

class Rigidbody2D(Component):
	def __init__(self):
		super().__init__()
		self.velocity = Vector2(0, 0)

	def set_velocity(self, velocity: tuple):
		self.velocity = Vector2(velocity)

	def update(self) -> None:
		transform = self.game_object.transform
		new_pos = Vector2(transform.topleft) + self.velocity
		transform.topleft = (int(new_pos.x), int(new_pos.y))