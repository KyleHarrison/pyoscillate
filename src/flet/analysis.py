"""Compact waveform and spectrum plots for the monitored patch.

Each plot is one `Canvas` holding one `Path`. Frames come from
`pyoscillate.analysis.live.LiveAnalyser` as bounded `(x, y)` points in its
`WIDTH` x `HEIGHT` viewport (y down) and are scaled to the plot's real size.
"""

from __future__ import annotations

import flet as ft
import flet.canvas as cv
from pyoscillate.analysis.live import LiveAnalyser, Points

ACCENT = "#00A896"
MUTED = "#A9B8B4"
TILE_BG = "#1D2B28"
GRID = "#31403D"


class AnalysisPlot:
    """One titled canvas drawing a single polyline."""

    HEIGHT = 90
    FALLBACK_WIDTH = 300
    FREQ_LABELS = ((20, "20"), (100, "100"), (1000, "1k"), (10000, "10k"))

    def __init__(self, title: str, *, log_freq_axis: bool = False) -> None:
        self.log_freq_axis = log_freq_axis
        self.width = float(self.FALLBACK_WIDTH)
        self.canvas = cv.Canvas(
            shapes=[],
            height=self.HEIGHT,
            expand=True,
            on_resize=self._handle_resize,
        )
        self.title = ft.Text(title, size=11, color=MUTED)
        self.control = ft.Container(
            content=ft.Column([self.title, self.canvas], spacing=2),
            bgcolor=TILE_BG,
            border_radius=8,
            padding=8,
            col={"xs": 12, "md": 6},
        )
        self.draw([])

    def _handle_resize(self, e: cv.CanvasResizeEvent) -> None:
        self.width = float(e.width)

    def draw(self, points: Points) -> None:
        """Show `points`; an empty frame leaves just the idle baseline."""
        scale_x = self.width / LiveAnalyser.WIDTH
        scale_y = self.HEIGHT / LiveAnalyser.HEIGHT
        baseline = self.HEIGHT / 2 if not self.log_freq_axis else self.HEIGHT - 1
        shapes: list[cv.Shape] = [
            cv.Line(
                0,
                baseline,
                self.width,
                baseline,
                paint=ft.Paint(color=GRID, stroke_width=1),
            )
        ]
        if points:
            elements: list[cv.Path.PathElement] = [
                cv.Path.MoveTo(points[0][0] * scale_x, points[0][1] * scale_y)
            ]
            elements += [
                cv.Path.LineTo(x * scale_x, y * scale_y) for x, y in points[1:]
            ]
            shapes.append(
                cv.Path(
                    elements,
                    paint=ft.Paint(
                        color=ACCENT,
                        stroke_width=1.5,
                        style=ft.PaintingStyle.STROKE,
                    ),
                )
            )
        self.canvas.shapes = shapes


class AnalysisView:
    """Waveform and spectrum plots, side by side on wide windows."""

    IDLE_NOTE = "Idle: enable the patch to see its output"
    LIVE_NOTE = "Pre-master output, left channel"

    def __init__(self) -> None:
        self.wave = AnalysisPlot("Waveform (50 ms)")
        self.spectrum = AnalysisPlot(
            "Spectrum (20 Hz - 20 kHz, log)", log_freq_axis=True
        )
        self.note = ft.Text(self.IDLE_NOTE, size=11, color=MUTED)
        self.control = ft.Column(
            [
                ft.ResponsiveRow(
                    [self.wave.control, self.spectrum.control], spacing=8, run_spacing=8
                ),
                self.note,
            ],
            spacing=4,
        )

    def show(self, wave: Points, spectrum: Points, live: bool) -> None:
        self.wave.draw(wave if live else [])
        self.spectrum.draw(spectrum if live else [])
        self.note.value = self.LIVE_NOTE if live else self.IDLE_NOTE
