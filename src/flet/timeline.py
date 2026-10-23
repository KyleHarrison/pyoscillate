"""A musical timeline for one `Evolution`: what plays now, what comes next and
where the change lands.

Each block is one interval of the evolution (`bars` bars wide) holding one
choice: a phrase draws its steps as dots, tiled across the bars; a chord
progression draws its chords as spans. The block playing carries a playhead
read off the evolution's clock progress, and a marker under its right edge
says where the evolution moves on. A hold shows the one choice with no
playhead.

Two stacked canvases keep refreshes cheap: the blocks are redrawn only when
the choices, bars or width change, and the playhead on its own canvas every
tick.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any, ClassVar

import flet as ft
import flet.canvas as cv
from pyoscillate.patches.evolve import Evolution
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, Step
from pyoscillate.theory.progression import ChordChanges

ACCENT = "#00A896"
MUTED = "#A9B8B4"
TEXT = "#F4F7F6"
TILE_BG = "#1D2B28"
NOW_BG = "#16413C"
EDIT_BG = "#1C4F48"
GRID = "#31403D"


class EvolveTimeline:
    """Draws one `Evolution` as blocks along a bar ruler. Reads the evolution
    and holds no values of its own beyond what it last drew."""

    FALLBACK_WIDTH = 300
    HEIGHT = 96
    LABEL_Y = 3
    BODY_TOP = 18
    BODY_BOTTOM = 60
    RULER_Y = 64
    MARKER_Y = 80
    BLOCK_GAP = 4
    MAX_BLOCKS = 4
    # the ring and template dot of the edit guide
    RING_RADIUS = 6
    # a playhead that moved less than this many pixels is not repainted
    MIN_MOVE = 1.0
    # the widest a bar's tick label may be crowded: label every Nth bar
    LABEL_STEPS: ClassVar[tuple[int, ...]] = (1, 2, 4, 8, 16, 32)
    MIN_LABEL_SPACING = 20
    # a chord's name, by its root in semitones above the key
    NUMERALS: ClassVar[tuple[str, ...]] = (
        "I",
        "bII",
        "II",
        "bIII",
        "III",
        "IV",
        "#IV",
        "V",
        "bVI",
        "VI",
        "bVII",
        "VII",
    )

    def __init__(self, evolution: Evolution) -> None:
        self.evolution = evolution
        self.width = float(self.FALLBACK_WIDTH)
        self._drawn: tuple[Any, ...] | None = None
        self._block_width = 0.0
        self._span = self.evolution.bars
        self._playhead_x: float | None = None
        self.blocks = cv.Canvas(shapes=[], height=self.HEIGHT, expand=True)
        self.playhead = cv.Canvas(
            shapes=[],
            height=self.HEIGHT,
            expand=True,
            on_resize=self._handle_resize,
        )
        # the dotted guides at the cell a tap would change, on their own canvas
        self.guide = cv.Canvas(shapes=[], height=self.HEIGHT, expand=True)
        self.control = ft.GestureDetector(
            content=ft.Container(
                content=ft.Stack(
                    [self.blocks, self.guide, self.playhead], height=self.HEIGHT
                ),
                height=self.HEIGHT,
            ),
            on_tap_down=self._handle_tap,
            on_hover=self._handle_hover,
            on_exit=self._clear_guide,
        )
        self.redraw()

    # -- layout ------------------------------------------------------------

    def _block_count(self) -> int:
        """How many intervals to lay out: the rotation plus the one that
        wraps, so the loop is visible; one block when holding."""
        evolution = self.evolution
        if evolution.axis is None or not evolution.enabled:
            return 1
        if len(evolution.choices) < 2:
            return 1
        return min(len(evolution.choices) + 1, self.MAX_BLOCKS)

    def _span_of(self, choices: tuple[Any, ...]) -> int:
        """The bars a block spans: the evolution interval, or for a held phrase
        longer than that, the whole phrase so none of it is cut off."""
        bars = self.evolution.bars
        choice = choices[0]
        if len(choices) == 1 and isinstance(choice, Phrase):
            return max(bars, math.ceil(choice.cycle / choice.division))
        return bars

    def _handle_resize(self, e: cv.CanvasResizeEvent) -> None:
        self.width = float(e.width)
        self.redraw()
        self.blocks.update()
        self.playhead.update()

    # -- editing -----------------------------------------------------------

    def _editable(self) -> Phrase | None:
        """The phrase a tap would edit: the playing block's, when its patch
        can take an edit."""
        phrase = self.evolution.current if self.evolution.axis else None
        patch = getattr(self.evolution, "patch", None)
        if hasattr(patch, "edit_phrase") and isinstance(phrase, Phrase):
            return phrase
        return None

    def _dot_y(self, phrase: Phrase, offset: float) -> float:
        """The height a step of `offset` is drawn at, as `_draw_phrase` does."""
        offsets = [step.offset for step in phrase.steps]
        low, high = min(offsets), max(offsets)
        top, bottom = self.BODY_TOP + 6, self.BODY_BOTTOM - 6
        if phrase.mode is PhraseMode.NONE or high <= low:
            return (top + bottom) / 2
        return bottom - (offset - low) / (high - low) * (bottom - top)

    def _target(
        self, phrase: Phrase, x: float, y: float
    ) -> tuple[int, int, float, float]:
        """The step a tap at (x, y) lands on: its place in the cycle, its
        pitch offset, and the block coordinates of its dot."""
        cell = self._block_width / (self._span * phrase.division)
        column = int(x / cell)
        offsets = [step.offset for step in phrase.steps]
        low, high = min(offsets), max(offsets)
        top, bottom = self.BODY_TOP + 6, self.BODY_BOTTOM - 6
        if phrase.mode is PhraseMode.NONE or high <= low:
            return column % phrase.cycle, 0, column * cell, (top + bottom) / 2
        fraction = min(max((bottom - y) / (bottom - top), 0), 1)
        offset = round(low + fraction * (high - low))
        return (
            column % phrase.cycle,
            offset,
            column * cell,
            bottom - (offset - low) / (high - low) * (bottom - top),
        )

    def _handle_tap(self, e: ft.TapEvent) -> None:
        """A tap on the playing block's phrase adds a step where it landed, or
        takes away the step already there (the last one stays). A pitched
        phrase's step takes the pitch the tap's height stands for."""
        phrase = self._editable()
        if phrase is None or e.local_position is None:
            return
        x, y = e.local_position.x, e.local_position.y
        if not 0 <= x < self._edit_width(phrase):
            return
        at, offset, _, _ = self._target(phrase, x, y)
        kept = tuple(step for step in phrase.steps if step.at != at)
        if len(kept) < len(phrase.steps):
            steps = kept or phrase.steps
        else:
            steps = tuple(sorted((*kept, Step(at, offset)), key=Step.position))
        label = phrase.label
        if not label.endswith("(edited)"):
            label += " (edited)"
        self.evolution.patch.edit_phrase(replace(phrase, steps=steps, label=label))
        for canvas in self.redraw():
            canvas.update()

    def _handle_hover(self, e: ft.PointerEvent) -> None:
        """Draw dotted guides through the dot a tap here would place."""
        phrase = self._editable()
        position = e.local_position
        if (
            phrase is None
            or position is None
            or not 0 <= position.x < self._edit_width(phrase)
        ):
            self._clear_guide()
            return
        at, _, x, y = self._target(phrase, position.x, position.y)
        existing = next((step for step in phrase.steps if step.at == at), None)
        if existing is not None:
            # the tap would take this note away: the guides settle on it
            y = self._dot_y(phrase, existing.offset)
        paint = ft.Paint(color=TEXT, stroke_width=1, stroke_dash_pattern=[2, 3])
        self.guide.shapes = [
            cv.Line(x, self.BODY_TOP, x, self.BODY_BOTTOM, paint),
            cv.Line(0, y, self._edit_width(phrase), y, paint),
        ]
        if existing is not None:
            # a ring round the note that would go
            self.guide.shapes.append(
                cv.Circle(
                    x,
                    y,
                    self.RING_RADIUS,
                    ft.Paint(color=TEXT, stroke_width=2, style=ft.PaintingStyle.STROKE),
                )
            )
        else:
            # a template of the note that would appear
            self.guide.shapes.append(
                cv.Circle(
                    x,
                    y,
                    self.RING_RADIUS - 2,
                    ft.Paint(color=ft.Colors.with_opacity(0.55, ACCENT)),
                )
            )
        self.guide.update()

    def _clear_guide(self, e: ft.ControlEvent | None = None) -> None:
        if self.guide.shapes:
            self.guide.shapes = []
            self.guide.update()

    # -- drawing -----------------------------------------------------------

    def redraw(self) -> list[ft.Control]:
        """Lay the blocks out again if what they show has changed; the
        canvases that changed, for the caller to repaint."""
        evolution = self.evolution
        count = self._block_count()
        choices = evolution.rotation(count) or (None,)
        signature = (
            tuple(id(choice) for choice in choices),
            evolution.bars,
            evolution.enabled,
            round(self.width),
            self._span_of(choices),
        )
        changed: list[ft.Control] = []
        if signature != self._drawn:
            self._drawn = signature
            self.blocks.shapes = self._draw_blocks(choices)
            changed.append(self.blocks)
            # the block width may have changed under the playhead
            self._playhead_x = None
        return changed + self.refresh()

    def refresh(self) -> list[ft.Control]:
        """Move the playhead to where the clock is in the playing block; the
        playhead's canvas if it moved by at least a pixel (or appeared or
        went), for the caller to repaint."""
        evolution = self.evolution
        x = None
        if evolution.ticking:
            progress = (
                evolution.progress
                if self._span == evolution.bars
                else evolution.progress_over(self._span)
            )
            x = progress * self._block_width
        if x is None or self._playhead_x is None:
            if x == self._playhead_x:
                return []
        elif abs(x - self._playhead_x) < self.MIN_MOVE:
            return []
        self._playhead_x = x
        shapes: list[cv.Shape] = []
        if x is not None:
            shapes.append(
                cv.Line(
                    x,
                    self.BODY_TOP - 2,
                    x,
                    self.RULER_Y,
                    paint=ft.Paint(color=TEXT, stroke_width=2),
                )
            )
        self.playhead.shapes = shapes
        return [self.playhead]

    def _draw_blocks(self, choices: tuple[Any, ...]) -> list[cv.Shape]:
        count = len(choices)
        self._span = self._span_of(choices)
        gaps = self.BLOCK_GAP * (count - 1)
        self._block_width = (self.width - gaps) / count
        shapes: list[cv.Shape] = []
        for index, choice in enumerate(choices):
            left = index * (self._block_width + self.BLOCK_GAP)
            shapes += self._draw_block(choice, left, now=index == 0)
        if self.evolution.enabled:
            shapes += self._draw_marker(self._block_width)
        return shapes

    def _draw_block(self, choice: Any, left: float, *, now: bool) -> list[cv.Shape]:
        width = self._block_width
        label = choice.label if choice is not None else self.evolution.label
        top, bottom = self.BODY_TOP, self.BODY_BOTTOM
        shapes: list[cv.Shape] = [
            cv.Rect(
                left,
                top,
                width,
                bottom - top,
                border_radius=4,
                paint=ft.Paint(color=NOW_BG if now else TILE_BG),
            ),
            *self._draw_pattern_section(choice, left, now=now),
            cv.Rect(
                left,
                top,
                width,
                bottom - top,
                border_radius=4,
                paint=ft.Paint(
                    color=ACCENT if now else GRID,
                    stroke_width=1.5 if now else 1,
                    style=ft.PaintingStyle.STROKE,
                ),
            ),
            cv.Text(
                left + 2,
                self.LABEL_Y,
                label,
                style=ft.TextStyle(
                    size=10,
                    color=TEXT if now else MUTED,
                    weight=ft.FontWeight.BOLD if now else None,
                ),
                max_width=width - 4,
                max_lines=1,
                ellipsis="…",
            ),
        ]
        if isinstance(choice, Phrase):
            shapes += self._draw_phrase(choice, left, now=now)
        elif isinstance(choice, ChordChanges):
            shapes += self._draw_chords(choice, left, now=now)
        shapes += self._draw_ruler(left)
        return shapes

    def _edit_width(self, phrase: Phrase) -> float:
        """How wide the editable pattern is at the start of the block: one
        cycle, or all of it when the cycle fills the bars."""
        return min(phrase.cycle / phrase.division / self._span, 1) * self._block_width

    def _draw_pattern_section(
        self, choice: Any, left: float, *, now: bool
    ) -> list[cv.Shape]:
        """The one cycle the listener edits, picked out at the block's start;
        what follows is the same cycle repeating."""
        if not (now and isinstance(choice, Phrase) and self._editable()):
            return []
        top, bottom = self.BODY_TOP, self.BODY_BOTTOM
        width = self._edit_width(choice)
        return [
            cv.Rect(
                left,
                top,
                width,
                bottom - top,
                border_radius=4,
                paint=ft.Paint(color=EDIT_BG),
            ),
            cv.Rect(
                left,
                top,
                width,
                bottom - top,
                border_radius=4,
                paint=ft.Paint(
                    color=ACCENT, stroke_width=2, style=ft.PaintingStyle.STROKE
                ),
            ),
        ]

    def _draw_phrase(self, phrase: Phrase, left: float, *, now: bool) -> list[cv.Shape]:
        """One dot per sounding step, the phrase repeating to fill the bars;
        a pitched phrase's dots sit higher for higher offsets."""
        bars = self._span
        cycle_bars = phrase.cycle / phrase.division
        top, bottom = self.BODY_TOP + 6, self.BODY_BOTTOM - 6
        offsets = [step.offset for step in phrase.steps]
        low, high = (min(offsets), max(offsets)) if offsets else (0, 0)
        pitched = phrase.mode is not PhraseMode.NONE and high > low
        paint = ft.Paint(color=ACCENT if now else MUTED)
        # the cycles after the first only repeat it
        echo = ft.Paint(color=ft.Colors.with_opacity(0.4, ACCENT if now else MUTED))
        shapes: list[cv.Shape] = []
        repeat = 0.0
        while repeat < bars:
            for step in phrase.steps:
                at = repeat + step.at / phrase.division
                if at >= bars:
                    continue
                if pitched:
                    y = bottom - (step.offset - low) / (high - low) * (bottom - top)
                else:
                    y = (top + bottom) / 2
                radius = 1.5 + 1.5 * min(step.accent, 1.0)
                shapes.append(
                    cv.Circle(
                        left + at / bars * self._block_width,
                        y,
                        radius,
                        paint if repeat == 0 else echo,
                    )
                )
            repeat += cycle_bars
        return shapes

    def _draw_chords(
        self, changes: ChordChanges, left: float, *, now: bool
    ) -> list[cv.Shape]:
        """One span per chord, the progression repeating to fill the bars,
        named by numeral and sitting higher the higher its root."""
        bars = self.evolution.bars
        top, bottom = self.BODY_TOP + 4, self.BODY_BOTTOM - 4
        span = bottom - top
        shapes: list[cv.Shape] = []
        bar = 0
        while bar < bars:
            root = changes.chord_root(bar)
            length = min(
                changes.bars_per_chord - bar % changes.bars_per_chord, bars - bar
            )
            x = left + bar / bars * self._block_width
            width = length / bars * self._block_width
            y = bottom - 8 - root / 11 * (span - 8)
            shapes.append(
                cv.Rect(
                    x + 1,
                    y,
                    max(width - 2, 1),
                    8,
                    border_radius=2,
                    paint=ft.Paint(color=ACCENT if now else MUTED),
                )
            )
            if width >= 22:
                shapes.append(
                    cv.Text(
                        x + 3,
                        y - 11,
                        self.NUMERALS[root % 12],
                        style=ft.TextStyle(size=9, color=TEXT if now else MUTED),
                    )
                )
            bar += length
        return shapes

    def _draw_ruler(self, left: float) -> list[cv.Shape]:
        """A tick per bar under the block, numbered every few bars so the
        labels never crowd."""
        bars = self._span
        per_bar = self._block_width / bars
        label_every = next(
            (n for n in self.LABEL_STEPS if per_bar * n >= self.MIN_LABEL_SPACING),
            self.LABEL_STEPS[-1],
        )
        paint = ft.Paint(color=GRID, stroke_width=1)
        shapes: list[cv.Shape] = []
        for bar in range(bars):
            x = left + bar * per_bar
            major = bar % label_every == 0
            shapes.append(
                cv.Line(x, self.RULER_Y, x, self.RULER_Y + (5 if major else 3), paint)
            )
            if major:
                shapes.append(
                    cv.Text(
                        x + 1,
                        self.RULER_Y + 5,
                        str(bar + 1),
                        style=ft.TextStyle(size=9, color=MUTED),
                    )
                )
        return shapes

    def _draw_marker(self, edge: float) -> list[cv.Shape]:
        """An arrow under the playing block's right edge: evolve here."""
        paint = ft.Paint(color=ACCENT, stroke_width=1.5)
        return [
            cv.Line(edge, self.BODY_BOTTOM + 2, edge, self.MARKER_Y - 2, paint),
            cv.Text(
                edge - 4,
                self.MARKER_Y - 1,
                "▲ evolve here",
                style=ft.TextStyle(size=10, color=ACCENT),
                alignment=ft.Alignment(1, -1),
            ),
        ]
