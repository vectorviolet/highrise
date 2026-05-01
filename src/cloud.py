#-# Import Packages #-#
from default.object import Object
import random
from pygame_core.asset_path import ImagePath, AssetPath
from untiy.rigidbody2d import Rigidbody2D


class Cloud(Object):
    def __init__(self, image_path: AssetPath, surface_size: tuple, size=(100, 100)):
        x = random.randint(0, surface_size[0] - 101)
        y = random.randint(0, surface_size[1] - 101)
        super().__init__((x, y), size, {"Normal": image_path})
        self.get_component(Rigidbody2D).set_velocity((random.choice([1/6, 1/7, 1/8, 1/9, 1/10, 1/11, 1/12, -1/6, -1/7, -1/8 -1/9, -1/10, -1/11 -1/12]), 0))

class GameClouds(list[Cloud]):
    def __init__(self, count, surface_size) -> None:
        super().__init__()
        self.surface_size = surface_size
        self.count = count
        self.create_clouds()

    def create_clouds(self):
        for i in range(self.count):
            cloud = Cloud(ImagePath("cloud"), self.surface_size)
            self.append(cloud)
    def update(self) -> None:
        for cloud in self:
            velocity = cloud.get_component(Rigidbody2D).velocity
            xvel = velocity.x
            position = cloud.transform
            width = cloud.transform.width
            a = self.surface_size[0] - width
            is_left_exit = a >= position.x + xvel > self.surface_size[0] - width and xvel > 0
            is_right_exit = xvel <= position.x < 0 and xvel < 0
            if is_left_exit:
                new_cloud = Cloud(ImagePath("cloud"), self.surface_size)
                new_cloud.transform.topleft = (position.x - self.surface_size[0], position.y)
                new_cloud.get_component(Rigidbody2D).set_velocity(velocity)
                self.append(new_cloud)
            elif is_right_exit:
                new_cloud = Cloud(ImagePath("cloud"), self.surface_size)
                new_cloud.transform.topleft = (position.x + self.surface_size[0], position.y)
                new_cloud.get_component(Rigidbody2D).set_velocity(velocity)
                self.append(new_cloud)

            if position.x >= self.surface_size[0] or position.x < -width:
                self.remove(cloud)

            cloud.update()

    def draw(self, surface) -> None:
        for cloud in self:
            cloud.draw(surface)

class CloudAnimation(list[Cloud]):
    def __init__(self, surface_size):
        super().__init__()
        self.surfaceSize = surface_size

    def create_clouds(self):
        for i in range(100):
            cloud = Cloud(ImagePath("cloud"), self.surfaceSize, (200, 200))
            if cloud.transform.x <= self.surfaceSize[0]/2:
                cloud.get_component(Rigidbody2D).set_velocity((-10, 0))
            else:
                cloud.get_component(Rigidbody2D).set_velocity((10, 0))

            self.append(cloud)

    def update(self) -> None:
        for cloud in self:
            if cloud.transform.x >= self.surfaceSize[0] or cloud.transform.x <= -cloud.width:
                self.remove(cloud)

            cloud.update()

    def draw(self, surface):
        for cloud in self:
            cloud.draw(surface)