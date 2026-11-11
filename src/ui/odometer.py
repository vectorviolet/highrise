"""The cash amount as an odometer: only the digits that change roll.

The cash display's `money_text` widget keeps the real text and the layout (its right edge and
height); this draws that text one character at a time, over it, and rolls the characters that
changed. Money up: the new digit comes in from the bottom and the old one leaves at the top.
Money down: the other way round. Separators and the currency sign never roll. A change during a
roll retargets to the newest text (nothing is queued): a digit that is already rolling toward the
right character keeps going, the others start from the character they were heading for.

Characters are matched from the right, so a number that gains or loses a digit rolls that digit
in or out at its left end. Every digit is clipped to its own cell (the text's line) and to the
plate. Time is passed in (milliseconds), so the logic needs no real waiting.
"""

from dataclasses import dataclass

import pygame


@dataclass
class _Slot:
    from_char: str  # what was there ("" for a digit that is new)
    to_char: str  # what is there now ("" for a digit that is leaving)
    started_ms: int
    direction: int  # 1: money up, -1: money down, 0: no roll


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


class Odometer:
    def __init__(self, duration_ms: int) -> None:
        assert duration_ms > 0, "the roll must take some time"
        self.duration_ms = duration_ms
        self._widget = None
        self._bounds: pygame.Rect | None = None
        self._slots: list[_Slot] = []  # rightmost first
        self._glyphs: dict[tuple[int, tuple, str], pygame.Surface] = {}

    def bind(self, widget, bounds: pygame.Rect) -> None:
        """Draws `widget`'s text (its font, color, right edge, top and height), clipped to
        `bounds`. Call again when the widgets are rebuilt."""
        self._widget = widget
        self._bounds = bounds
        self._glyphs.clear()

    @property
    def text(self) -> str:
        """The text the odometer is heading for (what it shows once nothing rolls)."""
        return "".join(s.to_char for s in reversed(self._slots))

    def snap(self, text: str) -> None:
        """Shows `text` at once, with no roll (a new session, a language change)."""
        self._slots = [_Slot(c, c, 0, 0) for c in reversed(text)]

    def set_target(self, text: str, direction: int, now_ms: int) -> None:
        """Heads for `text`: the digits that differ roll in `direction` (1 money up, -1 down)."""
        assert direction in (1, -1), "a roll goes up or down"
        old = self._slots
        slots = []
        for i, char in enumerate(reversed(text)):
            previous = old[i] if i < len(old) else None
            if previous is not None and previous.to_char == char:
                slots.append(previous)  # unchanged; keeps rolling if it already was
                continue
            from_char = previous.to_char if previous is not None else ""
            rolls = char.isdigit() or from_char.isdigit()
            slots.append(_Slot(from_char, char, now_ms, direction if rolls else 0))
        for previous in old[len(text) :]:  # a digit that leaves at the left
            if previous.to_char.isdigit():
                slots.append(_Slot(previous.to_char, "", now_ms, direction))
        self._slots = slots

    def is_rolling(self, now_ms: int) -> bool:
        return any(self._progress(s, now_ms) < 1 for s in self._slots)

    def _progress(self, slot: _Slot, now_ms: int) -> float:
        if slot.direction == 0:
            return 1.0
        return min(1.0, max(0.0, (now_ms - slot.started_ms) / self.duration_ms))

    def _glyph(self, char: str) -> pygame.Surface:
        assert self._widget is not None
        key = (id(self._widget.font), tuple(self._widget.color), char)
        if key not in self._glyphs:
            self._glyphs[key] = self._widget.font.render(char, True, self._widget.color)
        return self._glyphs[key]

    def draw(self, surface: pygame.Surface, now_ms: int) -> None:
        assert self._widget is not None and self._bounds is not None, "bind() first"
        # Leaving digits that finished rolling out are gone.
        self._slots = [
            s for s in self._slots if s.to_char or self._progress(s, now_ms) < 1
        ]
        rect = self._widget.rect
        x = rect.right
        previous_clip = surface.get_clip()
        for slot in self._slots:
            width = self._glyph(slot.to_char or slot.from_char).get_width()
            x -= width
            cell = pygame.Rect(x, rect.top, width, rect.height)
            surface.set_clip(cell.clip(self._bounds))
            self._draw_slot(surface, slot, cell, now_ms)
        surface.set_clip(previous_clip)

    def _draw_slot(
        self, surface: pygame.Surface, slot: _Slot, cell: pygame.Rect, now_ms: int
    ) -> None:
        t = _ease_out(self._progress(slot, now_ms))
        if t >= 1:
            self._blit(surface, slot.to_char, cell, 0)
            return
        # Up: the old digit leaves at the top, the new one comes from the bottom.
        shift = slot.direction * cell.height
        self._blit(surface, slot.from_char, cell, -round(t * shift))
        self._blit(surface, slot.to_char, cell, round((1 - t) * shift))

    def _blit(
        self, surface: pygame.Surface, char: str, cell: pygame.Rect, dy: int
    ) -> None:
        if not char:
            return
        glyph = self._glyph(char)
        surface.blit(glyph, (cell.centerx - glyph.get_width() // 2, cell.top + dy))
