from dataclasses import dataclass
from typing import Callable

from pygame import Vector2
from gameplay.tiles.tile import Tile
from pygamine import ImagePath
from pygamine import StateObject
from pygamine import Rigidbody2D

AGES = ["wood", "rock", "sand", "stone"]


@dataclass
class _MoveAxis:
    line_count: int
    line_length: int
    get_line: Callable
    get_pos: Callable
    get_tile: Callable
    reverse: bool


class Building(StateObject):
    def __init__(self, level, age_number, tile: Tile) -> None:
        self.tile = tile
        self.age_number = age_number
        self.age = AGES[age_number]
        self.selected = False
        self.should_destroy = False
        self.cooldown = 2
        self.level = level
        self.speed = (self.level * 2 * (age_number + 1)) - 1
        self.sell_price = self.level * (self.age_number + 1) * 70
        self.__set_size()
        self.set_position_from_tile(self.tile)
        super().__init__(
            pos=self.unselected_position,
            size=self.size,
            image_path=self.get_image_path(),
        )
        self.add_component(Rigidbody2D).set_velocity((0, 0))
        self.on_payout: Callable[[int], None] | None = None
        self.invoke_repeating(self._payout, delay=self.cooldown, interval=self.cooldown)

    def _payout(self) -> None:
        if self.on_payout:
            self.on_payout(self.cooldown * self.speed)

    @property
    def rigidbody(self) -> Rigidbody2D:
        rb = self.get_component(Rigidbody2D)
        assert rb is not None, "Building requires a Rigidbody2D"
        return rb

    def get_image_path(self) -> ImagePath:
        return ImagePath("level" + str(self.level), "buildings/" + self.age)

    def __set_size(self) -> None:
        self.floor_count = (self.level + 1) // 2
        self.size = self.width, self.height = (50, 75 + (self.floor_count - 1) * 23)

    def set_position_from_tile(self, tile: Tile) -> None:
        x, y = tile.rect.x + 43, tile.rect.y - 23 - (self.floor_count - 1) * 23
        self.unselected_position = Vector2(x, y)
        self.selected_position = Vector2(x, y - 10)

    def set_target_tile(self, target_tile: Tile) -> None:
        self.tile = target_tile
        self.set_position_from_tile(target_tile)
        self.target_position = self.unselected_position
        direction = self.target_position - Vector2(self.rect.topleft)
        self.rigidbody.set_velocity(direction.normalize() * 8)

    def level_up(self, sacrificial_building) -> None:
        sacrificial_building.set_target_tile(self.tile)
        sacrificial_building.merge_into(self)

    def merge_into(self, target: "Building") -> None:
        self.merge_target = target
        self.should_destroy = True

    def has_arrived(self) -> bool:
        target = self.target_position
        position = Vector2(self.rect.topleft)
        velocity = self.rigidbody.velocity
        x_done = (
            velocity.x == 0
            or (velocity.x > 0 and position.x >= target.x)
            or (velocity.x < 0 and position.x <= target.x)
        )
        y_done = (
            velocity.y == 0
            or (velocity.y > 0 and position.y >= target.y)
            or (velocity.y < 0 and position.y <= target.y)
        )
        return x_done and y_done


class Buildings(list[Building]):
    def __init__(
        self,
        *,
        on_merge: Callable[[], None] | None = None,
        on_payout: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__()
        self.max_age_number = len(AGES) - 1
        self.age_number = 0
        self.on_merge = on_merge
        self.on_payout = on_payout

    def create(
        self, level: int, tile: Tile, *, age_number: int | None = None
    ) -> Building:
        """Construct a building with the collection's payout callback, without adding it."""
        age = self.age_number if age_number is None else age_number
        building = Building(level, age, tile)
        building.on_payout = self.on_payout
        return building

    def set_age(self, age_number) -> None:
        if age_number <= self.max_age_number:
            self.age_number = age_number

            for i, building in enumerate(self):
                self[i] = self.create(building.level, building.tile)

    def is_moving(self) -> bool:
        return any(b.rigidbody.velocity != Vector2(0, 0) for b in self)

    def get_age_cost(self) -> int:
        return (self.age_number + 1) * 1000

    def get_build_cost(self) -> int:
        return (self.age_number + 1) * 100

    def control_moving(self) -> None:
        # Merges are collected and applied after the loop: removing from the
        # list while iterating over it would skip the next building.
        settled_merges: list[Building] = []
        for building in self:
            if building.rigidbody.velocity == Vector2(0, 0):
                if building.should_destroy:
                    settled_merges.append(building)
                else:
                    self._snap_idle(building)
            elif building.has_arrived():
                building.rigidbody.set_velocity(Vector2(0, 0))
                building.rect.topleft = (
                    int(building.target_position.x),
                    int(building.target_position.y),
                )

        for building in settled_merges:
            self._finish_merge(building)
        if settled_merges:
            self.sort(key=lambda b: b.tile.column_number)

    @staticmethod
    def _snap_idle(building: Building) -> None:
        position = (
            building.selected_position
            if building.tile.selected
            and building.tile.rect == building.tile.selected_rect
            else building.unselected_position
        )
        building.rect.topleft = (int(position.x), int(position.y))

    def _finish_merge(self, building: Building) -> None:
        self.remove(building)
        self.remove(building.merge_target)
        self.append(
            self.create(
                building.level + 1, building.tile, age_number=building.age_number
            )
        )
        if self.on_merge is not None:
            self.on_merge()

    def update(self) -> None:
        for building in self:
            building.update()
        self.control_moving()

    def draw(self, surface) -> None:
        for building in self:
            building.draw(surface)

    def move(self, rotation: str, tilemap, max_level: int) -> None:
        if self.is_moving():
            return
        axis = self._axis_for(rotation, tilemap)
        for line in range(axis.line_count):
            self._resolve_line(line, axis, max_level)
        self.sort(key=lambda b: b.tile.column_number)

    @staticmethod
    def _axis_for(rotation: str, tilemap) -> _MoveAxis:
        reverse = rotation in ("down", "right")
        if rotation in ("up", "down"):
            return _MoveAxis(
                line_count=tilemap.column_count,
                line_length=tilemap.row_count,
                get_line=lambda b: b.tile.column_number - 1,
                get_pos=lambda b: b.tile.row_number - 1,
                get_tile=lambda line, pos: tilemap[pos][line],
                reverse=reverse,
            )
        return _MoveAxis(
            line_count=tilemap.row_count,
            line_length=tilemap.column_count,
            get_line=lambda b: b.tile.row_number - 1,
            get_pos=lambda b: b.tile.column_number - 1,
            get_tile=lambda line, pos: tilemap[line][pos],
            reverse=reverse,
        )

    @staticmethod
    def _can_merge(
        previous: "Building | None", building: "Building", max_level: int
    ) -> bool:
        return (
            previous is not None
            and previous.level == building.level
            and previous.level < max_level
        )

    def _resolve_line(self, line: int, axis: _MoveAxis, max_level: int) -> None:
        line_buildings = sorted(
            [b for b in self if axis.get_line(b) == line],
            key=axis.get_pos,
            reverse=axis.reverse,
        )
        if not line_buildings:
            return

        previous: Building | None = None
        target = 0
        for building in line_buildings:
            if previous is not None and self._can_merge(previous, building, max_level):
                previous.level_up(building)
                previous = None
                continue
            target_pos = axis.line_length - target - 1 if axis.reverse else target
            if axis.get_pos(building) != target_pos:
                building.set_target_tile(axis.get_tile(line, target_pos))
            previous = building
            target += 1
