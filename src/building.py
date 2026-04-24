from pygame import Vector2
from src.tile import Tile
from src.default.application import Application
from game_core.path import *
from src.default.object import Object

ages = ["wood", "rock", "sand", "stone"]

#-# Building Class #-#
class Building(Object):

    def __init__(self, level, age_number, tile: Tile) -> None:

        self.tile = tile
        self.age_number = age_number
        self.age = ages[age_number]
        self.selected = False
        self.should_destroy = False
        self.cooldown = 2
        self.last_time = None
        self.level = level
        self.speed = (self.level * 2 * (age_number + 1)) - 1
        self.sell_price = self.level*(self.age_number+1)*70
        self.__set_size()
        self.set_position_from_tile(self.tile)
        super().__init__(self.unselected_position, self.size, {"Normal" : self.get_image_path()})
        self.set_velocity((0, 0))

    def get_image_path(self) -> str:

        return ImagePath("level" + str(self.level), "buildings/" + self.age)

    def __set_size(self) -> None:

        if self.level == 1 or self.level == 2:
            self.floor_count = 1
        elif self.level == 3 or self.level == 4:
            self.floor_count = 2
        elif self.level == 5 or self.level == 6:
            self.floor_count = 3

        self.size = self.width, self.height = (50, 75 + (self.floor_count - 1) * 23)

    def set_position_from_tile(self, tile: Tile) -> None:

        x, y = tile.x + 43, tile.y - 23 - (self.floor_count - 1) * 23

        self.unselected_position = Vector2(x, y)
        self.selected_position = Vector2(x, y - 10)

    def set_target_tile(self, target_tile: Tile) -> None:

        self.tile = target_tile
        self.set_position_from_tile(target_tile)
        self.target_position = self.unselected_position
        direction = self.target_position - self.position
        self.velocity = direction.normalize() * 8

    def level_up(self, sacrificial_building) -> None:
        sacrificial_building.set_target_tile(self.tile)
        sacrificial_building.destroy(self)

    def destroy(self, new_building) -> None:

        self.new_building = new_building
        self.should_destroy = True

# Buildings Class #-#
class Buildings(list[Building]):

    def __init__(self, sfx_volume: 100) -> None:

        self.maxAgeNumber = len(ages) - 1
        self.sfx_volume = sfx_volume

        super().__init__()

    def set_age(self, age_number):

        if age_number <= self.maxAgeNumber:

            self.age_number = age_number

            for i, building in enumerate(self):

                self[i] = Building(building.level, self.age_number, building.tile)

    def get_age_cost(self):

        return (self.age_number + 1) * 1000

    def get_build_cost(self):

        return (self.age_number + 1) * 100

    def handle_events(self, event, mouse_position) -> None:

        pass

    def control_moving(self):

        for building in self:

            if building.velocity == Vector2(0, 0):

                if building.should_destroy:

                    self.remove(building)
                    self.remove(building.new_building)
                    self.append(Building(building.level + 1, building.age_number, building.tile))
                    self.sort(key=lambda b: b.tile.column_number)

                    sound = SoundPath("rollover2")
                    Application.play_sound(1, sound, self.sfx_volume)

                else:

                    if building.tile.selected and building.tile.rect == building.tile.selected_rect:

                        building.position = building.selected_position

                    else:

                        building.position = building.unselected_position
            else:

                tp = building.target_position
                p = building.position
                v = building.velocity
                if (tp.x < p.x < tp.x + v.x or tp.x > p.x > tp.x + v.x) and \
                   (tp.y < p.y < tp.y + v.y or tp.y > p.y > tp.y + v.y):

                    building.velocity = Vector2(0, 0)

    def draw(self, surface):

        for building in self:

            self.control_moving()
            building.draw(surface)
