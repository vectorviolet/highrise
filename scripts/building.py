#-# Import Packages #-#
from images import *
from scripts.tile import *
from scripts.default.application import *
from scripts.default.path import *

ages = ["wood", "rock", "sand", "stone"]

#-# Building Class #-#
class Building(Object):

    def __init__(self, level, ageNumber, tile: Tile) -> None:
        
        self.tile = tile
        self.ageNumber = ageNumber
        self.age = ages[ageNumber]
        self.selected = False
        self.destroy = False
        self.cooldown = 2
        self.lastTime = None
        self.level = level
        self.speed = (self.level * 2 * (ageNumber + 1)) - 1 # cash per second
        self.sellPrice = self.level*(self.ageNumber+1)*70
        self.__SetSize()
        self.SetPositionFromTile(self.tile)
        super().__init__(self.unselectedPosition, self.size, {"Normal" : self.GetImagePath()})
        #self.rect = self.GetRect()
        self.SetVelocity((0, 0))

    def GetImagePath(self) -> str:
        
        return ImagePath("level" + str(self.level), "buildings/" + self.age)

    def __SetSize(self) -> None:

        if self.level == 1 or self.level == 2:
            self.floorCount = 1
        elif self.level == 3 or self.level == 4:
            self.floorCount = 2
        elif self.level == 5 or self.level == 6:
            self.floorCount = 3
        
        self.size = self.width, self.height = (50, 75 + (self.floorCount - 1) * 23)        

    def SetPositionFromTile(self, tile: Tile) -> None:

        x, y = tile.x + 43, tile.y - 23 - (self.floorCount - 1) * 23
        
        self.unselectedPosition = Vector2(x, y)
        self.selectedPosition = Vector2(x, y - 10)

    def SetTargetTile(self, targetTile: Tile) -> None:

        self.tile = targetTile
        self.SetPositionFromTile(targetTile)
        self.targetPosition = self.unselectedPosition
        direction = self.targetPosition - self.position # This vector points from the mouse pos to the target.
        self.velocity = direction.normalize() * 8 # The velocity is the normalized direction vector scaled to the desired length.

    def LevelUp(self, sacrificialBuilding) -> None:
        sacrificialBuilding.SetTargetTile(self.tile)
        sacrificialBuilding.Destroy(self)

    def Destroy(self, newBuilding) -> None:
        
        self.newBuilding = newBuilding
        self.destroy = True

# Buildings Class #-#
class Buildings(list[Building]):

    def __init__(self, SFXVolume: 100) -> None:

        self.maxAgeNumber = len(ages) - 1
        self.SFXVolume = SFXVolume

        super().__init__()

    def SetAge(self, ageNumber):

        if ageNumber <= self.maxAgeNumber:

            self.ageNumber = ageNumber

            for i, building in enumerate(self):

                self[i] = Building(building.level, self.ageNumber, building.tile)

    def GetAgeCost(self):

        return (self.ageNumber + 1) * 1000

    def GetBuildCost(self):

        return (self.ageNumber + 1) * 100

    def HandleEvents(self, event, mousePosition) -> None:

        pass

    def ControlMoving(self):

        for building in self:

            if building.velocity == Vector2(0, 0):

                if building.destroy:

                    self.remove(building)
                    self.remove(building.newBuilding)
                    self.append(Building(building.level + 1, building.ageNumber, building.tile))
                    self.sort(key=lambda building: building.tile.columnNumber)
                    
                    sound = SoundPath("rollover2",)
                    Application.PlaySound(1, sound, self.SFXVolume)

                else:

                    if building.tile.selected and building.tile.rect == building.tile.selectedRect:

                        building.position = building.selectedPosition

                    else:

                        building.position = building.unselectedPosition
            else:

                if (building.targetPosition.x < building.position.x < building.targetPosition.x + building.velocity.x or building.targetPosition.x > building.position.x > building.targetPosition.x + building.velocity.x) and (building.targetPosition.y < building.position.y < building.targetPosition.y + building.velocity.y or building.targetPosition.y > building.position.y > building.targetPosition.y + building.velocity.y):
            
                    building.velocity = Vector2(0, 0)

    def Draw(self, surface):

        for building in self:

            self.ControlMoving()
            building.Draw(surface)