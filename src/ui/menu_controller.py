"""Keyboard-navigable menu controller.

Takes a list of button objects (StateObject-derived; must expose `_focused`,
`is_mouse_over`) and adds arrow-key / mouse cycling between buttons with
switch-up/down sounds. The focused button renders its hover image (via
StateObject.draw checking _hovered OR _focused).

Decouples menu *behaviour* from menu *layout* — the buttons themselves are
declared in YAML as regular image objects with child text objects.
"""
import pygame


class MenuController:
    def __init__(self, buttons: list, audio, switch_up_path, switch_down_path) -> None:
        self.buttons = buttons
        self.audio = audio
        self.switch_up_path = switch_up_path
        self.switch_down_path = switch_down_path
        if self.buttons:
            self._focus(self.buttons[0])

    def _focus(self, button) -> None:
        button.focused = True

    def _unfocus(self, button) -> None:
        button.focused = False

    def _swap_focus(self, from_i: int, to_i: int, sound_path) -> None:
        self.audio.play_sfx(sound_path)
        self._unfocus(self.buttons[from_i])
        self._focus(self.buttons[to_i])

    def _focused_index(self) -> int | None:
        return next((i for i, b in enumerate(self.buttons) if b.focused), None)

    def _handle_mouse_motion(self, mouse_position) -> None:
        target_i = next((i for i, b in enumerate(self.buttons)
                         if b.is_mouse_over(mouse_position) and not b.focused), None)
        focused_i = self._focused_index()
        if target_i is None or focused_i is None:
            return
        sound = self.switch_down_path if focused_i > target_i else self.switch_up_path
        self._swap_focus(focused_i, target_i, sound)

    def _handle_key(self, event) -> None:
        if event.key in (pygame.K_w, pygame.K_UP):
            delta, sound = -1, self.switch_up_path
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            delta, sound = 1, self.switch_down_path
        else:
            return
        focused_i = self._focused_index()
        if focused_i is not None and 0 <= focused_i + delta < len(self.buttons):
            self._swap_focus(focused_i, focused_i + delta, sound)

    def handle_event(self, event, mouse_position) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(mouse_position)
        elif event.type == pygame.KEYUP:
            self._handle_key(event)

    @property
    def focused(self):
        return next((b for b in self.buttons if b.focused), None)