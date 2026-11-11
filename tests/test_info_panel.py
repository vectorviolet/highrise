from typing import Any

import pygame

from gameplay.buildings.building import Building
from gameplay.tiles.tile import Tile
from pygamine import TextObject, Transform
from pygamine.util.localization import localization
from ui.info_panel import InfoPanel
from ui.money_format import format_money


class FakeText:
    def __init__(self):
        self.text = None
        self.state = None

    def set_text(self, text, state=None) -> None:
        self.text = text
        self.state = state


class FakeImage:
    def __init__(self):
        self.surfaces = {}
        self.state = None
        self.rect = Transform((0, 0), (60, 185))  # the size the panel was loaded at

    def add_surface(self, name, surface) -> None:
        self.surfaces[name] = surface

    def set_state(self, state) -> None:
        self.state = state


class FakePanelManager(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_panel = "game"


def make_label(text_key: str) -> TextObject:
    """A real label, built the way config/panels.yaml builds the info texts."""
    return TextObject(
        Transform((0, 0), (100, 100)),
        (0, 0),
        font=pygame.font.Font(None, 15),
        text_key=text_key,
        text_params={"value": ""},
    )


def make_panel_manager() -> tuple[FakePanelManager, dict[str, Any]]:
    panel = {
        "level_text": make_label("game.level"),
        "speed_text": make_label("game.speed"),
        "cooldown_text": make_label("game.cooldown"),
        "boost_text": make_label("game.booster_multiplier"),
        "sell_price_text": make_label("game.sell_price"),
        "sell_button_text": FakeText(),
        "info_panel_building_image": FakeImage(),
    }
    return FakePanelManager({"game": panel}), panel


def test_new_info_panel_starts_active_with_no_building(assets):
    # GameObject defaults to active=True -- Game.run() explicitly calls
    # info_panel.close() right after construction to actually hide it.
    manager, _ = make_panel_manager()
    info_panel = InfoPanel(manager)

    assert info_panel.is_active is True
    assert info_panel.building is None


def test_open_and_close_toggle_is_active(assets):
    manager, _ = make_panel_manager()
    info_panel = InfoPanel(manager)

    info_panel.open()
    assert info_panel.is_active is True

    info_panel.close()
    assert info_panel.is_active is False


def test_refresh_writes_every_field_from_the_building(assets):
    manager, panel = make_panel_manager()
    info_panel = InfoPanel(manager)
    building = Building(
        level=2, age_number=1, tile=Tile(1, 1), door_side="left", on_payout=None
    )

    info_panel.refresh(building)

    assert info_panel.building is building
    assert panel["level_text"].text == f"Level: {building.level}"
    assert panel["speed_text"].text == f"Speed: {building.speed} $/sec"
    assert panel["cooldown_text"].text == f"Cooldown: {building.cooldown} sec"
    assert (
        panel["sell_price_text"].text
        == f"Sell Price: {format_money(building.sell_price)}"
    )
    assert panel["sell_button_text"].text == format_money(building.sell_price)
    assert panel["sell_button_text"].state == "hover"
    assert panel["info_panel_building_image"].state == "default"
    assert "default" in panel["info_panel_building_image"].surfaces


def test_refresh_reads_from_whichever_panel_is_currently_open(assets):
    manager, panel = make_panel_manager()
    _, other_panel = make_panel_manager()
    manager["other"] = other_panel
    manager.current_panel = "other"
    info_panel = InfoPanel(manager)
    building = Building(
        level=1, age_number=0, tile=Tile(1, 1), door_side="left", on_payout=None
    )

    info_panel.refresh(building)

    assert other_panel["level_text"].text == f"Level: {building.level}"
    # The panel that is not open keeps its own, untouched labels.
    assert [panel[k].text for k in ("level_text", "speed_text")] == [
        "Level: ",
        "Speed:  $/sec",
    ]
    assert panel["cooldown_text"].text == "Cooldown:  sec"
    assert panel["sell_price_text"].text == "Sell Price: "
    assert panel["sell_button_text"].text is None
    assert other_panel["speed_text"].text == f"Speed: {building.speed} $/sec"


def test_refresh_texts_follow_a_language_switch():
    manager, panel = make_panel_manager()
    info_panel = InfoPanel(manager)
    building = Building(
        level=2, age_number=1, tile=Tile(1, 1), door_side="left", on_payout=None
    )
    info_panel.refresh(building)

    localization.set_language("tr")

    assert panel["level_text"].text == f"Seviye: {building.level}"
    assert panel["cooldown_text"].text == f"Bekleme: {building.cooldown} sn"


def test_relocalize_redoes_the_formatted_prices_of_an_open_panel(assets):
    manager, panel = make_panel_manager()
    manager.current_panel = "game"
    info_panel = InfoPanel(manager)
    building = Building(
        level=5, age_number=3, tile=Tile(1, 1), door_side="left", on_payout=None
    )
    building.sell_price = 12345
    info_panel.refresh(building)
    info_panel.open()
    assert panel["sell_price_text"].text == "Sell Price: 12,345$"

    localization.set_language("tr")
    info_panel.relocalize()

    assert panel["sell_price_text"].text == "Satış Fiyatı: 12.345$"
    assert panel["sell_button_text"].text == "12.345$"


def test_relocalize_does_nothing_while_the_panel_is_closed(assets):
    manager, panel = make_panel_manager()
    info_panel = InfoPanel(manager)
    info_panel.close()

    info_panel.relocalize()  # no building: must not raise

    assert panel["sell_button_text"].text is None


def test_the_info_image_fits_the_box_for_every_level(assets):
    manager, panel = make_panel_manager()
    info_panel = InfoPanel(manager)
    image = panel["info_panel_building_image"]
    box = tuple(image.rect.size)

    for level in (1, 6, 7, 11):
        building = Building(
            level=level, age_number=0, tile=Tile(1, 1), door_side="left", on_payout=None
        )
        info_panel.refresh(building)
        assert image.surfaces["default"].get_size() == box
        assert panel["level_text"].text == f"Level: {level}"


def _booster(level: int, multiplier: float) -> Building:
    return Building(
        level=level,
        age_number=0,
        tile=Tile(1, 1),
        door_side="left",
        on_payout=None,
        booster_multiplier=multiplier,
    )


def test_a_booster_shows_its_level_and_multiplier_instead_of_speed_and_cooldown(assets):
    manager, panel = make_panel_manager()
    info_panel = InfoPanel(manager)

    info_panel.refresh(_booster(3, 1.35))

    assert panel["level_text"].text == "Level: 3"
    assert panel["boost_text"].text == "Boost: x1.35"
    assert panel["boost_text"].active is True
    assert panel["speed_text"].active is False
    assert panel["cooldown_text"].active is False


def test_a_building_hides_the_boost_line_again(assets):
    manager, panel = make_panel_manager()
    info_panel = InfoPanel(manager)
    building = Building(
        level=1, age_number=0, tile=Tile(1, 1), door_side="left", on_payout=None
    )

    info_panel.refresh(_booster(1, 1.1))
    info_panel.refresh(building)

    assert panel["boost_text"].active is False
    assert panel["speed_text"].active is True
    assert panel["cooldown_text"].active is True
    assert panel["speed_text"].text == f"Speed: {building.speed} $/sec"


def test_the_multiplier_follows_a_language_switch(assets):
    manager, panel = make_panel_manager()
    info_panel = InfoPanel(manager)
    info_panel.refresh(_booster(3, 1.35))
    info_panel.open()

    localization.set_language("tr")
    info_panel.relocalize()

    assert panel["boost_text"].text == "Artış: x1,35"
