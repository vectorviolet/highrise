#region #-# Import Packages #-#

try:

	import pygame
	from pygame.math import Vector2

	from random import choice
	import webbrowser

	from scripts.default.application import Application
	from scripts.default.database import Database
	from scripts.default.button import Button
	from scripts.default.color import *
	from scripts.default.object import Object
	from scripts.default.image import GetImage
	from scripts.default.path import *
	from scripts.default.text import Text
	from scripts.building import Building, Buildings
	from scripts.cloud import CloudAnimation, GameClouds
	from scripts.menu import Menu
	from scripts.tile import Tiles
	
except Exception as error:

	print("An error occured during importing packages:", error)

#endregion

#-# Game Class #-#
class Game(Application):

	def __init__(self) -> None:
		
		#region Settings

		#-# Window Settings #-#
		self.cursorSize = 25, 25
		self.backgroundColors = {"menu" : Yellow, "settings" : Yellow, "display settings" : Yellow, "audio settings" : Yellow, "game settings" : Yellow, "developer" : Yellow, "game" : CustomBlue}
		super().__init__("2048 GAME", (1440, 900), self.backgroundColors, 165)

		#-# Game Settings #-#
		self.cloudCount = 30
		self.maxSize = 7
		self.maxBuildingLevel = 6
		self.startingMoney = 10000
		self.defaultMusicVolume = 1.00
		self.defaultSFXVolume = 1.00

		#endregion

		#region Paths

		#-# Font Paths #-#
		self.fontPath = FontPath("kenvector_future")
		self.fontPathThin = FontPath("kenvector_future_thin")

		#-# Sound Paths #-#
		self.backgroundMusicSoundPath = SoundPath("music", extension="mp3")
		self.clickSoundPath = SoundPath("click")
		self.goBackSoundPath = SoundPath("back")

		#endregion

	def Run(self) -> None:

		#-# Set Cursor #-#
		self.SetCursorVisible(False)
		self.SetCursorImage(Object((0, 0), self.cursorSize, {"Normal" : ImagePath("cursor")}))

		#-# Start The Application #-#
		self.GetData()
		self.AddObjects()
		self.OpenTab("menu")

		#-# Play Background Music #-#
		self.SetMusicVolume(self.musicVolume)
		self.SetSFXVolume(self.SFXVolume)
		self.PlayMusic(self.backgroundMusicSoundPath) 
		
		super().Run()

	#region #-# Music #-#

	def PlayMusic(self, soundPath: SoundPath) -> None:

		self.PlaySound(0, soundPath, self.musicVolume, -1)

	def SetMusicVolume(self, volume: float) -> None:

		if volume < 0:

			volume = 0
		
		if volume > 1:

			volume = 1

		self.musicVolume = self["menu"]["menu"].SFXVolume = self["settings"]["menu"].SFXVolume = self["audio settings"]["menu"].SFXVolume = self.SFXVolume = volume
		self["audio settings"]["music volume entry"].text.UpdateText("Normal", "%" + str(round(self.musicVolume*100)))
		self.SetVolume(0, volume)

	def PlaySFX(self, soundPath: SoundPath) -> None:

		self.PlaySound(1, soundPath, self.SFXVolume)

	def SetSFXVolume(self, volume: float) -> None:

		if volume < 0:

			volume = 0
		
		elif volume > 1:

			volume = 1

		self.buildings.SFXVolume = self["menu"]["menu"].SFXVolume = self["settings"]["menu"].SFXVolume = self["audio settings"]["menu"].SFXVolume = self.SFXVolume = volume
		self["audio settings"]["SFX volume entry"].text.UpdateText("Normal", "%" + str(round(self.SFXVolume*100)))
		self.SetVolume(1, volume)

	#endregion

	def AddObjects(self) -> None:

		#region #-# Menu tab #-#

		self.AddObject("menu", "menu", Menu(ImagePath("blue3", "gui/buttons"), self.title, 30, White, self.fontPath, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", ["START", "SETTINGS", "DEVELOPER", "EXIT"], 30, Gray, White, self.fontPath, self.size))
		self.AddObject("menu", "cloud animation", CloudAnimation(self.size))
		
		#endregion

		#region #-# Settings tab #-#

		self.AddObject("settings", "menu", Menu(ImagePath("blue3", "gui/buttons"), "SETTINGS", 30, White, self.fontPath, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", ["DISPLAY SETTINGS", "AUDIO SETTINGS", "GAME SETTINGS", "GO BACK"], 30, Gray, White, self.fontPath, self.size))
		self.AddObject("settings", "cloud animation", CloudAnimation(self.size))
		
		#endregion

		#region #-# Display Settings tab #-#

		self.AddObject("display settings", "menu", Menu(ImagePath("blue3", "gui/buttons"), "DISPLAY SETTINGS", 30, White, self.fontPath, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", [], 30, Gray, White, self.fontPath, self.size, 200))
		self.AddObject("display settings", "information", Text(((self.width - 300)/2, (self.height - 600)/2 + 280), "THIS PAGE WILL COMING SOON...", 25, color=Black, isCentered=False))
		self.AddObject("display settings", "go back button", Button((570, 490), (315, 60), {"Normal" : ImagePath("red", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "GO BACK", "", 28, White, Gray, self.fontPath))
		self.AddObject("display settings", "cloud animation", CloudAnimation(self.size))
		
		#endregion

		#region #-# Audio Settings tab #-#

		#-# Volume #-#
		self.AddObject("audio settings", "menu", Menu(ImagePath("blue3", "gui/buttons"), "AUDIO SETTINGS", 30, White, self.fontPath, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", [], 30, Gray, White, self.fontPath, self.size, 500))
		self.AddObject("audio settings", "music volume text", Text((610, 290), "MUSIC VOLUME", 25, color=Gray, fontPath=self.fontPath, isCentered=False))
		self.AddObject("audio settings", "music volume minus button", Button((600, 340), (36, 36), {"Normal" : ImagePath("blue_circle", "gui/buttons"), "Mouse Over" : ImagePath("yellow_circle", "gui/buttons")}))
		self.AddObject("audio settings", "music volume entry", Button((645, 340), (150, 35), {"Normal" : ImagePath("grey8", "gui/buttons")}, "%100", textSize=25, textColor=Gray, textFontPath=self.fontPath))
		self.AddObject("audio settings", "music volume plus button", Button((814, 340), (36, 36), {"Normal" : ImagePath("blue_circle", "gui/buttons"), "Mouse Over" : ImagePath("yellow_circle", "gui/buttons")}))
		self["audio settings"]["music volume minus button"]["Normal"].blit(GetImage(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self["audio settings"]["music volume minus button"]["Mouse Over"].blit(GetImage(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self["audio settings"]["music volume plus button"]["Normal"].blit(GetImage(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))
		self["audio settings"]["music volume plus button"]["Mouse Over"].blit(GetImage(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))

		#-# SFX Volume #-#
		self.AddObject("audio settings", "SFX volume text", Text((580, 460), "SOUND FX VOLUME", 25, color=Gray, fontPath=self.fontPath, isCentered=False))
		self.AddObject("audio settings", "SFX volume minus button", Button((600, 510), (36, 36), {"Normal" : ImagePath("blue_circle", "gui/buttons"), "Mouse Over" : ImagePath("yellow_circle", "gui/buttons")}))
		self.AddObject("audio settings", "SFX volume entry", Button((645, 510), (150, 35), {"Normal" : ImagePath("grey8", "gui/buttons")}, "%100", textSize=25, textColor=Gray, textFontPath=self.fontPath))
		self.AddObject("audio settings", "SFX volume plus button", Button((814, 510), (36, 36), {"Normal" : ImagePath("blue_circle", "gui/buttons"), "Mouse Over" : ImagePath("yellow_circle", "gui/buttons")}))
		self["audio settings"]["SFX volume minus button"]["Normal"].blit(GetImage(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self["audio settings"]["SFX volume minus button"]["Mouse Over"].blit(GetImage(ImagePath("minus", "gui/others"), (16, 16)), (10, 10))
		self["audio settings"]["SFX volume plus button"]["Normal"].blit(GetImage(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))
		self["audio settings"]["SFX volume plus button"]["Mouse Over"].blit(GetImage(ImagePath("plus", "gui/others"), (16, 16)), (10, 10))

		#-# Buttons #-#
		self.AddObject("audio settings", "cancel button", Button((570, 620), (150, 60), {"Normal" : ImagePath("red", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "CANCEL", "", 28, White, Gray, self.fontPath))
		self.AddObject("audio settings", "save button", Button((735, 620), (150, 60), {"Normal" : ImagePath("green", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "SAVE", "", 28, White, Gray, self.fontPath))
		self.AddObject("audio settings", "cloud animation", CloudAnimation(self.size))

		#endregion

		#region #-# Game Settings tab #-#

		self.AddObject("game settings", "menu", Menu(ImagePath("blue3", "gui/buttons"), "GAME SETTINGS", 30, White, self.fontPath, ImagePath("grey", "gui/panels"), (400, 60), "blue", "yellow", [], 30, Gray, White, self.fontPath, self.size, 200))
		self.AddObject("game settings", "delete data button", Button((570, 410), (315, 60), {"Normal" : ImagePath("red", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "DELETE DATA", "", 28, White, Gray, self.fontPath))
		self.AddObject("game settings", "go back button", Button((570, 490), (315, 60), {"Normal" : ImagePath("red", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "GO BACK", "", 28, White, Gray, self.fontPath))
		self.AddObject("game settings", "cloud animation", CloudAnimation(self.size))

		#endregion

		#region #-# Developer tab #-#

		self.AddObject("developer", "panel", Object(((self.width - 300)/2, (self.height - 600)/2), (300, 600), {"Normal" : ImagePath("grey", "gui/panels")}))
		self.AddObject("developer", "photo", Object(("CENTER", 180), (100, 100), {"Normal" : ImagePath("cv", "gui/others")}, self.size))
		self.AddObject("developer", "name", Text((640, 290), "Umutcan Ekinci", 30, color=Black, isCentered=False))
		self.AddObject("developer", "nickname", Text((675, 310), "LordCh4os", 25, color=Gray, isCentered=False))
		
		self.AddObject("developer", "github", Button((595, 350), (250, 40), {"Normal" : ImagePath("grey15", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "", "github.com/LordCh4os", 28, Black, Gray))
		self.AddObject("developer", "linkedin", Button((595, 400), (250, 40), {"Normal" : ImagePath("grey15", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.AddObject("developer", "instagram", Button((595, 450), (250, 40), {"Normal" : ImagePath("grey15", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.AddObject("developer", "facebook", Button((595, 500), (250, 40), {"Normal" : ImagePath("grey15", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.AddObject("developer", "x", Button((595, 550), (250, 40), {"Normal" : ImagePath("grey15", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.AddObject("developer", "youtube", Button((595, 600), (250, 40), {"Normal" : ImagePath("grey15", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "", "instagram.com/umut_ekinci_", 28, Black, Gray))
		self.AddObject("developer", "go back button", Button((595, 670), (250, 40), {"Normal" : ImagePath("red", "gui/buttons"), "Mouse Over" : ImagePath("yellow", "gui/buttons")}, "GO BACK", "", 28, Black, Gray))

		self["developer"]["github"]["Normal"].blit(GetImage(ImagePath("github", "gui/others"), (32, 32)), (105, 5))
		self["developer"]["linkedin"]["Normal"].blit(GetImage(ImagePath("linkedin", "gui/others"), (32, 32)), (105, 5))
		self["developer"]["instagram"]["Normal"].blit(GetImage(ImagePath("instagram", "gui/others"), (32, 32)), (105, 5))
		self["developer"]["facebook"]["Normal"].blit(GetImage(ImagePath("facebook", "gui/others"), (32, 32)), (105, 5))
		self["developer"]["x"]["Normal"].blit(GetImage(ImagePath("x", "gui/others"), (32, 32)), (105, 5))
		self["developer"]["youtube"]["Normal"].blit(GetImage(ImagePath("youtube", "gui/others"), (32, 32)), (105, 5))

		self.AddObject("developer", "cloud animation", CloudAnimation(self.size))

		#endregion
		
		#region #-# Game tab #-#

		self.AddObject("game", "clouds", GameClouds(self.cloudCount, self.size))
		self.AddObject("game", "game panel", Object((20, self.height - 100 - 20), (1400, 100), {"Normal" : ImagePath("grey", "gui/panels")}))
		self.AddObject("game", "info mode button", Button((100, 800), (60, 60),  {"On" : ImagePath("green", "gui/buttons"), "Off" : ImagePath("red", "gui/buttons")}))
		self.AddObject("game", "info mode button image", Object((105, 805), (50, 50), {"Normal" : ImagePath("info", "gui/others")}))
		self.AddObject("game", "expand button", Button((320, 800), (200, 60), {"Normal" : ImagePath("green", "gui/buttons"), "Mouse Over" : ImagePath("red", "gui/buttons")}, "EXPAND", str(self.tiles.GetExpandCost()) + "$", 27, textFontPath=self.fontPath))
		self.AddObject("game", "build button", Button((620, 800), (200, 60), {"Normal" : ImagePath("green", "gui/buttons"), "Mouse Over" : ImagePath("red", "gui/buttons")}, "BUILD", str(self.buildings.GetBuildCost()) + "$", 27, textFontPath=self.fontPath))
		self.AddObject("game", "next age button", Button((920, 800), (200, 60), {"Normal" : ImagePath("green", "gui/buttons"), "Mouse Over" : ImagePath("red", "gui/buttons")}, "NEXT AGE", str(self.buildings.GetAgeCost()) + "$", 27, textFontPath=self.fontPath))
		self.AddObject("game", "money text", Text((1180, 810), "", 55, color=Green, backgroundColor=Black, isCentered=False))
		self.AddObject("game", "tiles", self.tiles)
		self.AddObject("game", "buildings", self.buildings)

		self.AddObject("game", "info panel", Object(((self.width - 250)/2, (self.height - 400)/2), (250, 400), {"Normal" : ImagePath("grey", "gui/panels")}, show=False))
		self.AddObject("game", "info panel level text", Text(((self.width - 250)/2 + 90, (self.height - 400)/2 + 35), "Level: ", 15, True, Gray, fontPath=self.fontPathThin, isCentered=False, show=False))
		self.AddObject("game", "info panel speed text", Text(((self.width - 250)/2 + 90, (self.height - 400)/2 + 50), "Speed: ", 15, True, Gray, fontPath=self.fontPathThin, isCentered=False, show=False))
		self.AddObject("game", "info panel cooldown text", Text(((self.width - 250)/2 + 90, (self.height - 400)/2 + 65), "Cooldown: ", 15, True, Gray, fontPath=self.fontPathThin, isCentered=False, show=False))
		self.AddObject("game", "info panel sell price text", Text(((self.width - 250)/2 + 90, (self.height - 400)/2 + 80), "Sell Price: ", 15, True, Gray, fontPath=self.fontPathThin, isCentered=False, show=False))
		self.AddObject("game", "info panel building image", Object(((self.width - 250)/2 + 20, (self.height - 400)/2 + 20), (65, 89), show=False))
		self.AddObject("game", "info panel sell button", Button(((self.width - 250)/2 + 20, (self.height - 400)/2 + 325), (210, 50), {"Normal" : ImagePath("green", "gui/buttons"), "Mouse Over" : ImagePath("red", "gui/buttons")}, "SELL", "", 25, show=False))
		self.AddObject("game", "info panel close button", Button(((self.width - 250)/2 + 250 - 20, (self.height - 400)/2 - 12), None, {"Normal" : ImagePath("red_circle", "gui/buttons"), "Mouse Over" : ImagePath("yellow_circle", "gui/buttons")}, show=False))
		
		self.AddObject("game", "cloud animation", CloudAnimation(self.size))
		
		self["game"]["info mode button"].SetStatus("Off")
		self["game"]["info panel close button"]["Normal"].blit(GetImage(ImagePath("grey_crossWhite", "gui/others")), (9, 9))
		self["game"]["info panel close button"]["Mouse Over"].blit(GetImage(ImagePath("grey_crossGrey", "gui/others")), (9, 9))
		
		self.SetAge(self.buildings.ageNumber)
		self.UpdateButtonTexts()

		#endregion
	
	#region #-# Database #-#

	def GetData(self) -> None:

		self.database = Database("database")
	
		if self.database.Connect():

			sqlCode = "CREATE TABLE IF NOT EXISTS game(age_number INTEGER, size INTEGER, money INTEGER, music_volume INTEGER, sfx_volume INTEGER)"
			self.database.Execute(sqlCode)
			self.database.Commit()
			self.database.Disconnect()

			if self.database.Connect():

				sqlCode = "SELECT * FROM game"
				self.database.Execute(sqlCode)
				gameData = self.database.Execute(sqlCode).fetchall()

				if not gameData:

					sqlCode = "INSERT INTO game(age_number, size, money, music_volume, sfx_volume) VALUES(0, 2, "+str(self.startingMoney)+", "+str(self.defaultMusicVolume)+", "+str(self.defaultSFXVolume)+")"
					self.database.Execute(sqlCode)
					self.database.Commit()
					self.database.Disconnect()

					if self.database.Connect():

						sqlCode = "SELECT * FROM game"
						gameData = self.database.Execute(sqlCode).fetchall()

					else:

						self.Exit()

				ageNumber, size, self.money, self.musicVolume, self.SFXVolume  = gameData[0]

				self.tiles = Tiles(size, self.maxSize)

				self.database.Execute("CREATE TABLE IF NOT EXISTS buildings(level INTEGER, row INTEGER, column INTEGER)")
				self.database.Commit()
				self.database.Disconnect()

				if self.database.Connect():

					data = self.database.Execute("SELECT * FROM buildings")
					buildings = data.fetchall()

					self.buildings = Buildings(self.SFXVolume)
					self.buildings.ageNumber = ageNumber

					for building in buildings:

						self.AddBuilding(*building)
					
					self.database.Disconnect()
						  
				else:
				
					self.Exit()

			else:

				self.Exit()

		else:

			self.Exit()

	def DeleteData(self) -> None:

		if self.database.Connect():

			sqlCode = "DELETE FROM game"
			self.database.Execute(sqlCode)
			self.database.Commit()
			self.database.Disconnect()

			if self.database.Connect():

				sqlCode = "DELETE FROM buildings"
				self.database.Execute(sqlCode)
				self.database.Commit()
				self.database.Disconnect()

			else: 

				self.Exit()

		else: 

			self.Exit()

	#endregion

	def UpdateButtonTexts(self) -> None:

		if self.tiles.isMaxSize():

			self["game"]["expand button"].text.UpdateText("Mouse Over", "MAX SIZE")
		
		else:

			self["game"]["expand button"].text.UpdateText("Mouse Over", str(self.tiles.GetExpandCost()) + "$")
		
		if len(self.buildings) == self.tiles.rowCount*self.tiles.columnCount:
			
			self["game"]["build button"].text.UpdateText("Mouse Over", "TILES ARE FULL")
			self["game"]["build button"].text.UpdateSize("Mouse Over", 17)

		else:

			self["game"]["build button"].text.UpdateText("Mouse Over", str(self.buildings.GetBuildCost()) + "$")
			self["game"]["build button"].text.UpdateSize("Mouse Over", 27)

		if self.buildings.ageNumber == self.buildings.maxAgeNumber:
			
			self["game"]["next age button"].text.UpdateText("Mouse Over", "MAX AGE")

		else:

			self["game"]["next age button"].text.UpdateText("Mouse Over", str(self.buildings.GetAgeCost()) + "$")

	def ControlSelectingTile(self) -> None:

		isThereAnySelectedTile = self.tiles.isThereSelectedTile()

		for row in self.tiles:

			for tile in row:
				
				isMouseOver = tile.isMouseOver(self.mousePosition)

				if isMouseOver:

					if not isThereAnySelectedTile:
						
						tile.selected = True
						
						if self["game"]["info mode button"].status == "On":

							tile.rect = tile.selectedRect
						
				else:

					tile.selected = False
					tile.rect = tile.unselectedRect

	def Expand(self) -> None:
		
		if self.money >= self.tiles.GetExpandCost():

			if not self.tiles.isMaxSize():

				self.money -= self.tiles.GetExpandCost()
				self.tiles.Expand()

				for building in self.buildings:

					building.tile = self.tiles[building.tile.rowNumber - 1][building.tile.columnNumber - 1]

				self.UpdateButtonTexts()
				self.PlaySFX(self.clickSoundPath)
	
	#region #-# Events #-#

	def HandleExitEvents(self, event) -> None:
		
		#-# Go back if escape button pressed #-#
		if event.type == pygame.QUIT or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
				
			self.PlaySFX(self.goBackSoundPath)

			if self.tab == "menu":

				self.Exit()

			elif self.tab == "settings":

				self.OpenTab("menu")

			elif self.tab == "display settings":

				self.OpenTab("settings")

			elif self.tab == "audio settings":

				self.SetMusicVolume(self.oldMusicVolume)
				self.SetSFXVolume(self.oldSFXVolume)
				self.OpenTab("settings")

			elif self.tab == "game settings":

				self.OpenTab("settings")

			elif self.tab == "developer":

				self.OpenTab("menu")

			elif self.tab == "game":

				if self["game"]["info panel"].show:

					self.CloseInfoPanel()

				else:
					
					#region #-# Save everything to database #-#

					if self.database.Connect():

						sqlCode = "UPDATE game SET age_number='"+str(self.buildings.ageNumber)+"', size='"+str(self.tiles.rowCount)+"', money='"+str(self.money)+"'"
						self.database.Execute(sqlCode)
						self.database.Commit()
						self.database.Disconnect()

						if self.database.Connect():
							
							sqlCode = "DELETE FROM buildings"
							self.database.Execute(sqlCode)
							self.database.Commit()
							self.database.Disconnect()

							for building in self.buildings:

								if self.database.Connect():
								
									sqlCode = "INSERT INTO buildings(level, row, column) VALUES("+str(building.level)+", "+str(building.tile.rowNumber)+", "+str(building.tile.columnNumber)+")"
									self.database.Execute(sqlCode)
									self.database.Commit()
									self.database.Disconnect()

								else:
									
									self.Exit()

						else:

							self.Exit()

					#endregion

					self.OpenTab("menu")

	def HandleEvents(self, event) -> None:

		super().HandleEvents(event)

		if self.tab == "menu":
			
			#-# Control click button events with space button #-#
			if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:

				if self[self.tab]["menu"].buttons["START"].status == "Selected":

					self.PlaySFX(self.clickSoundPath)
					self.OpenTab("game")

				elif self[self.tab]["menu"].buttons["SETTINGS"].status == "Selected":

					self.PlaySFX(self.clickSoundPath)
					self.OpenTab("settings")

				elif self[self.tab]["menu"].buttons["DEVELOPER"].status == "Selected":

					self.PlaySFX(self.clickSoundPath)
					self.OpenTab("developer")

				elif self[self.tab]["menu"].buttons["EXIT"].status == "Selected":

					self.PlaySFX(self.clickSoundPath)
					self.Exit()

			#-# Control click button events with mouse #-#
			if self[self.tab]["menu"].buttons["START"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("game")

			elif self[self.tab]["menu"].buttons["SETTINGS"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("settings")

			elif self[self.tab]["menu"].buttons["DEVELOPER"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("developer")

			elif self[self.tab]["menu"].buttons["EXIT"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.goBackSoundPath)
				self.Exit()

		elif self.tab == "settings":

			#-# Control click button events with space button #-#
			if event.type == pygame.KEYUP:

				if event.key == pygame.K_SPACE:

					if self[self.tab]["menu"].buttons["DISPLAY SETTINGS"].status == "Selected":

						self.PlaySFX(self.clickSoundPath)
						self.OpenTab("display settings")

					elif self[self.tab]["menu"].buttons["AUDIO SETTINGS"].status == "Selected":

						self.oldMusicVolume, self.oldSFXVolume = self.musicVolume, self.SFXVolume
						self.PlaySFX(self.clickSoundPath)
						self.OpenTab("audio settings")

					elif self[self.tab]["menu"].buttons["GAME SETTINGS"].status == "Selected":

						self.PlaySFX(self.clickSoundPath)
						self.OpenTab("game settings")

					elif self[self.tab]["menu"].buttons["DELETE DATA"].status == "Selected":

						self.PlaySFX(self.clickSoundPath)
						self.OpenTab("menu")

						self.DeleteData()
						self.GetData()
						self.AddObjects()

					elif self[self.tab]["menu"].buttons["GO BACK"].status == "Selected":

						self.PlaySFX(self.clickSoundPath)
						self.OpenTab("menu")

			#-# Control click button events with mouse #-#
			if self[self.tab]["menu"].buttons["DISPLAY SETTINGS"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("display settings")

			elif self[self.tab]["menu"].buttons["AUDIO SETTINGS"].isMouseClick(event, self.mousePosition):

				self.oldMusicVolume, self.oldSFXVolume = self.musicVolume, self.SFXVolume
				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("audio settings")

			elif self[self.tab]["menu"].buttons["GAME SETTINGS"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("game settings")
				
			elif self[self.tab]["menu"].buttons["GO BACK"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("menu")

		elif self.tab == "display settings":
			
			if self[self.tab]["go back button"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("settings")

		elif self.tab == "audio settings":

			if self[self.tab]["music volume plus button"].isMouseClick(event, self.mousePosition):

				if self.musicVolume != 1.0:

					self.SetMusicVolume(self.musicVolume + 0.1)

			elif self[self.tab]["music volume minus button"].isMouseClick(event, self.mousePosition):

				if self.musicVolume > 0.0:

					self.SetMusicVolume(self.musicVolume - 0.1)

			elif self[self.tab]["SFX volume plus button"].isMouseClick(event, self.mousePosition):

				if self.SFXVolume != 1.0:

					self.SetSFXVolume(self.SFXVolume + 0.1)

			elif self[self.tab]["SFX volume minus button"].isMouseClick(event, self.mousePosition):

				if self.SFXVolume > 0.0:

					self.SetSFXVolume(self.SFXVolume - 0.1)

			elif self[self.tab]["cancel button"].isMouseClick(event, self.mousePosition):

				self.SetMusicVolume(self.oldMusicVolume)
				self.SetSFXVolume(self.oldSFXVolume)
				self.PlaySFX(self.goBackSoundPath)
				self.OpenTab("settings")

			elif self[self.tab]["save button"].isMouseClick(event, self.mousePosition):

				#region #-# Save Audio Settings to database #-#

				if self.database.Connect():

					sqlCode = "UPDATE game SET music_volume='"+str(self.musicVolume)+"', sfx_volume='"+str(self.SFXVolume)+"'"
					self.database.Execute(sqlCode)
					self.database.Commit()
					self.database.Disconnect()

				else:

					self.Exit()
				
				#endregion

				self.PlaySFX(self.goBackSoundPath)
				self.OpenTab("settings")

		elif self.tab == "game settings":

			if self[self.tab]["delete data button"].isMouseClick(event, self.mousePosition):

				self.DeleteData()
				self.GetData()
				self.AddObjects()

				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("menu")

			elif self[self.tab]["go back button"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("settings")

		elif self.tab == "developer":
			
			if self[self.tab]["github"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				webbrowser.open("https://www.github.com/LordCh4os/")

			elif self[self.tab]["linkedin"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				webbrowser.open("https://www.linkedin.com/in/umutcan-ekinci-b5435a108/")

			elif self[self.tab]["instagram"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				webbrowser.open("https://www.instagram.com/umut_ekinci_/")

			elif self[self.tab]["facebook"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				webbrowser.open("https://www.facebook.com/nmuetn/")

			elif self[self.tab]["x"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				webbrowser.open("https://twitter.com/muetnmuetn/")

			elif self[self.tab]["youtube"].isMouseClick(event, self.mousePosition):

				self.PlaySFX(self.clickSoundPath)
				webbrowser.open("https://www.youtube.com/channel/UC1ma8tkbaD-xxJ4tgSxDthg/")
			
			elif self[self.tab]["go back button"].isMouseClick(event, self.mousePosition):
			
				self.PlaySFX(self.clickSoundPath)
				self.OpenTab("menu")

		elif self.tab == "game":

			#-# sell building #-#
			if self["game"]["info panel"].show:

				if self[self.tab]["info panel sell button"].isMouseClick(event, self.mousePosition):
					
					self.buildings.remove(self.infoBuilding)
					self.money += self.infoBuilding.sellPrice
					self.CloseInfoPanel()
					self.PlaySFX(self.goBackSoundPath)
					self.UpdateButtonTexts()
				
				#-# close info panel #-#
				elif self["game"]["info panel close button"].isMouseClick(event, self.mousePosition):

					self.CloseInfoPanel()
					self.PlaySFX(self.goBackSoundPath)
					self.ControlSelectingTile()
			
			else:

				#-# Select tile if mouse over it #-#
				self.ControlSelectingTile()

				#-# On/off info mode with clicking info mode button #-#
				if self[self.tab]["info mode button"].isMouseClick(event, self.mousePosition):

					if self["game"]["info mode button"].status == "On":

						self[self.tab]["info mode button"].SetStatus("Off")

					else:

						self[self.tab]["info mode button"].SetStatus("On")
					
					self.PlaySFX(self.clickSoundPath)

				#-# Open building info if tile is clicked #-#
				if self["game"]["info mode button"].status == "On" and event.type == pygame.MOUSEBUTTONUP:

					for row in self.tiles:

						for tile in row:

							if tile.selected:

								for building in self.buildings:

									if building.tile == tile:

										self.OpenInfoPanel(building)
										self.PlaySFX(self.clickSoundPath)

										break
								break

				#-# expand #-#
				if self[self.tab]["expand button"].isMouseClick(event, self.mousePosition):

					self.Expand()

				#-# Create building if build button clicked #-#
				elif self[self.tab]["build button"].isMouseClick(event, self.mousePosition):

					self.CreateBuilding()

				#-# Go next age #-#
				elif self[self.tab]["next age button"].isMouseClick(event, self.mousePosition):

					self.NextAge()

			if event.type == pygame.KEYUP:

				#-# Create/Move buildings with keys #-#
				if not self["game"]["info panel"].show:

					if event.key == pygame.K_SPACE:
						
						self.CreateBuilding()
					
					elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
					
						self.MoveBuildings("right")
					
					elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
					
						self.MoveBuildings("left")
					
					elif event.key == pygame.K_UP or event.key == pygame.K_w:
					
						self.MoveBuildings("up")
					
					elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
					
						self.MoveBuildings("down")

	#endregion
	
	#region #-# Info panel #-#

	def OpenInfoPanel(self, building: Building) -> None:

		#-# Update Building Info #-#
		self.infoBuilding = building
		self[self.tab]["info panel level text"].UpdateText("Normal", "Level: " + str(building.level))
		self[self.tab]["info panel speed text"].UpdateText("Normal", "Speed: " + str(building.speed) + " $/sec")
		self[self.tab]["info panel cooldown text"].UpdateText("Normal", "Cooldown: " + str(building.cooldown) + " sec")
		self[self.tab]["info panel sell price text"].UpdateText("Normal", "Sell Price: " + str(building.sellPrice))
		self[self.tab]["info panel sell button"].text.UpdateText("Mouse Over", str(building.sellPrice) + "$")
		self[self.tab]["info panel building image"].AddSurface("Normal", GetImage(building.GetImagePath(), (65, 89)))

		self[self.tab]["info panel"].Show()
		self[self.tab]["info panel level text"].Show()
		self[self.tab]["info panel speed text"].Show()
		self[self.tab]["info panel cooldown text"].Show()
		self[self.tab]["info panel sell price text"].Show()
		self[self.tab]["info panel close button"].Show()
		self[self.tab]["info panel sell button"].Show()
		self[self.tab]["info panel building image"].Show()

	def CloseInfoPanel(self) -> None:

		self[self.tab]["info panel"].Hide()
		self[self.tab]["info panel level text"].Hide()
		self[self.tab]["info panel speed text"].Hide()
		self[self.tab]["info panel cooldown text"].Hide()
		self[self.tab]["info panel sell price text"].Hide()
		self[self.tab]["info panel close button"].Hide()
		self[self.tab]["info panel sell button"].Hide()
		self[self.tab]["info panel building image"].Hide()

	#endregion

	#region #-# Building #-#

	def MoveBuildings(self, rotation: str) -> None:

		isBuildingsMoving = False

		for building in self.buildings:
			
			if not building.velocity == Vector2(0, 0):
				isBuildingsMoving = True
				break

		if self["game"]["info mode button"].status == "Off" and not isBuildingsMoving:

			if rotation == "up" or rotation == "down":
                
				for columnNumber in range(self.tiles.columnCount):
					
					buildingCountInThisColumn = 0
					buildingsInThisColumn = []

					for building in self.buildings:
						if building.tile.columnNumber == columnNumber + 1:
							buildingCountInThisColumn += 1
							buildingsInThisColumn.append(building)
			
					if buildingCountInThisColumn > 0:

						if rotation == "up":

							buildingsInThisColumn.sort(key=lambda building: building.tile.rowNumber)
							
							previousBuilding = None
							targetRow = 0
							for building in buildingsInThisColumn:

								if not previousBuilding:
									if not building.tile.rowNumber == targetRow + 1:
										building.SetTargetTile(self.tiles[targetRow][columnNumber])
									previousBuilding = building
									targetRow += 1
								elif previousBuilding.level == building.level and self.maxBuildingLevel > building.level:
									previousBuilding.LevelUp(building)
									previousBuilding = None
								else:
									if not building.tile.rowNumber == targetRow + 1:
										building.SetTargetTile(self.tiles[targetRow][columnNumber])
									previousBuilding = building
									targetRow += 1

						else:

							buildingsInThisColumn.sort(key=lambda building: building.tile.rowNumber, reverse=True)
							
							previousBuilding = None
							targetRow = 0
							for building in buildingsInThisColumn:

								if not previousBuilding:
									if not building.tile.rowNumber == self.tiles.rowCount - targetRow:
										building.SetTargetTile(self.tiles[self.tiles.rowCount - targetRow - 1][columnNumber])
									previousBuilding = building
									targetRow += 1
								elif previousBuilding.level == building.level and self.maxBuildingLevel > building.level:
									previousBuilding.LevelUp(building)
									previousBuilding = None
								else:
									if not building.tile.rowNumber == self.tiles.rowCount - targetRow:
										building.SetTargetTile(self.tiles[self.tiles.rowCount - targetRow - 1][columnNumber])
									previousBuilding = building
									targetRow += 1

			elif rotation == "right" or rotation == "left":

				for rowNumber in range(self.tiles.rowCount):
					
					buildingCountInThisRow = 0
					buildingsInThisRow = []

					for building in self.buildings:
						if building.tile.rowNumber == rowNumber + 1:
							buildingCountInThisRow += 1
							buildingsInThisRow.append(building)
				
					if  buildingCountInThisRow > 0:

						if rotation == "left":

							buildingsInThisRow.sort(key=lambda building: building.tile.columnNumber)

							previousBuilding = None
							targetColumn = 0
							for building in buildingsInThisRow:
								
								if not previousBuilding:
									if not building.tile.columnNumber == targetColumn + 1:
										building.SetTargetTile(self.tiles[rowNumber][targetColumn])
									previousBuilding = building
									targetColumn += 1
								elif previousBuilding.level == building.level and self.maxBuildingLevel > building.level:
									previousBuilding.LevelUp(building)
									previousBuilding = None
								else:
									if not building.tile.columnNumber == targetColumn + 1:
										building.SetTargetTile(self.tiles[rowNumber][targetColumn])
									previousBuilding = building
									targetColumn += 1

						else:

							buildingsInThisRow.sort(key=lambda building: building.tile.columnNumber, reverse=True)

							previousBuilding =  None
							targetColumn = 0
							for building in buildingsInThisRow:

								if not previousBuilding:
									if not building.tile.columnNumber == self.tiles.columnCount - targetColumn:
										building.SetTargetTile(self.tiles[rowNumber][self.tiles.columnCount - targetColumn - 1])
									previousBuilding = building
									targetColumn += 1
								elif previousBuilding.level == building.level and self.maxBuildingLevel > building.level:
									previousBuilding.LevelUp(building)
									previousBuilding = None
								else:
									if not building.tile.columnNumber == self.tiles.columnCount - targetColumn:
										building.SetTargetTile(self.tiles[rowNumber][self.tiles.columnCount - targetColumn - 1])
									previousBuilding = building
									targetColumn += 1

			self.buildings.sort(key=lambda building: building.tile.columnNumber)

	def AddBuilding(self, level, rowNumber, columnNumber) -> None:

		newBuilding = Building(level, self.buildings.ageNumber, self.tiles[rowNumber - 1][columnNumber - 1])
		self.buildings.append(newBuilding)
		self.buildings.sort(key=lambda building: building.tile.columnNumber)

		if len(self.buildings) == self.tiles.rowCount*self.tiles.columnCount and "game" in self and "build button" in self["game"]:

			self["game"]["build button"].text.UpdateText("Mouse Over", "TILES ARE FULL")
			self["game"]["build button"].text.UpdateSize("Mouse Over", 17)
		
	def CreateBuilding(self) -> None:

		#region Control of buildings are moving

		isBuildingsMoving = False

		for building in self.buildings:

			if not building.velocity == Vector2(0, 0):

				isBuildingsMoving = True

				break

		#endregion

		if not isBuildingsMoving and self.money >= self.buildings.GetBuildCost():

			#region Get Empty Tiles

			emptyTiles = []
			
			for rowNumber in range(self.tiles.rowCount):

				for columnNumber in range(self.tiles.columnCount):

					emptyTiles.append((rowNumber + 1, columnNumber + 1))


			for building in self.buildings:
				emptyTiles.remove((building.tile.rowNumber, building.tile.columnNumber))

			#endregion

			if len(emptyTiles) > 0:
				
				rowNumber, columnNumber = choice(emptyTiles)

				self.AddBuilding(1, rowNumber, columnNumber)
				self.money -= self.buildings.GetBuildCost()
				self.PlaySFX(self.clickSoundPath)
				
			else:

				pass # not enough space
	
	def SetAge(self, ageNumber) -> None:
		
		if ageNumber <= self.buildings.maxAgeNumber:

			self.buildings.SetAge(ageNumber)
			self.UpdateButtonTexts()

	def NextAge(self) -> None:

		if self.buildings.ageNumber < self.buildings.maxAgeNumber and self.money >= self.buildings.GetAgeCost():
			
			self.money -= self.buildings.GetAgeCost()
			self.SetAge(self.buildings.ageNumber + 1)
			self.PlaySFX(self.clickSoundPath)

	#endregion

	def OpenTab(self, tab: str) -> None:

		super().OpenTab(tab)

		if self.tab in self:
			
			if "cloud animation" in self[self.tab]:

				self[self.tab]["cloud animation"].CreateClouds()

	def UpdateMoney(self) -> None:

		time = pygame.time.get_ticks()

		for building in self.buildings:
			
			if not building.lastTime: building.lastTime = time
			
			if time - building.lastTime > (building.cooldown)*1000:
				
				self.money += building.cooldown*building.speed
				building.lastTime = pygame.time.get_ticks()

		#-# Money Text #-#
		self[self.tab]["money text"].UpdateText("Normal", str(self.money) + "$")

	def Draw(self) -> None:
		
		if self.tab == "game":

			self.UpdateMoney()

		super().Draw()
