class Player:
    def __init__(self) -> None:
        self.money = 0

    def can_afford(self, cost: int) -> bool:
        return self.money >= cost

    def spend(self, amount: int) -> bool:
        if self.money < amount:
            return False
        self.money -= amount
        return True

    def earn(self, amount: int) -> None:
        self.money += amount