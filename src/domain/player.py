from typing import Callable


class Player:
    def __init__(self) -> None:
        self._money: int = 0
        self._money_listeners: list[Callable[[int], None]] = []

    @property
    def money(self) -> int:
        return self._money

    @money.setter
    def money(self, value: int) -> None:
        if value == self._money:
            return
        self._money = value
        for cb in self._money_listeners:
            cb(self._money)

    def add_money_listener(self, cb: Callable[[int], None]) -> None:
        self._money_listeners.append(cb)

    def can_afford(self, cost: int) -> bool:
        return self._money >= cost

    def spend(self, amount: int) -> bool:
        if self._money < amount:
            return False
        self.money = self._money - amount
        return True

    def earn(self, amount: int) -> None:
        self.money = self._money + amount