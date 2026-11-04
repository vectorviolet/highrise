from pygamine import load_image
from pygamine import GameObject
from gameplay.buildings.building import Building


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
        panel["sell_price_text"].set_params(value=building.sell_price)
        panel["sell_button_text"].set_text(
            str(building.sell_price) + "$", state="hover"
        )
        image = panel["info_panel_building_image"]
        image.add_surface(
            "default", load_image(building.get_image_path(), tuple(image.rect.size))
        )
        panel["info_panel_building_image"].set_state("default")

    def open(self) -> None:
        self.root.active = True

    def close(self) -> None:
        self.root.active = False

    @property
    def is_active(self) -> bool:
        return self.root.active
