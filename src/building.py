from sound_manager import SoundManager
from pygame import Vector2
from tile import Tile
from pygame_core.asset_path import ImagePath, SoundPath
from object import Object
from untiy.components.rigidbody2d import Rigidbody2D

ages = ["wood", "rock", "sand", "stone"]

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
        self.get_component(Rigidbody2D).set_velocity((0, 0))

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
        direction = self.target_position - Vector2(self.rect.topleft)
        self.get_component(Rigidbody2D).set_velocity(direction.normalize() * 8)

    def level_up(self, sacrificial_building) -> None:
        sacrificial_building.set_target_tile(self.tile)
        sacrificial_building.destroy(self)

    def destroy(self, new_building) -> None:
        self.new_building = new_building
        self.should_destroy = True

class Buildings(list[Building]):
    def __init__(self, sfx_volume: 100) -> None:
        self.max_age_number = len(ages) - 1
        self.sfx_volume = sfx_volume

        super().__init__()

    def set_age(self, age_number):

        if age_number <= self.max_age_number:
            self.age_number = age_number

            for i, building in enumerate(self):
                self[i] = Building(building.level, self.age_number, building.tile)

    def is_moving(self) -> bool:
        return any(b.get_component(Rigidbody2D).velocity != Vector2(0, 0) for b in self)

    def get_age_cost(self):
        return (self.age_number + 1) * 1000

    def get_build_cost(self):
        return (self.age_number + 1) * 100

    def control_moving(self):
        for building in self:
            if building.get_component(Rigidbody2D).velocity == Vector2(0, 0):
                if building.should_destroy:
                    self.remove(building)
                    self.remove(building.new_building)
                    self.append(Building(building.level + 1, building.age_number, building.tile))
                    self.sort(key=lambda b: b.tile.column_number)

                    sound = SoundPath("rollover2")
                    SoundManager.play_sound(1, sound, self.sfx_volume)
                else:
                    if building.tile.selected and building.tile.rect == building.tile.selected_rect:
                        building.rect.topleft = (int(building.selected_position.x), int(building.selected_position.y))
                    else:
                        building.rect.topleft = (int(building.unselected_position.x), int(building.unselected_position.y))
            else:
                tp = building.target_position
                p = Vector2(building.rect.topleft)
                v = building.get_component(Rigidbody2D).velocity
                x_done = v.x == 0 or (v.x > 0 and p.x >= tp.x) or (v.x < 0 and p.x <= tp.x)
                y_done = v.y == 0 or (v.y > 0 and p.y >= tp.y) or (v.y < 0 and p.y <= tp.y)
                if x_done and y_done:

                    building.get_component(Rigidbody2D).set_velocity(Vector2(0, 0))

    def draw(self, surface):
        self.control_moving()

        for building in self:
            building.draw(surface)