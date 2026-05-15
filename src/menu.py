import pygame

from sound_manager import SoundManager
from pygame_core.asset_path import SoundPath
from state_object.state_object import StateObject
from state_object.button import Button
from unity.gameobject import GameObject


class Menu(GameObject):
    """Handles navigation input and rendering for a menu screen."""

    HOVER_SHIFT_Y = -10

    def __init__(self, title: Button, panel: StateObject, buttons: dict) -> None:
        super().__init__()

        self.title = title
        self.panel = panel
        self.buttons = buttons

        self.switch_up_sound_path = SoundPath("switchUp")
        self.switch_down_sound_path = SoundPath("switchDown")

        if self.buttons:
            self._focus(next(iter(self.buttons.values())))

    def _focus(self, button: Button) -> None:
        x, y = button.rect.topleft
        button.rect.set_position((x, y + self.HOVER_SHIFT_Y))
        button.set_base_state("hover")

    def _unfocus(self, button: Button) -> None:
        x, y = button.rect.topleft
        button.rect.set_position((x, y - self.HOVER_SHIFT_Y))
        button.set_base_state("default")

    def _swap_focus(self, buttons: list, from_i: int, to_i: int, sound: SoundPath) -> None:
        SoundManager.play_sound(1, sound)
        self._unfocus(buttons[from_i])
        self._focus(buttons[to_i])

    def _handle_mouse_motion(self, buttons: list, mouse_position) -> None:
        target_i = next((i for i, b in enumerate(buttons) if b.is_mouse_over(mouse_position) and b.state != "hover"), None)
        hover_i  = next((i for i, b in enumerate(buttons) if b.state == "hover"), None)
        if target_i is None or hover_i is None:
            return
        sound = self.switch_down_sound_path if hover_i > target_i else self.switch_up_sound_path
        self._swap_focus(buttons, hover_i, target_i, sound)

    def _handle_key(self, buttons: list, event) -> None:
        if event.key in (pygame.K_w, pygame.K_UP):
            delta, sound = -1, self.switch_up_sound_path
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            delta, sound = 1, self.switch_down_sound_path
        else:
            return

        hover_i = next((i for i, b in enumerate(buttons) if b.state == "hover"), None)
        if hover_i is not None and 0 <= hover_i + delta < len(buttons):
            self._swap_focus(buttons, hover_i, hover_i + delta, sound)

    def handle_event(self, event, mouse_position) -> None:
        if not self.active:
            return
        buttons = list(self.buttons.values())

        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(buttons, mouse_position)
        elif event.type == pygame.KEYUP:
            self._handle_key(buttons, event)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        self.title.draw(surface)
        self.panel.draw(surface)

        for button in self.buttons.values():
            button.draw(surface)