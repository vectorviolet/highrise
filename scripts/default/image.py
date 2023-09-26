#-# Importing Packages #-#
import pygame
from scripts.default.path import *

#-# Image Function #-#
def GetImage(path: ImagePath, Size=[0, 0], ReturnSize=False):

	if type(Size) == tuple:
		Size = list(Size)

	if Size == [0, 0] and ReturnSize == False:
		return pygame.image.load(path).convert_alpha()
	
	Img = pygame.image.load(path).convert_alpha()
	
	if Size[0] == 0: Size[0] = Img.get_width()
	if Size[1] == 0: Size[1] = Img.get_height()
	if Size[0] == 1/3: Size[0] = Img.get_width()//5
	if Size[1] == 1/3: Size[1] = Img.get_height()//5

	if ReturnSize:
		
		return [pygame.transform.scale(pygame.image.load(path).convert_alpha(), Size), Size]

	return pygame.transform.scale(pygame.image.load(path).convert_alpha(), Size)
