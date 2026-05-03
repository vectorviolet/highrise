import pygame
from random import choice
import webbrowser

from pygame_core.panel_loader_ext import PanelLoaderExt
from pygame_core.asset_manager import AssetManager
from pygame_core.database import Database
from pygame_core.image import load_image
from pygame_core.color import CustomBlue, Gray, White, Yellow
from pygame_core.asset_path import ImagePath, FontPath, SoundPath
from pygame_core.application import Application
from pygame_core.panel_manager import PanelManager

from sound_manager import SoundManager
import panel_factory

from untiy.components.transform import Transform
from object import Object
from building import Building, Buildings
from cloud import CloudAnimation, GameClouds
from menu import Menu
from tile import Tiles

class Game(Application):
	def __init__(self) -> None:
		self.cursor_size = 25, 25
		self.background_colors = {"menu": Yellow, "settings": Yellow, "display_settings": Yellow, "audio_settings": Yellow, "game_settings": Yellow, "developer": Yellow, "game": CustomBlue}

		super().__init__((1920, 1080), "2048 GAME", 165)
		self.window_transform = Transform((0, 0), self.size)
		self._last_displayed_money = None
		self.panel_manager = PanelManager(self.background_colors)

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

		self.font_path = FontPath("kenvector_future")
		self.font_path_thin = FontPath("kenvector_future_thin")

		self.background_music_sound_path = SoundPath("music", extension="mp3")
		self.click_sound_path = SoundPath("click")
		self.go_back_sound_path = SoundPath("back")
		self.cloud_animation = CloudAnimation(self.size)

	def run(self) -> None:
		self.mouse.set_cursor_visible(False)
		self.mouse.set_cursor_image(Object((0, 0), self.cursor_size, {"default": ImagePath("cursor")}))

		self.get_data()
		self.add_objects()

		self.set_age(self.buildings.age_number)
		self.update_button_texts()

		self.open_panel("menu")
		self.set_music_volume(SoundManager.get_volume(0))
		self.set_sfx_volume(SoundManager.get_volume(1))
		self.play_music(self.background_music_sound_path)

		super().run()

	def add_objects(self) -> None:
		blue3 = self.assets.image_path("blue_button")

		# Menus
		self.panel_manager.add_object("menu", "menu",             Menu(blue3, self.get_title(), 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60), "blue_button", "yellow_button", ["START", "SETTINGS", "DEVELOPER", "EXIT"], 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets)))
		self.panel_manager.add_object("settings", "menu",         Menu(blue3, "SETTINGS", 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60), "blue_button", "yellow_button", ["display_settings", "audio_settings", "game_settings", "GO BACK"], 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets)))
		self.panel_manager.add_object("display_settings", "menu", Menu(blue3, "display_settings", 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60), "blue_button", "yellow_button", [], 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets), panel_height=200))
		self.panel_manager.add_object("audio_settings", "menu",   Menu(blue3, "audio_settings", 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60),"blue_button", "yellow_button", [], 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets), panel_height=500))
		self.panel_manager.add_object("game_settings", "menu",    Menu(blue3, "game_settings", 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60), "blue_button", "yellow_button", [], 30, Gray, White, "kenvector_future", self.size, panel_factory.make_button_factory(self.assets), panel_height=200))

		# Game
		self.panel_manager.add_object("game", "clouds", GameClouds(self.cloud_count, self.size))
		self.panel_manager.add_object("game", "info_panel", Object(((self.width - 250) / 2, (self.height - 400) / 2), (250, 400), {"default": ImagePath("grey", "gui/panels")}, visible=False))
		self.panel_manager.add_object("game", "tiles", self.tiles)
		self.panel_manager.add_object("game", "buildings", self.buildings)

		loader = PanelLoaderExt(self.panel_manager, self.window_transform, self.assets)
		loader.register("object", panel_factory.make_factory(self.assets), default=True)
		loader.register("text", panel_factory.make_text_factory(self.assets))
		loader.register("button", panel_factory.make_button_factory(self.assets))
		loader.load("config/panels.yaml")

		# Developer
		self.panel_manager["developer"]["github"].states["default"].blit(load_image(self.assets.image_path("github_icon"), (32, 32)), (105, 5))
		self.panel_manager["developer"]["linkedin"].states["default"].blit(load_image(self.assets.image_path("linkedin_icon"), (32, 32)), (105, 5))

		self.panel_manager["audio_settings"]["music_volume_minus_button"].states["default"].blit(load_image(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["music_volume_minus_button"].states["hover"].blit(load_image(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["music_volume_plus_button"].states["default"].blit(load_image(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["music_volume_plus_button"].states["hover"].blit(load_image(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["sfx_volume_minus_button"].states["default"].blit(load_image(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["sfx_volume_minus_button"].states["hover"].blit(load_image(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["sfx_volume_plus_button"].states["default"].blit(load_image(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["sfx_volume_plus_button"].states["hover"].blit(load_image(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))

		self.panel_manager.add_object("game", "info_mode_button_image", Object((345, 990), (50, 50), {"default": ImagePath("info", "gui/others")}))
		self.panel_manager.add_object("game", "info_panel_building_image", Object(((self.width - 250) / 2 + 20, (self.height - 400) / 2 + 20), (65, 89), visible=False))

		self.panel_manager["game"]["info_mode_button"].set_state("off")
		self.panel_manager["game"]["info_panel_close_button"].states["default"].blit(load_image(ImagePath("grey_crossWhite", "gui/others")), (9, 9))
		self.panel_manager["game"]["info_panel_close_button"].states["hover"].blit(load_image(ImagePath("grey_crossGrey", "gui/others")), (9, 9))


	def play_music(self, sound_path) -> None:
		SoundManager.play_sound(0, sound_path, -1)

	def play_sfx(self, sound_path) -> None:
		SoundManager.play_sound(1, sound_path)

	def set_music_volume(self, volume: float) -> None:
		SoundManager.set_volume(0, volume)

	def set_sfx_volume(self, volume: float) -> None:
		SoundManager.set_volume(1, volume)

	def set_sfx_label(self, volume: float) -> None:
		self.set_volume_label(volume, self.panel_manager["audio_settings"]["sfx_volume_entry"])

	def set_music_label(self, volume: float) -> None:
		self.set_volume_label(volume, self.panel_manager["audio_settings"]["music_volume_entry"])

	def set_volume_label(self, volume: float, label) -> None:
		if volume < 0:
			volume = 0
		elif volume > 1:
			volume = 1

		label.text.update_text("default", "%" + str(round(volume * 100)))

	def get_data(self) -> None:
		self.database = Database("database")

		self._execute_sql("CREATE TABLE IF NOT EXISTS game(age_number INTEGER, size INTEGER, money INTEGER, music_volume INTEGER, sfx_volume INTEGER)")
		game_data = self._execute_sql("SELECT * FROM game", True)

		if not game_data:
			self._execute_sql(f"INSERT INTO game(age_number, size, money, music_volume, sfx_volume) VALUES(0, 2, {self.starting_money}, {self.default_music_volume}, {self.default_sfx_volume})")
			game_data = self._execute_sql("SELECT * FROM game", True)

		age_number, size, self.money, music_volume, sfx_volume  = game_data[0]
		self.set_music_volume(music_volume)
		self.set_sfx_volume(sfx_volume)
		self.tiles = Tiles(size, self.max_size)
		self._execute_sql("CREATE TABLE IF NOT EXISTS buildings(level INTEGER, row INTEGER, column INTEGER)")

		buildings = self._execute_sql("SELECT * FROM buildings", True)

		self.buildings = Buildings(SoundManager.get_volume(1))
		self.buildings.age_number = age_number

		for building in buildings:
			self.add_building(*building)

	def delete_data(self) -> None:
		self._execute_sql("DELETE FROM game")
		self._execute_sql("DELETE FROM buildings")

	def _execute_sql(self, query: str, fetch: bool = False):
		"""Handles the repetitive database boilerplate safely."""
		if not self.database.connect():
			self.exit()

		cursor = self.database.execute(query)
		result = cursor.fetchall() if fetch else None

		self.database.commit()
		self.database.disconnect()

		return result

	def update_button_texts(self) -> None:
		if self.tiles.is_max_size():
			self.panel_manager["game"]["expand_button"].text.update_text("hover", "MAX SIZE")
		else:
			self.panel_manager["game"]["expand_button"].text.update_text("hover", str(self.tiles.get_expand_cost()) + "$")

		if len(self.buildings) == self.tiles.rowCount * self.tiles.columnCount:
			self.panel_manager["game"]["build_button"].text.update_text("hover", "TILES ARE FULL")
			self.panel_manager["game"]["build_button"].text.update_size("hover", 17)
		else:
			self.panel_manager["game"]["build_button"].text.update_text("hover", str(self.buildings.get_build_cost()) + "$")
			self.panel_manager["game"]["build_button"].text.update_size("hover", 27)

		if self.buildings.age_number == self.buildings.max_age_number:
			self.panel_manager["game"]["next_age_button"].text.update_text("hover", "MAX AGE")
		else:
			self.panel_manager["game"]["next_age_button"].text.update_text("hover", str(self.buildings.get_age_cost()) + "$")

	def control_selecting_tile(self) -> None:
		is_there_selected = self.tiles.is_there_selected_tile()

		for row in self.tiles:
			for tile in row:
				is_over = tile.is_mouse_over(self.mouse.position)

				if is_over:
					if not is_there_selected:
						tile.selected = True
						if self.is_info_mode():
							tile.rect = tile.selected_rect
				else:
					tile.selected = False
					tile.rect = tile.unselected_rect

	def expand(self) -> None:
		if self.money >= self.tiles.get_expand_cost() and not self.tiles.is_max_size():
			self.money -= self.tiles.get_expand_cost()
			self.tiles.expand()

			for building in self.buildings:
				building.tile = self.tiles[building.tile.row_number - 1][building.tile.column_number - 1]

			self.update_button_texts()
			self.play_sfx(self.click_sound_path)

	def handle_event(self, event) -> None:
		super().handle_event(event)
		self.panel_manager.handle_event(event, self.mouse.position)

		event_handlers = {
			"menu": self.handle_menu_events,
			"settings": self.handle_settings_events,
			"display_settings": self.handle_display_settings_events,
			"audio_settings": self.handle_audio_settings_events,
			"game_settings": self.handle_game_settings_events,
			"developer": self.handle_developer_events,
			"game": self.handle_game_events
		}

		# 2. Call the appropriate method
		current_panel = self.panel_manager.current_panel
		if handler := event_handlers.get(current_panel):
			handler(event)

	def handle_menu_events(self, event: pygame.event.Event) -> None:
		buttons = self.panel_manager["menu"]["menu"].buttons

		if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
			if buttons["START"].state == "hover":
				self.play_sfx(self.click_sound_path); self.open_panel("game")
			elif buttons["SETTINGS"].state == "hover":
				self.play_sfx(self.click_sound_path); self.open_panel("settings")
			elif buttons["DEVELOPER"].state == "hover":
				self.play_sfx(self.click_sound_path); self.open_panel("developer")
			elif buttons["EXIT"].state == "hover":
				self.play_sfx(self.click_sound_path); self.exit()

		if buttons["EXIT"].is_clicked(event, self.mouse.position):
			self.play_sfx(self.go_back_sound_path)
			self.exit()

		navigations = {"START": "game", "SETTINGS": "settings", "DEVELOPER": "developer"}

		for navigation, panel in navigations.items():
			if buttons[navigation].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path);
				self.open_panel(panel)

	def handle_settings_events(self, event: pygame.event.Event) -> None:
		panel = "settings"

		if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
			if self.panel_manager[panel]["menu"].buttons["display_settings"].state == "hover":
				self.play_sfx(self.click_sound_path); self.open_panel("display_settings")
			elif self.panel_manager[panel]["menu"].buttons["audio_settings"].state == "hover":
				self.old_music_volume, self.old_sfx_volume = SoundManager.get_volume(0), SoundManager.get_volume(1)
				self.play_sfx(self.click_sound_path); self.open_panel("audio_settings")
			elif self.panel_manager[panel]["menu"].buttons["game_settings"].state == "hover":
				self.play_sfx(self.click_sound_path); self.open_panel("game_settings")
			elif self.panel_manager[panel]["menu"].buttons["GO BACK"].state == "hover":
				self.play_sfx(self.click_sound_path); self.open_panel("menu")

		if self.panel_manager[panel]["menu"].buttons["display_settings"].is_clicked(event, self.mouse.position):
			self.play_sfx(self.click_sound_path); self.open_panel("display_settings")
		elif self.panel_manager[panel]["menu"].buttons["audio_settings"].is_clicked(event, self.mouse.position):
			self.old_music_volume, self.old_sfx_volume = SoundManager.get_volume(0), SoundManager.get_volume(1)
			self.play_sfx(self.click_sound_path); self.open_panel("audio_settings")
		elif self.panel_manager[panel]["menu"].buttons["game_settings"].is_clicked(event, self.mouse.position):
			self.play_sfx(self.click_sound_path); self.open_panel("game_settings")
		elif self.panel_manager[panel]["menu"].buttons["GO BACK"].is_clicked(event, self.mouse.position):
			self.play_sfx(self.click_sound_path); self.open_panel("menu")

	def handle_display_settings_events(self, event: pygame.event.Event):
		panel = "display_settings"
		if self.panel_manager[panel]["go_back_button"].is_clicked(event, self.mouse.position):
			self.play_sfx(self.click_sound_path); self.open_panel("settings")

	def handle_audio_settings_events(self, event: pygame.event.Event) -> None:
		panel = "audio_settings"
		if self.panel_manager[panel]["music_volume_plus_button"].is_clicked(event, self.mouse.position):
			self.set_music_volume(SoundManager.get_volume(0) + 0.1)
			self.set_music_label(SoundManager.get_volume(0) + 0.1)
		elif self.panel_manager[panel]["music_volume_minus_button"].is_clicked(event, self.mouse.position):
			self.set_music_volume(SoundManager.get_volume(0) - 0.1)
			self.set_music_label(SoundManager.get_volume(0) - 0.1)
		elif self.panel_manager[panel]["sfx_volume_plus_button"].is_clicked(event, self.mouse.position):
			self.set_sfx_volume(SoundManager.get_volume(1) + 0.1)
			self.set_sfx_label(SoundManager.get_volume(1) + 0.1)
		elif self.panel_manager[panel]["sfx_volume_minus_button"].is_clicked(event, self.mouse.position):
			self.set_sfx_volume(SoundManager.get_volume(1) - 0.1)
			self.set_sfx_label(SoundManager.get_volume(1) - 0.1)
		elif self.panel_manager[panel]["cancel_button"].is_clicked(event, self.mouse.position):
			self.set_music_volume(self.old_music_volume)
			self.set_sfx_volume(self.old_sfx_volume)
			self.play_sfx(self.go_back_sound_path)
			self.open_panel("settings")
		elif self.panel_manager[panel]["save_button"].is_clicked(event, self.mouse.position):
			self._execute_sql(f"UPDATE game SET music_volume='{SoundManager.get_volume(0)}', sfx_volume='{SoundManager.get_volume(1)}'")
			self.play_sfx(self.go_back_sound_path); self.open_panel("settings")

	def handle_game_settings_events(self, event: pygame.event.Event) -> None:
		panel = "game_settings"
		if self.panel_manager[panel]["delete_data_button"].is_clicked(event, self.mouse.position):
			self.delete_data(); self.get_data(); self.add_objects()
			self.play_sfx(self.click_sound_path); self.open_panel("menu")
		elif self.panel_manager[panel]["go_back_button"].is_clicked(event, self.mouse.position):
			self.play_sfx(self.click_sound_path); self.open_panel("settings")

	def handle_developer_events(self, event: pygame.event.Event) -> None:
		panel = "developer"
		if self.panel_manager[panel]["github"].is_clicked(event, self.mouse.position):
			self.play_sfx(self.click_sound_path); webbrowser.open("https://www.github.com/umutcanekinci/")
		elif self.panel_manager[panel]["linkedin"].is_clicked(event, self.mouse.position):
			self.play_sfx(self.click_sound_path); webbrowser.open("https://www.linkedin.com/in/umutcanekinci/")
		elif self.panel_manager[panel]["go_back_button"].is_clicked(event, self.mouse.position):
			self.play_sfx(self.click_sound_path); self.open_panel("menu")

	def handle_game_events(self, event: pygame.event.Event) -> None:
		panel = "game"
		if self.panel_manager[panel]["info_panel"].visible:
			if self.panel_manager[panel]["info_panel_sell_button"].is_clicked(event, self.mouse.position):
				self.buildings.remove(self.info_building)
				self.money += self.info_building.sell_price
				self.close_info_panel()
				self.play_sfx(self.go_back_sound_path)
				self.update_button_texts()
			elif self.panel_manager[panel]["info_panel_close_button"].is_clicked(event, self.mouse.position):
				self.close_info_panel()
				self.play_sfx(self.go_back_sound_path)
				self.control_selecting_tile()
		else:
			self.control_selecting_tile()

			info_button = self.panel_manager[panel]["info_mode_button"]
			if info_button.is_clicked(event, self.mouse.position):
				state = "off" if info_button.state == "on" else "on"
				info_button.set_state(state)
				self.play_sfx(self.click_sound_path)

			if self.is_info_mode() and event.type == pygame.MOUSEBUTTONUP:
				for row in self.tiles:
					for tile in row:
						if tile.selected:
							for building in self.buildings:
								if building.tile == tile:
									self.refresh_info_panel(building)
									self.open_info_panel()
									self.play_sfx(self.click_sound_path)
									break
							break

			if self.panel_manager[panel]["expand_button"].is_clicked(event, self.mouse.position):
				self.expand()
			elif self.panel_manager[panel]["build_button"].is_clicked(event, self.mouse.position):
				self.create_building()
			elif self.panel_manager[panel]["next_age_button"].is_clicked(event, self.mouse.position):
				self.next_age()

		if event.type == pygame.KEYUP and not self.panel_manager["game"]["info_panel"].visible:

			if event.key == pygame.K_SPACE:
				self.create_building()
			elif event.key in (pygame.K_RIGHT, pygame.K_d):
				self.move_buildings("right")
			elif event.key in (pygame.K_LEFT, pygame.K_a):
				self.move_buildings("left")
			elif event.key in (pygame.K_UP, pygame.K_w):
				self.move_buildings("up")
			elif event.key in (pygame.K_DOWN, pygame.K_s):
				self.move_buildings("down")

	def update(self) -> None:
		self.panel_manager.update()
		for building in self.buildings:
			building.update()
		self.cloud_animation.update()

	def on_exit(self) -> None:
		self.play_sfx(self.go_back_sound_path)

		if self.panel_manager.current_panel == "menu":
			self.exit()
		elif self.panel_manager.current_panel == "settings":
			self.open_panel("menu")
		elif self.panel_manager.current_panel == "display_settings":
			self.open_panel("settings")
		elif self.panel_manager.current_panel == "audio_settings":
			self.set_music_volume(self.old_music_volume)
			self.set_sfx_volume(self.old_sfx_volume)
			self.open_panel("settings")
		elif self.panel_manager.current_panel == "game_settings":
			self.open_panel("settings")
		elif self.panel_manager.current_panel == "developer":
			self.open_panel("menu")
		elif self.panel_manager.current_panel == "game":
			if self.panel_manager["game"]["info_panel"].visible:
				self.close_info_panel()
			else:
				self.save_game()
				self.open_panel("menu")

	def save_game(self) -> None:
		self._execute_sql(f"UPDATE game SET age_number={self.buildings.age_number}, size={self.tiles.rowCount}, money={self.money}")
		self._execute_sql("DELETE FROM buildings")

		for building in self.buildings:
			self._execute_sql(f"INSERT INTO buildings(level, row, column) VALUES({building.level}, {building.tile.row_number}, {building.tile.column_number})")

	def refresh_info_panel(self, building: Building) -> None:
		self.info_building = building
		panel = self.panel_manager[self.panel_manager.current_panel]

		panel["level_text"].set_text("Level: " + str(building.level))
		panel["speed_text"].set_text("Speed: " + str(building.speed) + " $/sec")
		panel["cooldown_text"].set_text("Cooldown: " + str(building.cooldown) + " sec")
		panel["sell_price_text"].set_text("Sell Price: " + str(building.sell_price))
		panel["info_panel_sell_button"].text.update_text("hover", str(building.sell_price) + "$")
		panel["info_panel_building_image"].add_surface("default", load_image(building.get_image_path(), (65, 89)))

	def open_info_panel(self) -> None:
		self.set_info_panel_active(True)

	def close_info_panel(self) -> None:
		self.set_info_panel_active(False)

	def set_info_panel_active(self, active: bool) -> None:
		panel = self.panel_manager[self.panel_manager.current_panel]

		panel["info_panel"].active = active
		panel["level_text"].active = active
		panel["speed_text"].active = active
		panel["cooldown_text"].active = active
		panel["sell_price_text"].active = active
		panel["info_panel_close_button"].active = active
		panel["info_panel_sell_button"].active = active
		panel["info_panel_building_image"].active = active

	def is_info_mode(self) -> bool:
		return self.panel_manager["game"]["info_mode_button"].state == "on"

	def move_buildings(self, rotation: str) -> None:
		if self.is_info_mode() or self.buildings.is_moving(): return

		is_vertical = rotation in ("up", "down")
		reverse_sort = rotation in ("down", "right")

		if is_vertical:
			line_count = self.tiles.columnCount
			line_length = self.tiles.rowCount
			get_line = lambda b: b.tile.column_number - 1
			get_pos = lambda b: b.tile.row_number - 1
			get_tile = lambda line, pos: self.tiles[pos][line]
		else:
			line_count = self.tiles.rowCount
			line_length = self.tiles.columnCount
			get_line = lambda b: b.tile.row_number - 1
			get_pos = lambda b: b.tile.column_number - 1
			get_tile = lambda line, pos: self.tiles[line][pos]

		for line in range(line_count):
			line_buildings = sorted(
				[b for b in self.buildings if get_line(b) == line],
				key=get_pos,
				reverse=reverse_sort
			)

			if not line_buildings: continue

			previous = None
			target = 0

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

	def add_building(self, level, row_number, column_number) -> None:
		new_building = Building(level, self.buildings.age_number, self.tiles[row_number - 1][column_number - 1])
		self.buildings.append(new_building)
		self.buildings.sort(key=lambda b: b.tile.column_number)

		if len(self.buildings) == self.tiles.rowCount * self.tiles.columnCount and "game" in self and "build_button" in self.panel_manager["game"]:
			self.panel_manager["game"]["build_button"].text.update_text("hover", "TILES ARE FULL")
			self.panel_manager["game"]["build_button"].text.update_size("hover", 17)

	def create_building(self) -> None:
		is_moving = self.buildings.is_moving()

		if not is_moving and self.money >= self.buildings.get_build_cost():
			all_tiles = {(r + 1, c + 1) for r in range(self.tiles.rowCount) for c in range(self.tiles.columnCount)}
			occupied = {(b.tile.row_number, b.tile.column_number) for b in self.buildings}
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

	def open_panel(self, tab: str) -> None:
		self.panel_manager.open_panel(tab)
		self.cloud_animation.create_clouds()

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
			self.panel_manager[self.panel_manager.current_panel]["money_text"].set_text(str(self.money) + "$")

	def draw(self) -> None:
		self.panel_manager.draw(self.window)
		if self.panel_manager.current_panel == "game":
			self.update_money()
		self.cloud_animation.draw(self.window)
		super().draw()
