"""2048's StateObject — preserves the dict-init / auto-resolve / public-state API
on top of the shared pygame_core.ecs.state_object.HoverableStateObject base.

Aliases the base's `images`/`_hover_images` dicts as `states`/`_hover_states` so
existing Button/ButtonText/GuiObject code keeps working. Overrides handle_event
to auto-resolve from mouse events (default / hover / base_state / mouse_click
suffixes) and draw to blit from the dicts directly — the inherited
SpriteRenderer2D component is unused for this subclass.
"""
import pygame
from pygame_core.image import load_image
from pygame_core.ecs.state_object import HoverableStateObject


class StateObject(HoverableStateObject):
    def __init__(self,
                 position: tuple = ("CENTER", "CENTER"),
                 size: tuple = (0, 0),
                 image_paths: dict | None = None,
                 parent=None,
                 visible: bool = True,
                 nine_slice: int = 0,
                 anchor: str = "top-left"):
        super().__init__(parent=parent, pos=position, size=size,
                         image_path=None, nine_slice=nine_slice, anchor=anchor)

        self.states = self.images                # alias
        self._hover_states = self._hover_images  # alias

        self._base_state: str | None = None
        self._focused: bool = False
        self.visible = visible
        self.state: str | None = None
        self.image_paths = image_paths if image_paths is not None else {}

        has_size = bool(size and size[0] and size[1])
        self.size = size if has_size else (0, 0)
        self.add_images(self.image_paths)

        if not has_size and self.states:
            surface = self.states.get("default") or next(iter(self.states.values()))
            self.size = surface.get_rect().size
        self.width, self.height = self.size

    # ── image registration (forwards to base; preserves old method names) ────

    def add_images(self, image_paths: dict):
        for state, path in image_paths.items():
            if path is None or state is None: continue
            self.add_image(state, path)

    def add_image(self, state, image_path):
        self.add_state(state, image_path)
        if self.state is None and state == "default":
            self.set_base_state("default")

    def add_hover_image(self, state, image_path):
        if image_path is None:
            return
        self._hover_states[state] = load_image(image_path, self._size, self._nine_slice)

    def add_surface(self, state: str | None, surface: pygame.Surface):
        self.states[state] = surface
        if self.state is None and state == "default":
            self.set_base_state("default")

    # ── state machine (auto-resolve from events) ─────────────────────────────

    def set_base_state(self, state: str):
        self._base_state = state
        self.state = state

    def _resolve_state(self, event, mouse_position) -> str | None:
        if "mouse_click" in self.states and self.is_clicked(event, mouse_position):
            return "mouse_click"
        if self._hovered:
            hover_key = f"{self._base_state}_hover" if self._base_state else None
            if hover_key and hover_key in self.states:
                return hover_key
            if "hover" in self.states:
                return "hover"
        if self._base_state and self._base_state in self.states:
            return self._base_state
        if "default" in self.states:
            return "default"
        return self.state

    def handle_event(self, event, mouse_position):
        if not self.active:
            return
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.is_mouse_over(mouse_position)
        self.state = self._resolve_state(event, mouse_position)

    # ── rendering / visibility ───────────────────────────────────────────────

    def draw(self, surface) -> None:
        if not self.active:
            return
        if not (self.visible and self.state in self.states):
            return
        if (self._hovered or self._focused) and self.state in self._hover_states:
            surface.blit(self._hover_states[self.state], self.rect)
        else:
            surface.blit(self.states[self.state], self.rect)

    def on_disable(self):
        self._hovered = False