from pygamine import GameObject
from gameplay.buildings import sprites
from gameplay.buildings.building import Building
from ui.money_format import format_money


class InfoPanel:
    def __init__(self, panel_manager) -> None:
        self.panel_manager = panel_manager
        self.root = GameObject("info_panel")
        self.building: Building | None = None

    def refresh(self, building: Building) -> None:
        self.building = building
        panel = self.panel_manager[self.panel_manager.current_panel]
        # These labels take their text from the language files; set_params
        # keeps them in the current language.
        panel["level_text"].set_params(value=building.level)
        panel["speed_text"].set_params(value=building.speed)
        panel["cooldown_text"].set_params(value=building.cooldown)
        self.retext_prices(panel, building)
        image = panel["info_panel_building_image"]
        # Taller sprites shrink to fit the box instead of stretching.
        image.add_surface(
            "default",
            sprites.fit_sprite(
                building.age, building.level, building.door_side, tuple(image.rect.size)
            ),
        )
        panel["info_panel_building_image"].set_state("default")

    @staticmethod
    def retext_prices(panel, building: Building) -> None:
        """The sell price in the language's money format (the label's params and the
        button's hover text hold the formatted text, so a language change must redo it)."""
        panel["sell_price_text"].set_params(value=format_money(building.sell_price))
        panel["sell_button_text"].set_text(
            format_money(building.sell_price), state="hover"
        )

    def relocalize(self) -> None:
        """Redoes the texts that hold formatted money after a language change."""
        if self.is_active and self.building is not None:
            self.retext_prices(self.panel_manager["game"], self.building)

    def open(self) -> None:
        self.root.active = True

    def close(self) -> None:
        self.root.active = False

    @property
    def is_active(self) -> bool:
        return self.root.active
