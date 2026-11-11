"""The cash amount as an odometer: only the digits that change roll.

This draws the text one character at a time and rolls the characters that changed. Money up: the
new digit comes in from the bottom and the old one leaves at the top. Money down: the other way
round. Separators and the currency sign never roll. A change during a roll retargets to the
newest text (nothing is queued): a digit that is already rolling toward the right character keeps
going, the others start from the character they were heading for.

Characters are matched from the right, so a number that gains or loses a digit rolls that digit
in or out at its left end; a separator that goes away stays (still) until the digits next to it
have rolled out. The cell of a rolling character grows or shrinks smoothly between the old and
the new glyph, so its neighbors don't jump. Every digit is clipped to its own cell and to the
plate, and a text too wide for the room (the coin takes the left part) is scaled down to fit.
Time is passed in (milliseconds), so the logic needs no real waiting.
"""

from dataclasses import dataclass

import pygame


@dataclass
class _Slot:
    from_char: str  # what was there ("" for a character that is new)
    to_char: str  # what is there now ("" for a character that is leaving)
    started_ms: int
    direction: int  # 1: money up, -1: money down, 0: nothing changes
    rolls: (
        bool  # whether the change rolls (digits) or just waits and swaps (separators)
    )


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


class Odometer:
    def __init__(self, duration_ms: int) -> None:
        assert duration_ms > 0, "the roll must take some time"
        self.duration_ms = duration_ms
        self._area: pygame.Rect | None = None  # where the text goes: right, top, height
        self._font: pygame.font.Font | None = None
        self._color = (255, 255, 255)
        self._bounds = pygame.Rect(0, 0, 0, 0)
        self._left_limit = 0
        self._slots: list[_Slot] = []  # rightmost first
        self._glyphs: dict[tuple[str, int], pygame.Surface] = {}
        self._fit = 1.0

    def bind(
        self,
        area: pygame.Rect,
        font: pygame.font.Font,
        color,
        bounds: pygame.Rect,
        left_limit: int,
    ) -> None:
        """Draws text right-aligned to `area.right`, one line of `area.height` from
        `area.top`, in `font` and `color`, clipped to `bounds` and never left of `left_limit`
        (a longer text is scaled down). Call again when the widgets are rebuilt."""
        self._area = area.copy()
        self._font = font
        self._color = tuple(color)
        self._bounds = bounds.copy()
        self._left_limit = left_limit
        self._glyphs.clear()

    @property
    def text(self) -> str:
        """The text the odometer is heading for (what it shows once nothing rolls)."""
        return "".join(s.to_char for s in reversed(self._slots))

    def snap(self, text: str) -> None:
        """Shows `text` at once, with no roll (a new session, a language change)."""
        self._slots = [_Slot(c, c, 0, 0, False) for c in reversed(text)]

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
            # The new character starts from the one the slot was heading for. A slot that
            # was leaving was heading for nothing: its glyph is still on its way out, so a
            # different character starts from that glyph, and the same one rolls back in.
            from_char = "" if previous is None else previous.to_char
            if (
                previous is not None
                and not previous.to_char
                and previous.from_char != char
            ):
                from_char = previous.from_char
            slots.append(
                _Slot(
                    from_char,
                    char,
                    now_ms,
                    direction,
                    char.isdigit() or from_char.isdigit(),
                )
            )
        for previous in old[len(text) :]:  # characters that leave at the left
            if not previous.to_char:
                slots.append(previous)  # already leaving: let it finish
            else:
                slots.append(
                    _Slot(
                        previous.to_char,
                        "",
                        now_ms,
                        direction,
                        previous.to_char.isdigit(),
                    )
                )
        self._slots = slots

    def is_rolling(self, now_ms: int) -> bool:
        return any(self._progress(s, now_ms) < 1 for s in self._slots)

    def _progress(self, slot: _Slot, now_ms: int) -> float:
        if slot.direction == 0:
            return 1.0
        return min(1.0, max(0.0, (now_ms - slot.started_ms) / self.duration_ms))

    def _glyph(self, char: str) -> pygame.Surface:
        """The glyph of `char`, scaled by the current fit."""
        assert self._font is not None, "bind() first"
        key = (char, round(self._fit * 1000))
        if key not in self._glyphs:
            glyph = self._font.render(char, True, self._color)
            if self._fit < 1 and glyph.get_width() > 0:
                size = (
                    max(1, round(glyph.get_width() * self._fit)),
                    max(1, round(glyph.get_height() * self._fit)),
                )
                glyph = pygame.transform.smoothscale(glyph, size)
            self._glyphs[key] = glyph
        return self._glyphs[key]

    def _natural_width(self, char: str) -> int:
        assert self._font is not None, "bind() first"
        return self._font.size(char)[0] if char else 0

    def _fit_for(self) -> float:
        """How much to scale the text down so it fits between the left limit and the right
        edge, whatever its characters are rolling to or from."""
        assert self._area is not None, "bind() first"
        total = sum(
            max(self._natural_width(s.from_char), self._natural_width(s.to_char))
            for s in self._slots
        )
        room = self._area.right - self._left_limit
        return 1.0 if total <= room or total == 0 else room / total

    def draw(self, surface: pygame.Surface, now_ms: int) -> None:
        assert self._area is not None, "bind() first"
        # Characters that finished leaving are gone.
        self._slots = [
            s for s in self._slots if s.to_char or self._progress(s, now_ms) < 1
        ]
        self._fit = self._fit_for()
        area = self._area
        limit = self._bounds.clip(
            pygame.Rect(
                self._left_limit, self._bounds.top, area.right, self._bounds.height
            )
        )
        x = area.right
        previous_clip = surface.get_clip()
        for slot in self._slots:
            t = _ease_out(self._progress(slot, now_ms))
            width = round(
                (
                    self._natural_width(slot.from_char) * (1 - t)
                    + self._natural_width(slot.to_char) * t
                )
                * self._fit
            )
            x -= width
            cell = pygame.Rect(x, area.top, width, area.height)
            surface.set_clip(cell.clip(limit))
            self._draw_slot(surface, slot, cell, t)
        surface.set_clip(previous_clip)

    def _draw_slot(
        self, surface: pygame.Surface, slot: _Slot, cell: pygame.Rect, t: float
    ) -> None:
        if t >= 1:
            self._blit(surface, slot.to_char, cell, 0)
        elif not slot.rolls:
            # A separator waits where it was until the digits next to it are done.
            self._blit(
                surface, slot.from_char if not slot.to_char else slot.to_char, cell, 0
            )
        else:
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
        surface.blit(
            glyph,
            (
                cell.centerx - glyph.get_width() // 2,
                cell.top + (cell.height - glyph.get_height()) // 2 + dy,
            ),
        )
