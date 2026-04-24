#-# Import Packages #-#
from src.default.object import *
import random

class Cloud(Object):

    def __init__(self, imagePath: FilePath, surfaceSize: tuple, size=(100, 100)):

        x = random.randint(0, surfaceSize[0] - 101)
        y = random.randint(0, surfaceSize[1] - 101)

        self.set_velocity((random.choice([1/6, 1/7, 1/8, 1/9, 1/10, 1/11, 1/12, -1/6, -1/7, -1/8 -1/9, -1/10, -1/11 -1/12]), 0))

        super().__init__((x, y), size, {"Normal" : imagePath})

class GameClouds(list[Cloud]):

    def __init__(self, count, surfaceSize) -> None:

        super().__init__()

        self.surfaceSize = surfaceSize
        self.count = count

        self.create_clouds()

    def create_clouds(self):

        for i in range(self.count):

            cloud = Cloud(ImagePath("cloud"), self.surfaceSize)
            self.append(cloud)

    def handle_events(self, event, mouse_position):

        pass

    def draw(self, surface) -> None:

        for cloud in self:

            if self.surfaceSize[0] - cloud.width + cloud.velocity[0] >= cloud.position.x > self.surfaceSize[0] - cloud.width and cloud.velocity[0] > 0:

                new_cloud = Cloud(ImagePath("cloud"), self.surfaceSize)
                new_cloud.set_position((cloud.position.x - self.surfaceSize[0], cloud.position.y))
                new_cloud.velocity = cloud.velocity
                self.append(new_cloud)

            elif cloud.velocity[0] <= cloud.position.x < 0 and cloud.velocity[0] < 0:

                new_cloud = Cloud(ImagePath("cloud"), self.surfaceSize)
                new_cloud.set_position((cloud.position.x + self.surfaceSize[0], cloud.position.y))
                new_cloud.velocity = cloud.velocity
                self.append(new_cloud)

            if cloud.position.x >= self.surfaceSize[0] or cloud.position.x < -cloud.width:

                self.remove(cloud)

            cloud.draw(surface)

class CloudAnimation(list[Cloud]):

    def __init__(self, surfaceSize):

        super().__init__()

        self.surfaceSize = surfaceSize

    def create_clouds(self):

        for i in range(100):

            cloud = Cloud(ImagePath("cloud"), self.surfaceSize, (200, 200))

            if cloud.position.x <= self.surfaceSize[0]/2:

                cloud.set_velocity((-10, 0))

            else:

                cloud.set_velocity((10, 0))

            self.append(cloud)

    def handle_events(self, event, mouse_position):

        pass

    def draw(self, surface):

        for cloud in self:

            cloud.draw(surface)

            if cloud.position.x >= self.surfaceSize[0] or cloud.position.x <= -cloud.width:

                self.remove(cloud)
