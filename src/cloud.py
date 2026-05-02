#-# Import Packages #-#
import random

from pygame_core.image import load_image
from pygame_core.asset_path import ImagePath, AssetPath
from untiy.game_object_list import GameObjectList
from untiy.gameobject import GameObject
from untiy.components.rigidbody2d import Rigidbody2D
from untiy.components.sprite_renderer2d import SpriteRenderer2D


class Cloud(GameObject):
    def __init__(self, image_path: AssetPath, surface_size: tuple, size=(100, 100)):
        super().__init__()

        x = random.randint(0, surface_size[0] - 101)
        y = random.randint(0, surface_size[1] - 101)
        self.rect.size = size
        self.rect.set_position((x, y))
        self.add_component(SpriteRenderer2D).set_image(load_image(image_path, size))
        self.add_component(Rigidbody2D).set_velocity((random.choice([1/6, 1/7, 1/8, 1/9, 1/10, 1/11, 1/12, -1/6, -1/7, -1/8, -1/9, -1/10, -1/11, -1/12]), 0))
        self.has_companion = False

class GameClouds(GameObjectList):
    _cloud_image = ImagePath("cloud")

    def __init__(self, count, surface_size) -> None:
        super().__init__()
        self.surface_size = surface_size
        self.count = count
        self.create_clouds()

    def create_clouds(self):
        for _ in range(self.count):
            self.append(self.new())

    def new(self):
        return Cloud(self._cloud_image, self.surface_size)

    def update(self) -> None:
        to_add = []
        to_remove = []

        for cloud in self:
            rb = cloud.get_component(Rigidbody2D)
            velocity = rb.velocity
            xvel = velocity.x
            x = cloud.rect.x
            y = cloud.rect.y
            width = cloud.rect.width
            W = self.surface_size[0]

            if not cloud.has_companion:
                if xvel > 0 and x + width > W:
                    cloud.has_companion = True
                    companion = self.new()
                    companion.rect.topleft = (x - W, y)
                    companion.get_component(Rigidbody2D).set_velocity(velocity)
                    to_add.append(companion)
                elif xvel < 0 and x < 0:
                    cloud.has_companion = True
                    companion = self.new()
                    companion.rect.topleft = (x + W, y)
                    companion.get_component(Rigidbody2D).set_velocity(velocity)
                    to_add.append(companion)

            cloud.update()

            if cloud.rect.x >= W or cloud.rect.x + width < 0:
                to_remove.append(cloud)

        for cloud in to_add:
            self.append(cloud)
        for cloud in to_remove:
            self.remove(cloud)

class CloudAnimation(GameObjectList):
    def __init__(self, surface_size):
        super().__init__()
        self.surface_size = surface_size

    def create_clouds(self):
        for _ in range(100):
            cloud = Cloud(ImagePath("cloud"), self.surface_size, (200, 200))
            if cloud.rect.x <= self.surface_size[0] / 2:
                cloud.get_component(Rigidbody2D).set_velocity((-10, 0))
            else:
                cloud.get_component(Rigidbody2D).set_velocity((10, 0))
            self.append(cloud)

    def update(self) -> None:
        W = self.surface_size[0]
        to_remove = [c for c in self if c.rect.x >= W or c.rect.x + c.rect.width <= 0]
        for cloud in to_remove:
            self.remove(cloud)
        super().update()