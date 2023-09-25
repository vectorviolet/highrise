#-# Import Packages #-#
import pygame
from images import *
from scripts.default.button import *
from scripts.default.application import Application

#-# Menu Class #-#
class Menu(pygame.Surface):

    def __init__(
            self,

            titleImagePath: FilePath,
            titleText: str,
            titleTextSize: int,
            titleTextColor: tuple,
            titleFontPath: FontPath,
            panelImagePath: FilePath,

            buttonSize: tuple,
            buttonColor: tuple,
            buttonSelectedColor,
            buttonTexts: tuple,
            buttonTextSize: int,
            buttonTextColor: tuple,
            buttonSelectedTextColor: tuple,
            buttonTextFontPath: str,

            screenSize: tuple,
            panelHeight: tuple = None,
            SFXVolume: int = 100

            ) -> None:
        
        self.SFXVolume = SFXVolume
        space = 20 # space between objects
        buttonAdditionalSize = 15
        self.buttonCount = len(buttonTexts)
        
        self.titleSize = buttonSize[0] + space * 2, 70
        self.panelSize = buttonSize[0] + space * 2, buttonSize[1]*self.buttonCount + (self.buttonCount + 3)*space
        
        if panelHeight:
            
            self.panelSize = self.panelSize[0], panelHeight

        self.size = self.titleSize[0], self.titleSize[1] + self.panelSize[1] - space/2

        self.position = (screenSize[0] - self.size[0]) / 2, (screenSize[1] - self.size[1]) / 2
        self.panelPosition = self.position[0], self.position[1] + self.titleSize[1] - space/2

        #-# Sound Paths #-#
        self.switchUpSoundPath = SoundPath("switchUp")
        self.switchDownSoundPath = SoundPath("switchDown")

        #-# Title #-#
        self.title = Button(self.position, self.titleSize, {"Normal" : titleImagePath}, titleText, "", titleTextSize, titleTextColor, White, titleFontPath)

        #-# Panel #-#
        self.panel = Object(self.panelPosition, self.panelSize, {"Normal" : panelImagePath})
        
        #-# Buttons #-#
        self.buttons = {}

        if self.buttonCount:

            buttonSelectedSize = buttonSize[0], buttonSize[1] + buttonAdditionalSize
            
            
            for i in range(self.buttonCount):

                buttonPosition = pygame.math.Vector2(space, space*(i+3/2) + buttonSize[1]*i)
                buttonScreenPosition = buttonPosition + self.panelPosition
                
                self.buttons[buttonTexts[i]] = MenuButton(buttonColor, buttonScreenPosition, buttonSelectedColor, buttonTexts[i], buttonTexts[i], buttonTextColor, buttonSelectedTextColor
                                    , buttonTextSize, buttonTextFontPath, buttonSize, buttonSelectedSize)


            list(self.buttons.values())[0].SetStatus("Selected")

        super().__init__(self.size, pygame.SRCALPHA)

    def HandleEvents(self, event, mousePosition) -> None:

        #-# Change the color of buttons if mouse over it #-#
        if event.type == pygame.MOUSEMOTION:

            for i, button in enumerate(self.buttons.values()):

                if button.isMouseOver(mousePosition) and button.status != "Selected":

                    for j, button2 in enumerate(self.buttons.values()):

                        if button2.status == "Selected":
                            
                            if j > i:

                                Application.PlaySound(1, self.switchDownSoundPath, self.SFXVolume)

                            else:

                                Application.PlaySound(1, self.switchUpSoundPath, self.SFXVolume)

                            button.SetStatus("Selected")
                            button2.SetStatus("Unselected")

                            break

        #-# Change the selected button with keys #-#
        elif event.type == pygame.KEYUP:
  
            if event.key == pygame.K_w or event.key == pygame.K_UP:

                for i, button in enumerate(self.buttons.values()):
                            
                    if button.status == "Selected" and i != 0:
                        
                        Application.PlaySound(self.switchUpSoundPath, self.SFXVolume)

                        self.buttons[list(self.buttons.keys())[i-1]].SetStatus("Selected")
                        button.SetStatus("Unselected")

                        break

            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:

                for i, button in enumerate(self.buttons.values()):
                            
                    if button.status == "Selected" and i != len(self.buttons) - 1:
                        
                        Application.PlaySound(self.switchDownSoundPath, self.SFXVolume)

                        self.buttons[list(self.buttons.keys())[i+1]].SetStatus("Selected")
                        button.SetStatus("Unselected")

                        break

    def Draw(self, surface: pygame.Surface) -> None:

        surface.blit(self, self.position)
        self.title.Draw(surface)
        self.panel.Draw(surface)

        for button in self.buttons.values():

            button.Draw(surface)
      