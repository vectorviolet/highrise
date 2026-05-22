"""Keyboard-navigable menu controller.

Takes a list of button objects (each must expose `rect`, `state`,
`is_mouse_over`, `set_base_state`) and adds: focus shift on hover,
arrow-key / mouse cycling between buttons, and switch-up/down sounds.

Decouples menu *behaviour* from menu *layout* — the buttons themselves
are declared in YAML as regular image objects with child text objects.
"""
import pygame


class MenuController:
    HOVER_SHIFT_Y = -10

    def __init__(self, buttons: list, audio, switch_up_path, switch_down_path) -> None:
        self.buttons = buttons
        self.audio = audio
        self.switch_up_path = switch_up_path
        self.switch_down_path = switch_down_path
        if self.buttons:
            self._focus(self.buttons[0])

    def _focus(self, button) -> None:
        x, y = button.rect.topleft
        button.rect.set_position((x, y + self.HOVER_SHIFT_Y))
        button.set_base_state("hover")

    def _unfocus(self, button) -> None:
        x, y = button.rect.topleft
        button.rect.set_position((x, y - self.HOVER_SHIFT_Y))
        button.set_base_state("default")

    def _swap_focus(self, from_i: int, to_i: int, sound_path) -> None:
        self.audio.play_sfx(sound_path)
        self._unfocus(self.buttons[from_i])
        self._focus(self.buttons[to_i])

    def _handle_mouse_motion(self, mouse_position) -> None:
        target_i = next((i for i, b in enumerate(self.buttons)
                         if b.is_mouse_over(mouse_position) and b.state != "hover"), None)
        hover_i  = next((i for i, b in enumerate(self.buttons) if b.state == "hover"), None)
        if target_i is None or hover_i is None:
            return
        sound = self.switch_down_path if hover_i > target_i else self.switch_up_path
        self._swap_focus(hover_i, target_i, sound)

    def _handle_key(self, event) -> None:
        if event.key in (pygame.K_w, pygame.K_UP):
            delta, sound = -1, self.switch_up_path
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            delta, sound = 1, self.switch_down_path
        else:
            return
        hover_i = next((i for i, b in enumerate(self.buttons) if b.state == "hover"), None)
        if hover_i is not None and 0 <= hover_i + delta < len(self.buttons):
            self._swap_focus(hover_i, hover_i + delta, sound)

    def handle_event(self, event, mouse_position) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(mouse_position)
        elif event.type == pygame.KEYUP:
            self._handle_key(event)

    @property
    def focused(self):
        return next((b for b in self.buttons if b.state == "hover"), None)