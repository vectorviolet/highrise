import pygame
from random import choice

from pygame_core.panel_loader_ext import PanelLoaderExt
from pygame_core.asset_manager import AssetManager
from pygame_core.database import Database
from pygame_core.image import load_image
from pygame_core.color import Black, White, Gray, Yellow, CustomBlue
from pygame_core.asset_path import ImagePath, FontPath, SoundPath
from pygame_core.application import Application
from pygame_core.panel_manager import PanelManager
from pygame_core.unity.components.transform import Transform

from sound_manager import SoundManager
import panel_factory

from state_object import StateObject
from building import Building, Buildings
from cloud import CloudAnimation, GameClouds
from menu import Menu
from tile import Tilemap, Tile
from game_persistence import GamePersistenceMixin
from game_audio import GameAudioMixin
from game_events import GameEventsMixin


class Game(GameEventsMixin, GamePersistenceMixin, GameAudioMixin, Application):
    BACKGROUND_COLORS = {"menu": Yellow, "settings": Yellow, "display_settings": Yellow, "audio_settings": Yellow,
                         "game_settings": Yellow, "developer": Yellow, "game": CustomBlue}
    TITLE = "2048 GAME"
    SIZE = (1920, 1080)
    FPS = 165
    CURSOR_SIZE = (25, 25)
    DEBUG = False

    def __init__(self) -> None:
        super().__init__(Game.SIZE, Game.TITLE, Game.FPS)
        self._last_displayed_money = None
        self.tilemap = None
        self.info_building = None
        self.window_transform = Transform((0, 0), Game.SIZE)
        self.panel_manager = PanelManager(Game.BACKGROUND_COLORS)
        self.database = Database("database")
        self.buildings = Buildings()
        self.assets = AssetManager()
        self.assets.load_manifest("config/assets.yaml")
        missing = self.assets.validate()
        if missing:
            raise RuntimeError("Missing assets:\n" + "\n".join(missing))

        self.cloud_count = 30
        self.max_size = 7
        self.max_building_level = 6
        self.starting_money = 1000
        self.default_music_volume = 1.00
        self.default_sfx_volume = 1.00
        self.is_selection_mode = False
        self.is_info_panel_active = False
        self.money = 0
        self.old_music_volume = self.default_music_volume
        self.old_sfx_volume = self.default_sfx_volume

        self.font_path = FontPath("kenvector_future")
        self.font_path_thin = FontPath("kenvector_future_thin")
        self._debug_font = pygame.font.Font(str(self.font_path), 12)

        self.background_music_sound_path = SoundPath("music", extension="mp3")
        self.click_sound_path = SoundPath("click")
        self.go_back_sound_path = SoundPath("back")
        self.cloud_animation = CloudAnimation(self.size)

    def run(self) -> None:
        self.mouse.set_cursor_visible(False)
        self.mouse.set_cursor_image(StateObject((0, 0), Game.CURSOR_SIZE, {"default": ImagePath("cursor")}))

        self.load_data()
        self.add_objects()

        self.set_age(self.buildings.age_number)
        self.update_button_texts()

        self.open_panel("menu")
        self.close_info_panel()
        self.set_music_volume(SoundManager.get_volume(0))
        self.set_sfx_volume(SoundManager.get_volume(1))
        self.play_music(self.background_music_sound_path)

        super().run()

    def add_objects(self) -> None:
        blue3 = self.assets.image_path("blue_button")
        grey_panel = self.assets.image_path("grey_panel")

        # Menus
        self.panel_manager.add_object("menu",             "menu", Menu(blue3, self.get_title(), 30, White, self.font_path, grey_panel, (400, 60), "blue_button", "yellow_button", ("START", "SETTINGS", "DEVELOPER", "EXIT"), 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets)))
        self.panel_manager.add_object("settings",         "menu", Menu(blue3, "SETTINGS", 30, White, self.font_path, grey_panel, (400, 60), "blue_button", "yellow_button", ("display_settings", "audio_settings", "game_settings", "GO BACK"), 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets)))
        self.panel_manager.add_object("display_settings", "menu", Menu(blue3, "display_settings", 30, White, self.font_path, grey_panel, (400, 60), "blue_button", "yellow_button", (), 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets), panel_height=200))
        self.panel_manager.add_object("audio_settings",   "menu", Menu(blue3, "audio_settings", 30, White, self.font_path, grey_panel, (400, 60),"blue_button", "yellow_button", (), 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets), panel_height=500))
        self.panel_manager.add_object("game_settings",    "menu", Menu(blue3, "game_settings", 30, White, self.font_path, grey_panel, (400, 60), "blue_button", "yellow_button", (), 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets), panel_height=200))

        # Game
        self.panel_manager.add_object("game", "clouds", GameClouds(self.cloud_count, self.size))
        self.panel_manager.add_object("game", "tiles", self.tilemap)
        self.panel_manager.add_object("game", "buildings", self.buildings)

        loader = PanelLoaderExt(self.panel_manager, self.window_transform, self.assets)
        loader.register("object", panel_factory.make_factory(self.assets), default=True)
        loader.register("text", panel_factory.make_text_factory(self.assets))
        loader.register("button", panel_factory.make_button_factory(self.assets))
        loader.load("config/panels.yaml")

        # Developer panel icons
        panel = self.panel_manager["developer"]
        panel["github"].states["default"].blit(load_image(self.assets.image_path("github_icon"), (32, 32)), (105, 5))
        panel["linkedin"].states["default"].blit(load_image(self.assets.image_path("linkedin_icon"), (32, 32)), (105, 5))

        # Audio settings icons
        panel = self.panel_manager["audio_settings"]
        minus_icon = load_image(ImagePath("minus", "gui/others"), (16, 16))
        plus_icon  = load_image(ImagePath("plus",  "gui/others"), (16, 16))
        for key in ("music_volume_minus_button", "sfx_volume_minus_button"):
            for state in ("default", "hover"):
                panel[key].states[state].blit(minus_icon, (10, 10))
        for key in ("music_volume_plus_button", "sfx_volume_plus_button"):
            for state in ("default", "hover"):
                panel[key].states[state].blit(plus_icon, (10, 10))

        # Game panel
        self.panel_manager.add_object("game", "selection_mode_button_image", StateObject((345, 990), (50, 50), {"default": ImagePath("info", "gui/others")}))
        self.panel_manager.add_object("game", "info_panel_building_image", StateObject(((self.width - 250) / 2 + 20, (self.height - 400) / 2 + 20), (65, 89), visible=False))

        panel = self.panel_manager["game"]
        panel["selection_mode_button"].set_state("off")
        panel["close_button"].states["default"].blit(load_image(ImagePath("grey_crossWhite", "gui/others")), (9, 9))
        panel["close_button"].states["hover"].blit(load_image(ImagePath("grey_crossGrey",   "gui/others")), (9, 9))

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

        handlers = {
            "menu":             self.handle_menu_events,
            "settings":         self.handle_settings_events,
            "display_settings": self.handle_display_settings_events,
            "audio_settings":   self.handle_audio_settings_events,
            "game_settings":    self.handle_game_settings_events,
            "developer":        self.handle_developer_events,
            "game":             self.handle_game_events,
        }

        if handler := handlers.get(self.panel_manager.current_panel):
            handler(event)

    def update(self) -> None:
        self.panel_manager.update()
        self.buildings.update()
        self.cloud_animation.update()
        if self.panel_manager.current_panel == "game":
            self.update_money()

    def draw(self) -> None:
        self.panel_manager.draw(self.window)
        self.cloud_animation.draw(self.window)
        super().draw()

        self.window.blit(self._debug_font.render("v1.0.0", True, Black), (self.width - 60, self.height - 20))
        if Game.DEBUG:
            hovered = self.get_hovered_tile()
            self.window.blit(self._debug_font.render(f"info_panel: {self.is_info_panel_active}", True, Black), (10, self.height - 80))
            self.window.blit(self._debug_font.render(f"selection_mode: {self.is_selection_mode}", True, Black), (10, self.height - 60))
            self.window.blit(self._debug_font.render(f"mouse_tile: {(hovered.row_number, hovered.column_number) if hovered else None}", True, Black), (10, self.height - 40))
            self.window.blit(self._debug_font.render(f"mouse_pos: {self.mouse.position}", True, Black), (10, self.height - 20))

    def on_exit(self) -> None:
        self.play_sfx(self.go_back_sound_path)
        panel = self.panel_manager.current_panel

        if panel == "menu":
            self.exit()
        elif panel == "settings":
            self.open_panel("menu")
        elif panel in ("display_settings", "game_settings"):
            self.open_panel("settings")
        elif panel == "audio_settings":
            self.set_music_volume(self.old_music_volume)
            self.set_sfx_volume(self.old_sfx_volume)
            self.open_panel("settings")
        elif panel == "developer":
            self.open_panel("menu")
        elif panel == "game":
            if self.is_info_panel_active:
                self.close_info_panel()
            else:
                self.save_game()
                self.open_panel("menu")

    # ── Info panel ────────────────────────────────────────────────────────────

    def refresh_info_panel(self, building: Building) -> None:
        self.info_building = building
        panel = self.panel_manager[self.panel_manager.current_panel]
        panel["level_text"].set_text("Level: " + str(building.level))
        panel["speed_text"].set_text("Speed: " + str(building.speed) + " $/sec")
        panel["cooldown_text"].set_text("Cooldown: " + str(building.cooldown) + " sec")
        panel["sell_price_text"].set_text("Sell Price: " + str(building.sell_price))
        panel["sell_button"].text.update_text("hover", str(building.sell_price) + "$")
        panel["info_panel_building_image"].add_surface("default", load_image(building.get_image_path(), (65, 89)))

    def open_info_panel(self) -> None:
        self.set_info_panel_active(True)

    def close_info_panel(self) -> None:
        self.set_info_panel_active(False)

    def set_info_panel_active(self, active: bool) -> None:
        self.is_info_panel_active = active
        panel = self.panel_manager["game"]
        for name in ("info_panel", "level_text", "speed_text", "cooldown_text",
                     "sell_price_text", "close_button", "sell_button", "info_panel_building_image"):
            obj = panel[name]
            obj.active = active
            if hasattr(obj, "visible"):
                obj.visible = active

    # ── Tile / building selection ─────────────────────────────────────────────

    def control_selecting_tile(self) -> None:
        hovered = self.get_hovered_tile()
        for row in self.tilemap:
            for tile in row:
                tile.selected = tile is hovered
                tile.rect = tile.selected_rect if tile.selected and self.is_selection_mode else tile.unselected_rect

    def get_hovered_tile(self) -> Tile | None:
        for row in self.tilemap:
            for tile in row:
                if tile.is_mouse_over(self.mouse.position):
                    return tile
        return None

    def get_selected_tile(self) -> Tile | None:
        for row in self.tilemap:
            for tile in row:
                if tile.selected:
                    return tile
        return None

    def get_selected_building(self) -> Building | None:
        tile = self.get_selected_tile()
        if not tile: return None
        for building in self.buildings:
            if building.tile == tile:
                return building
        return None

    # ── Game mechanics ────────────────────────────────────────────────────────

    def expand(self) -> None:
        if self.money < self.tilemap.get_expand_cost() or self.tilemap.is_max_size(): return

        self.money -= self.tilemap.get_expand_cost()
        self.tilemap.expand()

        for building in self.buildings:
            building.tile = self.tilemap[building.tile.row_number - 1][building.tile.column_number - 1]

        self.update_button_texts()
        self.play_sfx(self.click_sound_path)

    def add_building(self, level, row_number, column_number) -> None:
        new_building = Building(level, self.buildings.age_number, self.tilemap[row_number - 1][column_number - 1])
        self.buildings.append(new_building)
        self.buildings.sort(key=lambda b: b.tile.column_number)

        if len(self.buildings) == self.tilemap.row_count * self.tilemap.column_count and "game" in self.panel_manager and "build_button" in self.panel_manager["game"]:
            self.panel_manager["game"]["build_button"].text.update_text("hover", "TILES ARE FULL")
            self.panel_manager["game"]["build_button"].text.update_size("hover", 17)

    def create_building(self) -> None:
        if self.buildings.is_moving() or self.money < self.buildings.get_build_cost():
            return

        all_tiles = {(r + 1, c + 1) for r in range(self.tilemap.row_count) for c in range(self.tilemap.column_count)}
        occupied  = {(b.tile.row_number, b.tile.column_number) for b in self.buildings}
        empty_tiles = list(all_tiles - occupied)

        if empty_tiles:
            row_number, column_number = choice(empty_tiles)
            self.add_building(1, row_number, column_number)
            self.money -= self.buildings.get_build_cost()
            self.play_sfx(self.click_sound_path)

    def set_age(self, age_number) -> None:
        if age_number <= self.buildings.max_age_number:
            self.buildings.set_age(age_number)
            self.update_button_texts()

    def next_age(self) -> None:
        if self.buildings.age_number < self.buildings.max_age_number and self.money >= self.buildings.get_age_cost():
            self.money -= self.buildings.get_age_cost()
            self.set_age(self.buildings.age_number + 1)
            self.play_sfx(self.click_sound_path)

    def move_buildings(self, rotation: str) -> None:
        if self.is_selection_mode or self.buildings.is_moving(): return

        is_vertical   = rotation in ("up", "down")
        reverse_sort  = rotation in ("down", "right")

        if is_vertical:
            line_count  = self.tilemap.column_count
            line_length = self.tilemap.row_count
            get_line    = lambda b: b.tile.column_number - 1
            get_pos     = lambda b: b.tile.row_number - 1
            get_tile    = lambda line, pos: self.tilemap[pos][line]
        else:
            line_count  = self.tilemap.row_count
            line_length = self.tilemap.column_count
            get_line    = lambda b: b.tile.row_number - 1
            get_pos     = lambda b: b.tile.column_number - 1
            get_tile    = lambda line, pos: self.tilemap[line][pos]

        for line in range(line_count):
            line_buildings = sorted(
                [b for b in self.buildings if get_line(b) == line],
                key=get_pos,
                reverse=reverse_sort,
            )
            if not line_buildings: continue

            previous = None
            target   = 0

            for building in line_buildings:
                if previous and previous.level == building.level and previous.level < self.max_building_level:
                    previous.level_up(building)
                    previous = None
                else:
                    target_pos = target if not reverse_sort else line_length - target - 1
                    if get_pos(building) != target_pos:
                        building.set_target_tile(get_tile(line, target_pos))
                    previous = building
                    target += 1

        self.buildings.sort(key=lambda b: b.tile.column_number)

    def update_money(self) -> None:
        now = pygame.time.get_ticks()

        for building in self.buildings:
            if not building.last_time:
                building.last_time = now
            if now - building.last_time > building.cooldown * 1000:
                self.money += building.cooldown * building.speed
                building.last_time = now

        if self.money != self._last_displayed_money:
            self._last_displayed_money = self.money
            self.panel_manager[self.panel_manager.current_panel]["money_text"].set_text(f"{self.money}$")

    def open_panel(self, tab: str) -> None:
        if tab == "exit":
            self.exit()
            return
        self.panel_manager.open_panel(tab)
        self.cloud_animation.create_clouds()