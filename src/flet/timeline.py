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

from typing import Any, ClassVar

import flet as ft
import flet.canvas as cv
from pyoscillate.patches.evolve import Evolution
from pyoscillate.theory.phrase.base import Phrase, PhraseMode
from pyoscillate.theory.progression import ChordChanges

ACCENT = "#00A896"
MUTED = "#A9B8B4"
TEXT = "#F4F7F6"
TILE_BG = "#1D2B28"
NOW_BG = "#16413C"
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
        self.blocks = cv.Canvas(shapes=[], height=self.HEIGHT, expand=True)
        self.playhead = cv.Canvas(
            shapes=[],
            height=self.HEIGHT,
            expand=True,
            on_resize=self._handle_resize,
        )
        self.control = ft.Container(
            content=ft.Stack([self.blocks, self.playhead], height=self.HEIGHT),
            height=self.HEIGHT,
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

    def _handle_resize(self, e: cv.CanvasResizeEvent) -> None:
        self.width = float(e.width)
        self.redraw()
        self.blocks.update()

    # -- drawing -----------------------------------------------------------

    def redraw(self) -> None:
        """Lay the blocks out again if what they show has changed."""
        evolution = self.evolution
        count = self._block_count()
        choices = evolution.rotation(count) or (None,)
        signature = (
            tuple(id(choice) for choice in choices),
            evolution.bars,
            evolution.enabled,
            round(self.width),
        )
        if signature != self._drawn:
            self._drawn = signature
            self.blocks.shapes = self._draw_blocks(choices)
        self.refresh()

    def refresh(self) -> None:
        """Move the playhead to where the clock is in the playing block."""
        shapes: list[cv.Shape] = []
        evolution = self.evolution
        if evolution.ticking:
            x = evolution.progress * self._block_width
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

    def _draw_blocks(self, choices: tuple[Any, ...]) -> list[cv.Shape]:
        count = len(choices)
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

    def _draw_phrase(self, phrase: Phrase, left: float, *, now: bool) -> list[cv.Shape]:
        """One dot per sounding step, the phrase repeating to fill the bars;
        a pitched phrase's dots sit higher for higher offsets."""
        bars = self.evolution.bars
        cycle_bars = phrase.cycle / phrase.division
        top, bottom = self.BODY_TOP + 6, self.BODY_BOTTOM - 6
        offsets = [step.offset for step in phrase.steps]
        low, high = (min(offsets), max(offsets)) if offsets else (0, 0)
        pitched = phrase.mode is not PhraseMode.NONE and high > low
        paint = ft.Paint(color=ACCENT if now else MUTED)
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
                    cv.Circle(left + at / bars * self._block_width, y, radius, paint)
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
        bars = self.evolution.bars
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
