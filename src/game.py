from default.sound_manager import SoundManager
from ext import panel_factory
from pygame_core.panel_loader_ext import PanelLoaderExt
from pygame_core.asset_manager import AssetManager
from untiy.rigidbody2d import Rigidbody2D

try:
	import pygame
	from random import choice
	import webbrowser

	from pygame_core.database import Database
	from pygame_core.image import load_image
	from pygame_core.color import Black, CustomBlue, Gray, Green, White, Yellow
	from pygame_core.asset_path import AssetPath, ImagePath, FontPath, SoundPath
	from pygame_core.application import Application
	from pygame_core.panel_manager import PanelManager

	from default.button import Button
	from default.object import Object
	from text import Text
	from building import Building, Buildings
	from cloud import CloudAnimation, GameClouds
	from menu import Menu
	from tile import Tiles
except Exception as error:
	print("An error occurred during importing packages:", error)

class Game(Application):
	def __init__(self) -> None:
		self.cursor_size = 25, 25
		self.background_colors = {"menu": Yellow, "settings": Yellow, "display_settings": Yellow, "audio_settings": Yellow, "game settings": Yellow, "developer": Yellow, "game": CustomBlue}

		super().__init__((1920, 1080), "2048 GAME", 165)

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

	def run(self) -> None:
		self.mouse.set_cursor_visible(False)
		self.mouse.set_cursor(Object((0, 0), self.cursor_size, {"Normal": ImagePath("cursor")}))

		self.get_data()
		self.add_objects()

		loader = PanelLoaderExt(self.panel_manager, self.size, self.assets)
		loader.register("object", panel_factory.make_factory(self.assets), default=True)
		loader.register("text", panel_factory.make_text_factory(self.assets))
		loader.load("config/panels.yaml")

		self.open_panel("menu")

		self.set_music_volume(self.music_volume)
		self.set_sfx_volume(self.sfx_volume)
		self.play_music(self.background_music_sound_path)

		super().run()

	def play_music(self, sound_path) -> None:
		SoundManager.play_sound(0, sound_path, self.music_volume, -1)

	def set_music_volume(self, volume: float) -> None:
		if volume < 0:
			volume = 0
		if volume > 1:
			volume = 1

		self.music_volume = self.panel_manager["menu"]["menu"].sfx_volume = self.panel_manager["settings"]["menu"].sfx_volume = self.panel_manager["audio_settings"]["menu"].sfx_volume = self.sfx_volume = volume
		self.panel_manager["audio_settings"]["music volume entry"].text.update_text("Normal", "%" + str(round(self.music_volume * 100)))
		SoundManager.set_volume(0, volume)

	def play_sfx(self, sound_path) -> None:
		SoundManager.play_sound(1, sound_path, self.sfx_volume)

	def set_sfx_volume(self, volume: float) -> None:
		if volume < 0:
			volume = 0
		elif volume > 1:
			volume = 1

		self.buildings.sfx_volume = self.panel_manager["menu"]["menu"].sfx_volume = self.panel_manager["settings"]["menu"].sfx_volume = self.panel_manager["audio_settings"]["menu"].sfx_volume = self.sfx_volume = volume
		self.panel_manager["audio_settings"]["SFX volume entry"].text.update_text("Normal", "%" + str(round(self.sfx_volume * 100)))
		SoundManager.set_volume(1, volume)

	def add_objects(self) -> None:
		# Menu
		self.panel_manager.add_object("menu", "menu", Menu(ImagePath("blue3", "gui/buttons"), self.get_title(), 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", ["START", "SETTINGS", "DEVELOPER", "EXIT"], 30, Gray, White, self.font_path, self.size))
		self.panel_manager.add_object("menu", "cloud animation", CloudAnimation(self.size))

		# Settings
		self.panel_manager.add_object("settings", "menu", Menu(ImagePath("blue3", "gui/buttons"), "SETTINGS", 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", ["display_settings", "audio_settings", "GAME SETTINGS", "GO BACK"], 30, Gray, White, self.font_path, self.size))
		self.panel_manager.add_object("settings", "cloud animation", CloudAnimation(self.size))

		# Display Settings
		self.panel_manager.add_object("display_settings", "menu", Menu(ImagePath("blue3", "gui/buttons"), "display_settings", 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", [], 30, Gray, White, self.font_path, self.size, 200))
		self.panel_manager.add_object("display_settings", "information", Text(((self.width - 300) / 2, (self.height - 600) / 2 + 280), "THIS PAGE WILL COMING SOON...", 25, color=Black, is_centered=False))
		self.panel_manager.add_object("display_settings", "go back button", Button((810, 580), (315, 60), {"Normal": ImagePath("red", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "GO BACK", "", 28, White, Gray, self.font_path))
		self.panel_manager.add_object("display_settings", "cloud animation", CloudAnimation(self.size))

		# Audio Settings
		self.panel_manager.add_object("audio_settings", "menu", Menu(ImagePath("blue3", "gui/buttons"), "audio_settings", 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", [], 30, Gray, White, self.font_path, self.size, 500))
		self.panel_manager.add_object("audio_settings", "music volume minus button", Button((840, 430), (36, 36), {"Normal": ImagePath("blue_circle", "gui/buttons"), "Mouse Over": ImagePath("yellow_circle", "gui/buttons")}))
		self.panel_manager.add_object("audio_settings", "music volume entry", Button((885, 430), (150, 35), {"Normal": ImagePath("grey8", "gui/buttons")}, "%100", textSize=25, textColor=Gray, textFontPath=self.font_path))
		self.panel_manager.add_object("audio_settings", "music volume plus button", Button((1054, 430), (36, 36), {"Normal": ImagePath("blue_circle", "gui/buttons"), "Mouse Over": ImagePath("yellow_circle", "gui/buttons")}))
		self.panel_manager["audio_settings"]["music volume minus button"].states["Normal"].blit(load_image(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["music volume minus button"].states["Mouse Over"].blit(load_image(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["music volume plus button"].states["Normal"].blit(load_image(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["music volume plus button"].states["Mouse Over"].blit(load_image(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))

		self.panel_manager.add_object("audio_settings", "SFX volume minus button", Button((840, 600), (36, 36), {"Normal": ImagePath("blue_circle", "gui/buttons"), "Mouse Over": ImagePath("yellow_circle", "gui/buttons")}))
		self.panel_manager.add_object("audio_settings", "SFX volume entry", Button((885, 600), (150, 35), {"Normal": ImagePath("grey8", "gui/buttons")}, "%100", textSize=25, textColor=Gray, textFontPath=self.font_path))
		self.panel_manager.add_object("audio_settings", "SFX volume plus button", Button((1054, 600), (36, 36), {"Normal": ImagePath("blue_circle", "gui/buttons"), "Mouse Over": ImagePath("yellow_circle", "gui/buttons")}))
		self.panel_manager["audio_settings"]["SFX volume minus button"].states["Normal"].blit(load_image(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["SFX volume minus button"].states["Mouse Over"].blit(load_image(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["SFX volume plus button"].states["Normal"].blit(load_image(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager["audio_settings"]["SFX volume plus button"].states["Mouse Over"].blit(load_image(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))
		self.panel_manager.add_object("audio_settings", "cancel button", Button((810, 710), (150, 60), {"Normal": ImagePath("red", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "CANCEL", "", 28, White, Gray, self.font_path))
		self.panel_manager.add_object("audio_settings", "save button", Button((975, 710), (150, 60), {"Normal": ImagePath("green", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "SAVE", "", 28, White, Gray, self.font_path))
		self.panel_manager.add_object("audio_settings", "cloud animation", CloudAnimation(self.size))

		# Game Settings
		self.panel_manager.add_object("game settings", "menu", Menu(ImagePath("blue3", "gui/buttons"), "GAME SETTINGS", 30, White, self.font_path, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", [], 30, Gray, White, self.font_path, self.size, 200))
		self.panel_manager.add_object("game settings", "delete data button", Button((810, 500), (315, 60), {"Normal": ImagePath("red", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "DELETE DATA", "", 28, White, Gray, self.font_path))
		self.panel_manager.add_object("game settings", "go back button", Button((810, 580), (315, 60), {"Normal": ImagePath("red", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "GO BACK", "", 28, White, Gray, self.font_path))
		self.panel_manager.add_object("game settings", "cloud animation", CloudAnimation(self.size))

		# Developer
		self.panel_manager.add_object("developer", "panel", Object(((self.width - 300) / 2, (self.height - 600) / 2), (300, 600), {"Normal": ImagePath("grey", "gui/panels")}))
		self.panel_manager.add_object("developer", "photo", Object(("CENTER", 270), (100, 100), {"Normal": ImagePath("cv", "gui/others")}, self.size))
		self.panel_manager.add_object("developer", "github", Button((835, 440), (250, 40), {"Normal": ImagePath("grey15", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "", "github.com/umutcanekinci", 28, Black, Gray))
		self.panel_manager.add_object("developer", "linkedin", Button((835, 490), (250, 40), {"Normal": ImagePath("grey15", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.panel_manager.add_object("developer", "instagram", Button((835, 540), (250, 40), {"Normal": ImagePath("grey15", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.panel_manager.add_object("developer", "facebook", Button((835, 590), (250, 40), {"Normal": ImagePath("grey15", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.panel_manager.add_object("developer", "x", Button((835, 640), (250, 40), {"Normal": ImagePath("grey15", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.panel_manager.add_object("developer", "youtube", Button((835, 690), (250, 40), {"Normal": ImagePath("grey15", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.panel_manager.add_object("developer", "go back button", Button((835, 760), (250, 40), {"Normal": ImagePath("red", "gui/buttons"), "Mouse Over": ImagePath("yellow", "gui/buttons")}, "GO BACK", "", 28, Black, Gray))
		self.panel_manager["developer"]["github"].states["Normal"].blit(load_image(ImagePath("github", "gui/others"), (32, 32)), (105, 5))
		self.panel_manager["developer"]["linkedin"].states["Normal"].blit(load_image(ImagePath("linkedin", "gui/others"), (32, 32)), (105, 5))
		self.panel_manager["developer"]["instagram"].states["Normal"].blit(load_image(ImagePath("instagram", "gui/others"), (32, 32)), (105, 5))
		self.panel_manager["developer"]["facebook"].states["Normal"].blit(load_image(ImagePath("facebook", "gui/others"), (32, 32)), (105, 5))
		self.panel_manager["developer"]["x"].states["Normal"].blit(load_image(ImagePath("x", "gui/others"), (32, 32)), (105, 5))
		self.panel_manager["developer"]["youtube"].states["Normal"].blit(load_image(ImagePath("youtube", "gui/others"), (32, 32)), (105, 5))
		self.panel_manager.add_object("developer", "cloud animation", CloudAnimation(self.size))

		# Game
		self.panel_manager.add_object("game", "clouds", GameClouds(self.cloud_count, self.size))
		self.panel_manager.add_object("game", "game panel", Object((0, self.height - 115), (1920, 100), {"Normal": ImagePath("grey", "gui/panels")}))
		self.panel_manager.add_object("game", "info mode button", Button((340, 985), (60, 60), {"On": ImagePath("green", "gui/buttons"), "Off": ImagePath("red", "gui/buttons")}))
		self.panel_manager.add_object("game", "info mode button image", Object((345, 990), (50, 50), {"Normal": ImagePath("info", "gui/others")}))
		self.panel_manager.add_object("game", "expand button", Button((560, 985), (200, 60), {"Normal": ImagePath("green", "gui/buttons"), "Mouse Over": ImagePath("red", "gui/buttons")}, "EXPAND", str(self.tiles.get_expand_cost()) + "$", 27, textFontPath=self.font_path))
		self.panel_manager.add_object("game", "build button", Button((860, 985), (200, 60), {"Normal": ImagePath("green", "gui/buttons"), "Mouse Over": ImagePath("red", "gui/buttons")}, "BUILD", str(self.buildings.get_build_cost()) + "$", 27, textFontPath=self.font_path))
		self.panel_manager.add_object("game", "next age button", Button((1160, 985), (200, 60), {"Normal": ImagePath("green", "gui/buttons"), "Mouse Over": ImagePath("red", "gui/buttons")}, "NEXT AGE", str(self.buildings.get_age_cost()) + "$", 27, textFontPath=self.font_path))


		self.panel_manager.add_object("game", "money_text", Text((1450, 995), "", 55, color=Green, background_color=Black, is_centered=False))


		self.panel_manager.add_object("game", "tiles", self.tiles)
		self.panel_manager.add_object("game", "buildings", self.buildings)
		self.panel_manager.add_object("game", "info panel", Object(((self.width - 250) / 2, (self.height - 400) / 2), (250, 400), {"Normal": ImagePath("grey", "gui/panels")}, visible=False))
		self.panel_manager.add_object("game", "info panel level text", Text(((self.width - 250) / 2 + 90, (self.height - 400) / 2 + 35), "Level: ", 15, True, Gray, font_path=self.font_path_thin, is_centered=False, visible=False))
		self.panel_manager.add_object("game", "info panel speed text", Text(((self.width - 250) / 2 + 90, (self.height - 400) / 2 + 50), "Speed: ", 15, True, Gray, font_path=self.font_path_thin, is_centered=False, visible=False))
		self.panel_manager.add_object("game", "info panel cooldown text", Text(((self.width - 250) / 2 + 90, (self.height - 400) / 2 + 65), "Cooldown: ", 15, True, Gray, font_path=self.font_path_thin, is_centered=False, visible=False))
		self.panel_manager.add_object("game", "info panel sell price text", Text(((self.width - 250) / 2 + 90, (self.height - 400) / 2 + 80), "Sell Price: ", 15, True, Gray, font_path=self.font_path_thin, is_centered=False, visible=False))
		self.panel_manager.add_object("game", "info panel building image", Object(((self.width - 250) / 2 + 20, (self.height - 400) / 2 + 20), (65, 89), visible=False))
		self.panel_manager.add_object("game", "info panel sell button", Button(((self.width - 250) / 2 + 20, (self.height - 400) / 2 + 325), (210, 50), {"Normal": ImagePath("green", "gui/buttons"), "Mouse Over": ImagePath("red", "gui/buttons")}, "SELL", "", 25, visible=False))
		self.panel_manager.add_object("game", "info panel close button", Button(((self.width - 250) / 2 + 250 - 20, (self.height - 400) / 2 - 12), None, {"Normal": ImagePath("red_circle", "gui/buttons"), "Mouse Over": ImagePath("yellow_circle", "gui/buttons")}, visible=False))
		self.panel_manager.add_object("game", "cloud animation", CloudAnimation(self.size))

		self.panel_manager["game"]["info mode button"].set_status("Off")
		self.panel_manager["game"]["info panel close button"].states["Normal"].blit(load_image(ImagePath("grey_crossWhite", "gui/others")), (9, 9))
		self.panel_manager["game"]["info panel close button"].states["Mouse Over"].blit(load_image(ImagePath("grey_crossGrey", "gui/others")), (9, 9))

		self.set_age(self.buildings.age_number)
		self.update_button_texts()

	def get_data(self) -> None:
		self.database = Database("database")

		if not self.database.connect():
			self.exit()

		self.database.execute("CREATE TABLE IF NOT EXISTS game(age_number INTEGER, size INTEGER, money INTEGER, music_volume INTEGER, sfx_volume INTEGER)")
		self.database.commit()
		self.database.disconnect()

		if not self.database.connect():
			self.exit()

		game_data = self.database.execute("SELECT * FROM game").fetchall()

		if not game_data:
			self.database.execute("INSERT INTO game(age_number, size, money, music_volume, sfx_volume) VALUES(0, 2, " + str(self.starting_money) + ", " + str(self.default_music_volume) + ", " + str(self.default_sfx_volume) + ")")
			self.database.commit()
			self.database.disconnect()

			if self.database.connect():
				game_data = self.database.execute("SELECT * FROM game").fetchall()
			else:
				self.exit()

		age_number, size, self.money, self.music_volume, self.sfx_volume = game_data[0]

		self.tiles = Tiles(size, self.max_size)

		self.database.execute("CREATE TABLE IF NOT EXISTS buildings(level INTEGER, row INTEGER, column INTEGER)")
		self.database.commit()
		self.database.disconnect()

		if not self.database.connect():
			self.exit()

		buildings = self.database.execute("SELECT * FROM buildings").fetchall()

		self.buildings = Buildings(self.sfx_volume)
		self.buildings.age_number = age_number

		for building in buildings:
			self.add_building(*building)

		self.database.disconnect()

	def delete_data(self) -> None:

		if not self.database.connect():
			self.exit()

		self.database.execute("DELETE FROM game")
		self.database.commit()
		self.database.disconnect()

		if not self.database.connect():
			self.exit()

		self.database.execute("DELETE FROM buildings")
		self.database.commit()
		self.database.disconnect()

	def update_button_texts(self) -> None:
		if self.tiles.is_max_size():
			self.panel_manager["game"]["expand button"].text.update_text("Mouse Over", "MAX SIZE")
		else:
			self.panel_manager["game"]["expand button"].text.update_text("Mouse Over", str(self.tiles.get_expand_cost()) + "$")

		if len(self.buildings) == self.tiles.rowCount * self.tiles.columnCount:
			self.panel_manager["game"]["build button"].text.update_text("Mouse Over", "TILES ARE FULL")
			self.panel_manager["game"]["build button"].text.update_size("Mouse Over", 17)
		else:
			self.panel_manager["game"]["build button"].text.update_text("Mouse Over", str(self.buildings.get_build_cost()) + "$")
			self.panel_manager["game"]["build button"].text.update_size("Mouse Over", 27)

		if self.buildings.age_number == self.buildings.max_age_number:
			self.panel_manager["game"]["next age button"].text.update_text("Mouse Over", "MAX AGE")
		else:
			self.panel_manager["game"]["next age button"].text.update_text("Mouse Over", str(self.buildings.get_age_cost()) + "$")

	def control_selecting_tile(self) -> None:
		is_there_selected = self.tiles.is_there_selected_tile()

		for row in self.tiles:
			for tile in row:
				is_over = tile.is_mouse_over(self.mouse.position)

				if is_over:
					if not is_there_selected:
						tile.selected = True
						if self.panel_manager["game"]["info mode button"].status == "On":
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
		panel = self.panel_manager.current_panel
		if panel == "menu":

			if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
				if self.panel_manager[panel]["menu"].buttons["START"].status == "Selected":
					self.play_sfx(self.click_sound_path); self.open_panel("game")
				elif self.panel_manager[panel]["menu"].buttons["SETTINGS"].status == "Selected":
					self.play_sfx(self.click_sound_path); self.open_panel("settings")
				elif self.panel_manager[panel]["menu"].buttons["DEVELOPER"].status == "Selected":
					self.play_sfx(self.click_sound_path); self.open_panel("developer")
				elif self.panel_manager[panel]["menu"].buttons["EXIT"].status == "Selected":
					self.play_sfx(self.click_sound_path); self.exit()

			if self.panel_manager[panel]["menu"].buttons["START"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); self.open_panel("game")
			elif self.panel_manager[panel]["menu"].buttons["SETTINGS"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); self.open_panel("settings")
			elif self.panel_manager[panel]["menu"].buttons["DEVELOPER"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); self.open_panel("developer")
			elif self.panel_manager[panel]["menu"].buttons["EXIT"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.go_back_sound_path); self.exit()

		elif panel == "settings":

			if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
				if self.panel_manager[panel]["menu"].buttons["display_settings"].status == "Selected":
					self.play_sfx(self.click_sound_path); self.open_panel("display_settings")
				elif self.panel_manager[panel]["menu"].buttons["audio_settings"].status == "Selected":
					self.old_music_volume, self.old_sfx_volume = self.music_volume, self.sfx_volume
					self.play_sfx(self.click_sound_path); self.open_panel("audio_settings")
				elif self.panel_manager[panel]["menu"].buttons["GAME SETTINGS"].status == "Selected":
					self.play_sfx(self.click_sound_path); self.open_panel("game settings")
				elif self.panel_manager[panel]["menu"].buttons["GO BACK"].status == "Selected":
					self.play_sfx(self.click_sound_path); self.open_panel("menu")

			if self.panel_manager[panel]["menu"].buttons["display_settings"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); self.open_panel("display_settings")
			elif self.panel_manager[panel]["menu"].buttons["audio_settings"].is_clicked(event, self.mouse.position):
				self.old_music_volume, self.old_sfx_volume = self.music_volume, self.sfx_volume
				self.play_sfx(self.click_sound_path); self.open_panel("audio_settings")
			elif self.panel_manager[panel]["menu"].buttons["GAME SETTINGS"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); self.open_panel("game settings")
			elif self.panel_manager[panel]["menu"].buttons["GO BACK"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); self.open_panel("menu")

		elif panel == "display_settings":

			if self.panel_manager[panel]["go back button"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); self.open_panel("settings")

		elif panel == "audio_settings":

			if self.panel_manager[panel]["music volume plus button"].is_clicked(event, self.mouse.position):
				if self.music_volume != 1.0: self.set_music_volume(self.music_volume + 0.1)
			elif self.panel_manager[panel]["music volume minus button"].is_clicked(event, self.mouse.position):
				if self.music_volume > 0.0: self.set_music_volume(self.music_volume - 0.1)
			elif self.panel_manager[panel]["SFX volume plus button"].is_clicked(event, self.mouse.position):
				if self.sfx_volume != 1.0: self.set_sfx_volume(self.sfx_volume + 0.1)
			elif self.panel_manager[panel]["SFX volume minus button"].is_clicked(event, self.mouse.position):
				if self.sfx_volume > 0.0: self.set_sfx_volume(self.sfx_volume - 0.1)
			elif self.panel_manager[panel]["cancel button"].is_clicked(event, self.mouse.position):
				self.set_music_volume(self.old_music_volume); self.set_sfx_volume(self.old_sfx_volume)
				self.play_sfx(self.go_back_sound_path); self.open_panel("settings")
			elif self.panel_manager[panel]["save button"].is_clicked(event, self.mouse.position):
				if self.database.connect():
					self.database.execute("UPDATE game SET music_volume='" + str(self.music_volume) + "', sfx_volume='" + str(self.sfx_volume) + "'")
					self.database.commit(); self.database.disconnect()
				else:
					self.exit()
				self.play_sfx(self.go_back_sound_path); self.open_panel("settings")

		elif panel == "game settings":

			if self.panel_manager[panel]["delete data button"].is_clicked(event, self.mouse.position):
				self.delete_data(); self.get_data(); self.add_objects()
				self.play_sfx(self.click_sound_path); self.open_panel("menu")
			elif self.panel_manager[panel]["go back button"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); self.open_panel("settings")

		elif panel == "developer":

			if self.panel_manager[panel]["github"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); webbrowser.open("https://www.github.com/umutcanekinci/")
			elif self.panel_manager[panel]["linkedin"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); webbrowser.open("https://www.linkedin.com/in/umutcanekinci/")
			elif self.panel_manager[panel]["instagram"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); webbrowser.open("https://www.instagram.com/umut_ekinci_/")
			elif self.panel_manager[panel]["facebook"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); webbrowser.open("https://www.facebook.com/nmuetn/")
			elif self.panel_manager[panel]["x"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); webbrowser.open("https://twitter.com/muetnmuetn/")
			elif self.panel_manager[panel]["youtube"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); webbrowser.open("https://www.youtube.com/channel/UC1ma8tkbaD-xxJ4tgSxDthg/")
			elif self.panel_manager[panel]["go back button"].is_clicked(event, self.mouse.position):
				self.play_sfx(self.click_sound_path); self.open_panel("menu")

		elif panel == "game":

			if self.panel_manager["game"]["info panel"].visible:

				if self.panel_manager[panel]["info panel sell button"].is_clicked(event, self.mouse.position):
					self.buildings.remove(self.info_building)
					self.money += self.info_building.sell_price
					self.close_info_panel()
					self.play_sfx(self.go_back_sound_path)
					self.update_button_texts()
				elif self.panel_manager["game"]["info panel close button"].is_clicked(event, self.mouse.position):
					self.close_info_panel()
					self.play_sfx(self.go_back_sound_path)
					self.control_selecting_tile()

			else:

				self.control_selecting_tile()

				if self.panel_manager[panel]["info mode button"].is_clicked(event, self.mouse.position):
					status = "Off" if self.panel_manager["game"]["info mode button"].status == "On" else "On"
					self.panel_manager[panel]["info mode button"].set_status(status)
					self.play_sfx(self.click_sound_path)

				if self.panel_manager["game"]["info mode button"].status == "On" and event.type == pygame.MOUSEBUTTONUP:
					for row in self.tiles:
						for tile in row:
							if tile.selected:
								for building in self.buildings:
									if building.tile == tile:
										self.open_info_panel(building)
										self.play_sfx(self.click_sound_path)
										break
								break

				if self.panel_manager[panel]["expand button"].is_clicked(event, self.mouse.position):
					self.expand()
				elif self.panel_manager[panel]["build button"].is_clicked(event, self.mouse.position):
					self.create_building()
				elif self.panel_manager[panel]["next age button"].is_clicked(event, self.mouse.position):
					self.next_age()

			if event.type == pygame.KEYUP and not self.panel_manager["game"]["info panel"].visible:

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

	def on_exit(self) -> None:
		self.play_sfx(self.go_back_sound_path)

		if self.panel_manager.current_panel == "menu":
			self.exit()
		elif self.panel_manager.current_panel == "settings":
			self.open_panel("menu")
		elif self.panel_manager.current_panel == "display_settings":
			self.open_panel("settings")
		elif self.panel_manager.current_panel == "audio_settings":
			SoundManager.set_volume(0, self.old_music_volume)
			SoundManager.set_volume(1, self.old_sfx_volume)
			self.open_panel("settings")
		elif self.panel_manager.current_panel == "game settings":
			self.open_panel("settings")
		elif self.panel_manager.current_panel == "developer":
			self.open_panel("menu")
		elif self.panel_manager.current_panel == "game":
			if self.panel_manager["game"]["info panel"].visible:
				self.close_info_panel()
			else:
				if self.database.connect():
					self.database.execute("UPDATE game SET age_number='" + str(self.buildings.age_number) + "', size='" + str(self.tiles.rowCount) + "', money='" + str(self.money) + "'")
					self.database.commit()
					self.database.disconnect()

					if self.database.connect():
						self.database.execute("DELETE FROM buildings")
						self.database.commit()
						self.database.disconnect()

						for building in self.buildings:
							if self.database.connect():
								self.database.execute("INSERT INTO buildings(level, row, column) VALUES(" + str(building.level) + ", " + str(building.tile.row_number) + ", " + str(building.tile.column_number) + ")")
								self.database.commit()
								self.database.disconnect()
							else:
								self.exit()
					else:
						self.exit()

				self.open_panel("menu")

	def open_info_panel(self, building: Building) -> None:

		self.info_building = building
		panel = self.panel_manager[self.panel_manager.current_panel]
		panel["info panel level text"].update_text("Normal", "Level: " + str(building.level))
		panel["info panel speed text"].update_text("Normal", "Speed: " + str(building.speed) + " $/sec")
		panel["info panel cooldown text"].update_text("Normal", "Cooldown: " + str(building.cooldown) + " sec")
		panel["info panel sell price text"].update_text("Normal", "Sell Price: " + str(building.sell_price))
		panel["info panel sell button"].text.update_text("Mouse Over", str(building.sell_price) + "$")
		panel["info panel building image"].add_surface("Normal", load_image(building.get_image_path(), (65, 89)))

		panel["info panel"].show()
		panel["info panel level text"].show()
		panel["info panel speed text"].show()
		panel["info panel cooldown text"].show()
		panel["info panel sell price text"].show()
		panel["info panel close button"].show()
		panel["info panel sell button"].show()
		panel["info panel building image"].show()

	def close_info_panel(self) -> None:
		panel = self.panel_manager[self.panel_manager.current_panel]
		panel["info panel"].hide()
		panel["info panel level text"].hide()
		panel["info panel speed text"].hide()
		panel["info panel cooldown text"].hide()
		panel["info panel sell price text"].hide()
		panel["info panel close button"].hide()
		panel["info panel sell button"].hide()
		panel["info panel building image"].hide()

	def move_buildings(self, rotation: str) -> None:
		is_moving = any(b.get_component(Rigidbody2D).velocity != pygame.math.Vector2(0, 0) for b in self.buildings)

		if self.panel_manager["game"]["info mode button"].status == "Off" and not is_moving:
			if rotation in ("up", "down"):

				for col in range(self.tiles.columnCount):
					col_buildings = sorted(
						[b for b in self.buildings if b.tile.column_number == col + 1],
						key=lambda b: b.tile.row_number,
						reverse=(rotation == "down")
					)

					if not col_buildings: continue

					previous = None
					target = 0
					for building in col_buildings:
						row_idx = target if rotation == "up" else self.tiles.rowCount - target - 1
						expected = row_idx + 1 if rotation == "up" else self.tiles.rowCount - target
						if not previous:
							if building.tile.row_number != expected:
								building.set_target_tile(self.tiles[row_idx][col])
							previous = building
							target += 1
						elif previous.level == building.level and self.max_building_level > building.level:
							previous.level_up(building)
							previous = None
						else:
							if building.tile.row_number != expected:
								building.set_target_tile(self.tiles[row_idx][col])
							previous = building
							target += 1

			elif rotation in ("left", "right"):
				for row in range(self.tiles.rowCount):
					row_buildings = sorted(
						[b for b in self.buildings if b.tile.row_number == row + 1],
						key=lambda b: b.tile.column_number,
						reverse=(rotation == "right")
					)

					if not row_buildings: continue

					previous = None
					target = 0
					for building in row_buildings:
						col_idx = target if rotation == "left" else self.tiles.columnCount - target - 1
						expected = col_idx + 1 if rotation == "left" else self.tiles.columnCount - target
						if not previous:
							if building.tile.column_number != expected:
								building.set_target_tile(self.tiles[row][col_idx])
							previous = building
							target += 1
						elif previous.level == building.level and self.max_building_level > building.level:
							previous.level_up(building)
							previous = None
						else:
							if building.tile.column_number != expected:
								building.set_target_tile(self.tiles[row][col_idx])
							previous = building
							target += 1

			self.buildings.sort(key=lambda b: b.tile.column_number)

	def add_building(self, level, row_number, column_number) -> None:
		new_building = Building(level, self.buildings.age_number, self.tiles[row_number - 1][column_number - 1])
		self.buildings.append(new_building)
		self.buildings.sort(key=lambda b: b.tile.column_number)

		if len(self.buildings) == self.tiles.rowCount * self.tiles.columnCount and "game" in self and "build button" in self.panel_manager["game"]:
			self.panel_manager["game"]["build button"].text.update_text("Mouse Over", "TILES ARE FULL")
			self.panel_manager["game"]["build button"].text.update_size("Mouse Over", 17)

	def create_building(self) -> None:
		is_moving = any(b.velocity != pygame.math.Vector2(0, 0) for b in self.buildings)

		if not is_moving and self.money >= self.buildings.get_build_cost():
			empty_tiles = [
				(r + 1, c + 1)
				for r in range(self.tiles.rowCount)
				for c in range(self.tiles.columnCount)
			]

			for building in self.buildings:
				empty_tiles.remove((building.tile.row_number, building.tile.column_number))

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

		if (self.panel_manager.current_panel in self.panel_manager and
				"cloud animation" in self.panel_manager[self.panel_manager.current_panel]):
			self.panel_manager[self.panel_manager.current_panel]["cloud animation"].create_clouds()

	def update_money(self) -> None:

		now = pygame.time.get_ticks()

		for building in self.buildings:

			if not building.last_time:
				building.last_time = now

			if now - building.last_time > building.cooldown * 1000:
				self.money += building.cooldown * building.speed
				building.last_time = pygame.time.get_ticks()

		self.panel_manager[self.panel_manager.current_panel]["money_text"].update_text("Normal", str(self.money) + "$")

	def draw(self) -> None:
		self.panel_manager.draw(self.window)
		if self.panel_manager.current_panel == "game":
			self.update_money()

		super().draw()
