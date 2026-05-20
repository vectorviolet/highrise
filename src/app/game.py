from pathlib import Path
from random import choice

import pygame
import yaml

from app.game_events import GameEventsMixin
from app.game_persistence import GamePersistenceMixin
from domain.player import Player
from gameplay.buildings.building import Building, Buildings
from gameplay.clouds.cloud_container import OneShotCloudAnimation, LoopingCloudAnimation
from gameplay.tile_selector import TileSelector
from pygame_core.application import Application
from pygame_core.asset_manager import AssetManager
from pygame_core.database import Database
from pygame_core.panel_loader_ext import PanelLoaderExt
from pygame_core.panel_manager import PanelManager
from pygame_core.splash_screen import SplashScreen
from pygame_core.unity.components.transform import Transform
from pygame_core.unity.game_audio import GameAudio
from ui import panel_factory
from ui.info_panel import InfoPanel
from ui.state_object import StateObject

class Game(GameEventsMixin, GamePersistenceMixin, Application):

    def __init__(self) -> None:
        self.settings = yaml.safe_load(Path("config/settings.yaml").read_text())
        window   = self.settings["window"]
        gameplay = self.settings["gameplay"]
        splash   = self.settings["splash"]
        ui       = self.settings["ui"]

        self.cursor_size = tuple(ui["cursor_size"])

        super().__init__(tuple(window["size"]), window["title"], window["fps"])

        self.assets = AssetManager()
        self.assets.load_manifest("config/assets.yaml")
        missing = self.assets.validate()
        if missing:
            raise RuntimeError("Missing assets:\n" + "\n".join(missing))

        self._last_displayed_money = None
        self.tilemap = None
        self.window_transform = Transform((0, 0), self.size)
        self.panel_manager = PanelManager(ui["background_colors"])
        self.database = Database("database")

        self.buildings = Buildings(self.assets)
        self.cloud_count = gameplay["cloud_count"]
        self.max_size = gameplay["max_map_size"]
        self.max_building_level = gameplay["max_building_level"]
        self.starting_money = gameplay["starting_money"]

        self.audio = GameAudio()
        self.player = Player()
        self.old_music_volume = 1.0
        self.old_sfx_volume = 1.0

        self.background_music_sound_path = self.assets.sound_path("bg")
        self.click_sound_path = self.assets.sound_path("click")
        self.go_back_sound_path = self.assets.sound_path("back")

        self.info_panel = InfoPanel(self.panel_manager)
        self.tile_selector = TileSelector(self.tilemap, self.mouse, self.buildings)
        self.cloud_animation = OneShotCloudAnimation(self.size)
        self.splash = SplashScreen(
            [self.assets.image_path("pygame_logo")],
            fade_ms=splash["fade_ms"], hold_ms=splash["hold_ms"],
        )

        self.handlers = {
            "menu":             self.handle_menu_events,
            "settings":         self.handle_settings_events,
            "display_settings": self.handle_display_settings_events,
            "audio_settings":   self.handle_audio_settings_events,
            "game_settings":    self.handle_game_settings_events,
            "developer":        self.handle_developer_events,
            "game":             self.handle_game_events,
        }

    def run(self) -> None:
        self.splash.run(self.window, self.clock, self._fps)
        self.mouse.set_cursor_visible(False)
        self.mouse.set_cursor_image(StateObject((0, 0), self.cursor_size, {"default": self.assets.image_path("cursor")}))

        self.load_data()
        self.tile_selector.tilemap = self.tilemap
        self.add_objects()

        self.set_age(self.buildings.age_number)
        self.update_button_texts()

        self.open_panel("menu")
        self.info_panel.close()
        self.audio.set_music_volume(self.audio.music_volume())
        self.audio.set_sfx_volume(self.audio.sfx_volume())
        self.audio.play_music(str(self.background_music_sound_path))

        super().run()

    def add_objects(self) -> None:
        # Game
        self.panel_manager.add_object("game", "clouds", LoopingCloudAnimation(self.cloud_count, self.size))
        self.panel_manager.add_object("game", "tiles", self.tilemap)
        self.panel_manager.add_object("game", "buildings", self.buildings)

        loader = PanelLoaderExt(self.panel_manager, self.window_transform, self.assets)
        loader.register("object", panel_factory.make_factory(self.assets), default=True)
        loader.register("text", panel_factory.make_text_factory(self.assets))
        loader.register("button", panel_factory.make_button_factory(self.assets))
        loader.register("menu", panel_factory.make_menu_factory(self.assets, self.size))
        loader.load("config/panels.yaml")

        panel = self.panel_manager["game"]
        for name in ("info_panel", "level_text", "speed_text", "cooldown_text",
                     "sell_price_text", "close_button", "sell_button", "info_panel_building_image"):
            panel[name].set_parent(self.info_panel.root)

        panel["selection_mode_button"].set_base_state("off")
        panel["close_button"].states["default"].blit(self.assets.get_image("cross_white"), (9, 9))
        panel["close_button"].states["hover"].blit(self.assets.get_image("cross_grey"), (9, 9))

    def update_button_texts(self) -> None:
        panel = self.panel_manager["game"]

        if self.tilemap.is_max_size():
            panel["expand_button"].text.update_text("hover", "MAX SIZE")
        else:
            panel["expand_button"].text.update_text("hover", f"{self.tilemap.get_expand_cost()}$")

        if len(self.buildings) == self.tilemap.row_count * self.tilemap.column_count:
            panel["build_button"].text.update_text("hover", "TILES ARE FULL")
            panel["build_button"].text.update_size("hover", 17)
        else:
            panel["build_button"].text.update_text("hover", str(self.buildings.get_build_cost()) + "$")
            panel["build_button"].text.update_size("hover", 27)

        if self.buildings.age_number == self.buildings.max_age_number:
            panel["next_age_button"].text.update_text("hover", "MAX AGE")
        else:
            panel["next_age_button"].text.update_text("hover", str(self.buildings.get_age_cost()) + "$")

    def handle_event(self, event: pygame.Event) -> None:
        super().handle_event(event)
        self.panel_manager.handle_event(event, self.mouse.position)

        if handler := self.handlers.get(self.panel_manager.current_panel):
            handler(event)

    def update(self) -> None:
        self.panel_manager.update()
        self.buildings.update()
        for building in self.buildings:
            if building.on_payout is None:
                building.on_payout = self._on_building_payout
        self.cloud_animation.update()
        if self.panel_manager.current_panel == "game" and self.player.money != self._last_displayed_money:
            self._last_displayed_money = self.player.money
            self.panel_manager["game"]["money_text"].set_text(f"{self.player.money}$")

    def draw(self) -> None:
        self.panel_manager.draw(self.window)
        self.cloud_animation.draw(self.window)
        super().draw()

    def on_exit(self) -> None:
        self.audio.play_sfx(self.go_back_sound_path)
        panel = self.panel_manager.current_panel

        if panel == "menu":
            self.exit()
        elif panel == "settings":
            self.open_panel("menu")
        elif panel in ("display_settings", "game_settings"):
            self.open_panel("settings")
        elif panel == "audio_settings":
            self.audio.set_music_volume(self.old_music_volume)
            self.audio.set_sfx_volume(self.old_sfx_volume)
            self.open_panel("settings")
        elif panel == "developer":
            self.open_panel("menu")
        elif panel == "game":
            if self.info_panel.is_active:
                self.info_panel.close()
            else:
                self.save_game()
                self.open_panel("menu")

    # ── Game mechanics ────────────────────────────────────────────────────────

    def expand(self) -> None:
        if self.tilemap.is_max_size() or not self.player.spend(self.tilemap.get_expand_cost()):
            return

        self.tilemap.expand()

        for building in self.buildings:
            building.tile = self.tilemap[building.tile.row_number - 1][building.tile.column_number - 1]

        self.update_button_texts()
        self.audio.play_sfx(self.click_sound_path)

    def add_building(self, level, row_number, column_number) -> None:
        new_building = Building(level, self.buildings.age_number, self.tilemap[row_number - 1][column_number - 1])
        self.buildings.append(new_building)
        self.buildings.sort(key=lambda b: b.tile.column_number)

        if len(self.buildings) == self.tilemap.row_count * self.tilemap.column_count and "game" in self.panel_manager and "build_button" in self.panel_manager["game"]:
            self.panel_manager["game"]["build_button"].text.update_text("hover", "TILES ARE FULL")
            self.panel_manager["game"]["build_button"].text.update_size("hover", 17)

    def create_building(self) -> None:
        if self.buildings.is_moving() or not self.player.can_afford(self.buildings.get_build_cost()):
            return

        all_tiles = {(r + 1, c + 1) for r in range(self.tilemap.row_count) for c in range(self.tilemap.column_count)}
        occupied  = {(b.tile.row_number, b.tile.column_number) for b in self.buildings}
        empty_tiles = list(all_tiles - occupied)

        if empty_tiles:
            row_number, column_number = choice(empty_tiles)
            self.add_building(1, row_number, column_number)
            self.player.spend(self.buildings.get_build_cost())
            self.audio.play_sfx(self.click_sound_path)

    def set_age(self, age_number) -> None:
        if age_number <= self.buildings.max_age_number:
            self.buildings.set_age(age_number)
            self.update_button_texts()

    def next_age(self) -> None:
        if self.buildings.age_number >= self.buildings.max_age_number:
            return
        if not self.player.spend(self.buildings.get_age_cost()):
            return
        self.set_age(self.buildings.age_number + 1)
        self.audio.play_sfx(self.click_sound_path)

    def move_buildings(self, rotation: str) -> None:
        if self.tile_selector.is_active:
            return
        self.buildings.move(rotation, self.tilemap, self.max_building_level)

    def _on_building_payout(self, amount: int) -> None:
        self.player.earn(amount)

    def open_panel(self, tab: str) -> None:
        if tab == "exit":
            self.exit()
            return
        self.panel_manager.open_panel(tab)
        self.cloud_animation.create_clouds()

    # ── audio-settings UI labels (volume → "%NN" text on a panel widget) ──

    def set_music_label(self, volume: float) -> None:
        self._set_volume_label(volume, self.panel_manager["audio_settings"]["music_volume_entry"])

    def set_sfx_label(self, volume: float) -> None:
        self._set_volume_label(volume, self.panel_manager["audio_settings"]["sfx_volume_entry"])

    @staticmethod
    def _set_volume_label(volume: float, label) -> None:
        volume = max(0.0, min(1.0, volume))
        label.text.update_text("default", "%" + str(round(volume * 100)))