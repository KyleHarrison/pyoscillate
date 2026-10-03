"""Shared Flet <-> Pyo patch plumbing.

This module abstracts the conversion between a `Patch` subclass instance (as
exposed by the modules under `pyoscillate.patches`) and a Flet UI: one patch
per `PatchPanel`, rendering an enable switch, parameter sliders, and a volume
slider. `PatchRackApp` composes any number
of `PatchPanel`s into a single scrollable page with an audio-engine
start/stop control and JSON preset save/load, so the same code drives a
single patch (`patch`) or a whole rack of patches (`deep_house`,
`psyambient`).
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from pyo.lib._core import PyoError
from pyo.lib.server import Server

import flet as ft
from pyoscillate.clock import Clock
from pyoscillate.controller import EvolvingRuntime, GroupControl, GroupRuntime
from pyoscillate.patches.base import BuildContext, Patch, start_server
from pyoscillate.patches.params import Param
from pyoscillate.patches.sweep import Sweep
from pyoscillate.projects.base import Rack
from pyoscillate.tempo import Tempo
from pyoscillate.theory.intervals import Progression
from pyoscillate.theory.notes import NOTE_NAMES

ACCENT = "#00A896"
BACKGROUND = "#101716"
PANEL = "#182220"
TILE_BG = "#1D2B28"
TEXT = "#F4F7F6"
MUTED = "#A9B8B4"
ERROR = "#FF8A80"
# preset entry for rack-wide settings; the leading underscore keeps it from
# colliding with a patch name
RACK_PRESET_KEY = "_rack"

Preset = dict[str, dict[str, Any]]


class PresetStore:
    """Loads/saves `{patch_name: {param: value}}` JSON presets for a rack."""

    def __init__(self, catalog_dir: Path) -> None:
        self.catalog_dir = catalog_dir
        self.catalog_dir.mkdir(parents=True, exist_ok=True)

    def names(self) -> list[str]:
        return sorted(path.stem for path in self.catalog_dir.glob("*.json"))

    def load(self, name: str) -> Preset:
        path = self.catalog_dir / f"{name}.json"
        return json.loads(path.read_text())

    def save(self, name: str, values: Preset) -> Path:
        path = self.catalog_dir / f"{name}.json"
        path.write_text(json.dumps(values, indent=2) + "\n")
        return path


class SweepRow:
    """The sweep view of one `Param`: a toggle that swaps the plain slider for
    a low/high range slider. The space between its two limit thumbs is the
    sweep itself: a dot travels there and back across it as the sweep runs,
    and dragging sideways on the band sets how many bars one there-and-back
    cycle takes. Reads and writes the patch's `Sweep`; holds no values of its
    own."""

    # the range slider's track starts this far in from each edge of its box
    TRACK_INSET = 20.0
    # clear space kept either side of the band so a drag there grabs the
    # thumb, not the cycle length
    THUMB_CLEARANCE = 12.0
    HEIGHT = 40.0
    DOT = 12.0
    # horizontal pixels of drag per bar of cycle length
    DRAG_PER_BAR = 8.0
    # seconds of travel the dot's trail shows: a faster cycle leaves a longer
    # trail, so the rate of change reads straight off the slider
    TRAIL_SECONDS = 0.6
    TRAIL_CLEAR = "#00F4F7F6"

    def __init__(self, sweep: Sweep, plain_slider: ft.Slider) -> None:
        self.sweep = sweep
        self.plain_slider = plain_slider
        self.width = 0.0
        self._last_position = 0.0
        spec = sweep.param.spec
        self.toggle = ft.IconButton(
            icon=ft.Icons.WAVES,
            icon_size=18,
            tooltip="Sweep between a low and a high",
            on_click=self._handle_toggle,
        )
        self.range_text = ft.Text("", color=ACCENT, size=13, weight=ft.FontWeight.BOLD)
        self.range_slider = ft.RangeSlider(
            min=spec.minimum,
            max=spec.maximum,
            divisions=spec.divisions,
            start_value=sweep.low,
            end_value=sweep.high,
            active_color=ACCENT,
            inactive_color="#31403D",
            on_change=self._handle_range,
            left=0,
            right=0,
            top=0,
        )
        self.dot = ft.Container(
            width=self.DOT,
            height=self.DOT,
            border_radius=self.DOT / 2,
            bgcolor=TEXT,
            top=(self.HEIGHT - self.DOT) / 2,
            left=0,
            visible=False,
        )
        self.trail = ft.Container(
            width=0,
            height=self.DOT / 2,
            border_radius=self.DOT / 4,
            top=(self.HEIGHT - self.DOT / 2) / 2,
            left=0,
            visible=False,
        )
        self.bars_text = ft.Text("", color=BACKGROUND, size=11)
        self.band = ft.GestureDetector(
            content=ft.Container(
                content=self.bars_text,
                alignment=ft.Alignment.CENTER,
                tooltip="Drag sideways to change the length of one there-and-back cycle",
            ),
            on_horizontal_drag_update=self._handle_bars_drag,
            top=0,
            height=self.HEIGHT,
            left=0,
            width=0,
            visible=False,
        )
        self.track = ft.Stack(
            controls=[self.range_slider, self.band, self.trail, self.dot],
            height=self.HEIGHT,
            on_size_change=self._handle_size,
        )
        self.sweep_view = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Sweeps between", color=MUTED, size=12),
                        self.range_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                self.track,
            ],
            spacing=2,
        )
        self.show()

    def _x(self, value: float) -> float:
        """Horizontal pixel of `value` along the range slider's track."""
        spec = self.sweep.param.spec
        span = spec.maximum - spec.minimum
        fraction = (value - spec.minimum) / span if span else 0.0
        return self.TRACK_INSET + fraction * (self.width - 2 * self.TRACK_INSET)

    def show(self) -> None:
        """Bring every control in line with the sweep's settings."""
        sweep, spec = self.sweep, self.sweep.param.spec
        self.toggle.selected = sweep.enabled
        self.toggle.icon_color = ACCENT if sweep.enabled else MUTED
        self.plain_slider.visible = not sweep.enabled
        self.sweep_view.visible = sweep.enabled
        self.range_slider.start_value = sweep.low
        self.range_slider.end_value = sweep.high
        self.range_text.value = f"{spec.format(sweep.low)} - {spec.format(sweep.high)}"
        self.bars_text.value = f"{sweep.bars:.0f} bars"
        self._place()

    def _place(self) -> None:
        """Fit the cycle band between the limit thumbs and the dot inside it."""
        sweep = self.sweep
        band_left = self._x(sweep.low) + self.THUMB_CLEARANCE
        band_width = self._x(sweep.high) - self._x(sweep.low) - 2 * self.THUMB_CLEARANCE
        self.band.visible = sweep.enabled and self.width > 0 and band_width > 0
        if self.band.visible:
            self.band.left = band_left
            self.band.width = band_width
        self.refresh()

    def refresh(self) -> None:
        """Move the dot to where the running sweep is between the limits, with
        a trail behind it as long as the distance it covers in
        `TRAIL_SECONDS`."""
        sweep = self.sweep
        shown = sweep.enabled and sweep.running and self.width > 0
        self.dot.visible = self.trail.visible = shown
        if not shown:
            return
        position = sweep.position
        rising = position >= self._last_position
        self._last_position = position
        x = self._x(sweep.value_at(position))
        self.dot.left = x - self.DOT / 2
        span = self._x(sweep.high) - self._x(sweep.low)
        assert sweep.patch.tempo is not None
        seconds = sweep.bars * sweep.patch.tempo.bar
        length = min(span, 2 * span / seconds * self.TRAIL_SECONDS)
        self.trail.width = length
        self.trail.left = x - length if rising else x
        self.trail.gradient = ft.LinearGradient(
            begin=ft.Alignment.CENTER_LEFT,
            end=ft.Alignment.CENTER_RIGHT,
            colors=[self.TRAIL_CLEAR, TEXT] if rising else [TEXT, self.TRAIL_CLEAR],
        )

    def _handle_size(self, e: ft.LayoutSizeChangeEvent) -> None:
        self.width = e.width
        self._place()

    def _handle_toggle(self, e: ft.ControlEvent) -> None:
        self.sweep.set_enabled(not self.sweep.enabled)
        self.show()
        e.page.update()

    def _handle_range(self, e: ft.ControlEvent) -> None:
        self.sweep.configure(
            float(e.control.start_value), float(e.control.end_value), self.sweep.bars
        )
        self.show()
        e.page.update()

    def _handle_bars_drag(self, e: ft.DragUpdateEvent) -> None:
        bars = self.sweep.bars + (e.primary_delta or 0.0) / self.DRAG_PER_BAR
        self.sweep.configure(self.sweep.low, self.sweep.high, bars)
        self.bars_text.value = f"{self.sweep.bars:.0f} bars"
        e.page.update()


class PatchPanel:
    """One patch's live controls: an enable switch plus one slider per
    `Param` (volume included).

    `self.patch`'s own parameter attributes are the only copy of a slider's
    current value - this panel never shadows them in a separate dict. A slider
    move assigns the `Param` on the patch, which live-updates the running Pyo
    graph; `_apply()` only decides whether that move also requires a full
    rebuild (a `rebuild` parameter changed since the last build).
    """

    def __init__(self, patch: Patch) -> None:
        self.patch = patch
        self.enabled = False
        self.context: BuildContext
        self._engine_ready = False
        self._group_enabled = True
        self._built_values: dict[Param, float] = {}
        self._value_texts: dict[Param, ft.Text] = {}
        self._sliders: dict[Param, ft.Slider] = {}
        self._dropdowns: dict[Param, ft.Dropdown] = {}
        self.sweep_rows: dict[Param, SweepRow] = {}

        self.switch = ft.Switch(
            value=False,
            active_color=ACCENT,
            on_change=self._handle_enabled,
            disabled=True,
        )
        self.control = self._build_control()

    # -- UI construction -------------------------------------------------

    def _option_row(self, param: Param) -> ft.Container:
        """A named-choice parameter: a dropdown whose value is the index."""
        spec = param.spec
        dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(key=str(i), text=name)
                for i, name in enumerate(spec.options)
            ],
            value=str(int(param.read(self.patch))),
            on_select=lambda e, param=param: self._handle_option(param, e),
        )
        self._dropdowns[param] = dropdown
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(spec.description, color=TEXT, size=14),
                    ft.Text(spec.help_text, color=MUTED, size=12),
                    dropdown,
                ],
                spacing=2,
            ),
            col={"xs": 12, "md": 6},
            padding=ft.padding.Padding(left=0, top=4, right=0, bottom=4),
        )

    def _slider_row(self, param: Param) -> ft.Container:
        spec = param.spec
        if spec.options:
            return self._option_row(param)
        value = param.read(self.patch)
        value_text = ft.Text(
            spec.format(value), color=ACCENT, size=13, weight=ft.FontWeight.BOLD
        )
        self._value_texts[param] = value_text
        # the track runs in the spec's position space (semitones for a note
        # slider), so its ticks are what the slider can actually produce
        slider = ft.Slider(
            min=spec.to_position(spec.minimum),
            max=spec.to_position(spec.maximum),
            divisions=spec.divisions,
            value=spec.to_position(value),
            active_color=ACCENT,
            inactive_color="#31403D",
            on_change=lambda e, param=param: self._handle_slider(param, e),
        )
        self._sliders[param] = slider
        header = [ft.Text(spec.description, color=TEXT, size=14), value_text]
        body: list[ft.Control] = [slider]
        if param.sweep:
            sweep_row = SweepRow(self.patch.sweep_for(param), slider)
            self.sweep_rows[param] = sweep_row
            header = [
                ft.Text(spec.description, color=TEXT, size=14),
                ft.Row(
                    controls=[value_text, sweep_row.toggle],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ]
            body.append(sweep_row.sweep_view)
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=header,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(spec.help_text, color=MUTED, size=12),
                    *body,
                ],
                spacing=2,
            ),
            col={"xs": 12, "md": 6},
            padding=ft.padding.Padding(left=0, top=4, right=0, bottom=4),
        )

    def _build_control(self) -> ft.Control:
        rows = [self._slider_row(param) for param in self.patch.params]
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        self.patch.title,
                                        color=TEXT,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(self.patch.summary, color=MUTED, size=12),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            self.switch,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.ResponsiveRow(controls=rows, spacing=12, run_spacing=4),
                ],
                spacing=8,
            ),
            bgcolor=TILE_BG,
            border_radius=8,
            padding=12,
        )

    def sync_sliders(self) -> None:
        """Move every slider to its parameter's current value - for values
        changed from outside this panel, e.g. a rack macro."""
        for param in self.patch.params:
            self._show(param, param.read(self.patch))
        for sweep_row in self.sweep_rows.values():
            sweep_row.show()

    def refresh_sweeps(self) -> bool:
        """Move every live sweep marker; whether any sweep is running."""
        running = False
        for sweep_row in self.sweep_rows.values():
            if sweep_row.sweep.running:
                sweep_row.refresh()
                running = True
        return running

    def _show(self, param: Param, value: float) -> None:
        if param in self._dropdowns:
            self._dropdowns[param].value = str(int(value))
            return
        self._sliders[param].value = param.spec.to_position(value)
        self._value_texts[param].value = param.spec.format(value)

    # -- engine lifecycle --------------------------------------------------

    def engine_started(self, context: BuildContext) -> None:
        self.context = context
        self._engine_ready = True
        self.switch.disabled = False

    def engine_stopped(self) -> None:
        self._engine_ready = False
        self.switch.disabled = True
        self.enabled = False
        self.switch.value = False
        self.patch.stop()

    def set_group_enabled(self, enabled: bool) -> None:
        self._group_enabled = enabled
        self.switch.disabled = not self._engine_ready or not enabled
        self._apply()

    # -- event handlers ----------------------------------------------------

    def _handle_enabled(self, e: ft.ControlEvent) -> None:
        self.enabled = bool(e.control.value)
        self._apply()
        e.page.update()

    def _handle_slider(self, param: Param, e: ft.ControlEvent) -> None:
        value = param.spec.from_position(float(e.control.value))
        param.write(self.patch, value)
        self._value_texts[param].value = param.spec.format(value)
        self._apply()
        e.page.update()

    def _handle_option(self, param: Param, e: ft.ControlEvent) -> None:
        param.write(self.patch, float(e.control.value))
        self._apply()
        e.page.update()

    def apply_enabled(self, enabled: bool) -> None:
        """Turn this patch on or off from outside its own switch."""
        self.enabled = enabled
        self.switch.value = enabled
        self._apply()

    def _apply(self) -> None:
        if not (self.enabled and self._engine_ready and self._group_enabled):
            self.patch.stop()
            return

        rebuild = not self.patch.playing or any(
            param.read(self.patch) != self._built_values[param]
            for param in self.patch.rebuild_params
        )
        if rebuild:
            self.patch.build(self.context)
            self.patch.start(self.context.tempo)
            self._built_values = {
                param: param.read(self.patch) for param in self.patch.rebuild_params
            }

    # -- presets -------------------------------------------------------------

    def to_preset(self) -> dict[str, Any]:
        values = {param.name: param.read(self.patch) for param in self.patch.params}
        preset: dict[str, Any] = {"enabled": self.enabled, **values}
        if self.patch.sweeps:
            preset["sweeps"] = {
                param.name: {
                    "enabled": sweep.enabled,
                    "low": sweep.low,
                    "high": sweep.high,
                    "bars": sweep.bars,
                }
                for param, sweep in self.patch.sweeps.items()
            }
        return preset

    def apply_preset(self, data: dict[str, Any]) -> None:
        self.enabled = bool(data.get("enabled", False))
        self.switch.value = self.enabled
        for param in self.patch.params:
            if param.name in data:
                value = param.spec.snap(float(data[param.name]))
                param.write(self.patch, value)
                self._show(param, value)
        for param, sweep in self.patch.sweeps.items():
            saved = data.get("sweeps", {}).get(param.name)
            if saved is not None:
                sweep.configure(
                    float(saved["low"]), float(saved["high"]), float(saved["bars"])
                )
                sweep.set_enabled(bool(saved["enabled"]))
                self.sweep_rows[param].show()
        self._apply()


GROUP_CONTROLLER_BARS_MAX = 64
GROUP_CONTROLLER_REPEAT_MAX = 16


class GroupControlSlider:
    """A group `GroupControl`'s slider and value readout. `on_change` runs
    after a move so the page can refresh every slider the push reached."""

    def __init__(
        self,
        group: GroupRuntime,
        control: GroupControl,
        path: str,
        on_change: Callable[[], None],
    ) -> None:
        self.group = group
        self.control = control
        # where the control sits in the rack, so equal slider names in
        # different groups stay distinct in a preset
        self.path = f"{path}/{control.slider.name}"
        self.on_change = on_change
        spec = control.slider
        self.text = ft.Text(
            spec.format(spec.default), color=ACCENT, size=13, weight=ft.FontWeight.BOLD
        )
        self.slider = ft.Slider(
            min=spec.minimum,
            max=spec.maximum,
            divisions=spec.divisions,
            value=spec.default,
            active_color=ACCENT,
            inactive_color="#31403D",
            on_change=self._handle_change,
        )
        self.control_view = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(spec.description, color=TEXT, size=14),
                            self.text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.slider,
                    ft.Text(spec.help_text, color=MUTED, size=11),
                ],
                spacing=2,
            ),
            col={"xs": 12, "md": 6},
            padding=ft.padding.Padding(left=0, top=4, right=0, bottom=4),
        )

    def show(self) -> None:
        """Move the slider to the amount its group last applied."""
        value = self.group.values[self.control]
        self.slider.value = value
        self.text.value = self.control.slider.format(value)

    def set_value(self, value: float) -> None:
        self.group.apply(self.control, value)
        self.on_change()

    def _handle_change(self, e: ft.ControlEvent) -> None:
        self.set_value(float(e.control.value))
        e.page.update()


class PatchGroup:
    """Titled group control that gates a row of related patch panels and any
    nested `PatchGroup`s, plus the group's own `GroupControl` sliders and (for
    an `EvolvingRuntime`) the live sliders for its own interval/repeat - the
    group-level evolution timer described in `controller.py`, distinct from
    any patch's own parameters. Switching a group off silences everything
    inside it, nested groups included."""

    def __init__(
        self,
        group_def: GroupRuntime,
        panels: list[PatchPanel],
        children: Sequence[PatchGroup] = (),
        *,
        path: str = "",
        on_control_change: Callable[[], None] = lambda: None,
    ) -> None:
        self.group_def = group_def
        self.panels = panels
        self.children = list(children)
        self.path = f"{path}/{group_def.title}" if path else group_def.title
        self.control_sliders = [
            GroupControlSlider(group_def, control, self.path, on_control_change)
            for control in group_def.controls
        ]
        self.enabled = True
        self._parent_enabled = True
        self._engine_ready = False
        # for a group of alternative styles, only the selected panel is shown
        self._alternatives = group_def.alternatives and len(panels) > 1
        self._selected = panels[0] if panels else None
        self._boxes: dict[PatchPanel, ft.Container] = {}
        self.style_dropdown = ft.Dropdown(
            label="Style",
            options=[
                ft.dropdown.Option(key=str(i), text=panel.patch.title)
                for i, panel in enumerate(panels)
            ],
            value="0",
            width=220,
            on_select=self._handle_style,
        )
        self.switch = ft.Switch(
            value=True,
            active_color=ACCENT,
            on_change=self._handle_enabled,
            disabled=True,
        )
        self.control = self._build_control()

    def _controller_row(
        self, label: str, help_text: str, text: ft.Text, slider: ft.Slider
    ) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[ft.Text(label, color=TEXT, size=14), text],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    slider,
                    ft.Text(help_text, color=MUTED, size=11),
                ],
                spacing=2,
            ),
            col={"xs": 12, "md": 6},
            padding=ft.padding.Padding(left=0, top=4, right=0, bottom=4),
        )

    def _evolution_rows(self, group: EvolvingRuntime) -> list[ft.Container]:
        bars_text = ft.Text(
            f"{group.bars}", color=ACCENT, size=13, weight=ft.FontWeight.BOLD
        )
        bars_slider = ft.Slider(
            min=1,
            max=GROUP_CONTROLLER_BARS_MAX,
            divisions=GROUP_CONTROLLER_BARS_MAX - 1,
            value=group.bars,
            active_color=ACCENT,
            inactive_color="#31403D",
            on_change=lambda e: self._handle_bars(group, bars_text, e),
        )
        repeat_text = ft.Text(
            f"{group.repeat}", color=ACCENT, size=13, weight=ft.FontWeight.BOLD
        )
        repeat_slider = ft.Slider(
            min=1,
            max=GROUP_CONTROLLER_REPEAT_MAX,
            divisions=GROUP_CONTROLLER_REPEAT_MAX - 1,
            value=group.repeat,
            active_color=ACCENT,
            inactive_color="#31403D",
            on_change=lambda e: self._handle_repeat(group, repeat_text, e),
        )
        return [
            self._controller_row(
                "Evolve every (bars)",
                "How many bars pass before this group's evolution moves on.",
                bars_text,
                bars_slider,
            ),
            self._controller_row(
                "Repeat",
                "How many times each step repeats before advancing to the next.",
                repeat_text,
                repeat_slider,
            ),
        ]

    def _handle_bars(
        self, group: EvolvingRuntime, text: ft.Text, e: ft.ControlEvent
    ) -> None:
        value = round(float(e.control.value))
        group.set_bars(value)
        text.value = f"{value}"
        e.page.update()

    def _handle_repeat(
        self, group: EvolvingRuntime, text: ft.Text, e: ft.ControlEvent
    ) -> None:
        value = round(float(e.control.value))
        group.set_repeat(value)
        text.value = f"{value}"
        e.page.update()

    def _build_control(self) -> ft.Control:
        controller_rows = [
            *(slider.control_view for slider in self.control_sliders),
            *(
                self._evolution_rows(self.group_def)
                if isinstance(self.group_def, EvolvingRuntime)
                else []
            ),
        ]

        patch_columns = []
        panel_column = (
            12
            if self._alternatives or len(self.panels) == 1 or len(self.panels) > 2
            else 6
        )
        for panel in self.panels:
            box = ft.Container(
                content=panel.control,
                col={"xs": 12, "md": panel_column},
                visible=not self._alternatives or panel is self._selected,
            )
            self._boxes[panel] = box
            patch_columns.append(box)

        return ft.Container(
            content=ft.ExpansionTile(
                title=ft.Text(
                    self.group_def.title, color=TEXT, size=18, weight=ft.FontWeight.BOLD
                ),
                subtitle=ft.Text(self.group_def.summary, color=MUTED, size=12),
                leading=self.switch,
                expanded=False,
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                *(
                                    [
                                        ft.ResponsiveRow(
                                            controls=controller_rows, spacing=16
                                        )
                                    ]
                                    if controller_rows
                                    else []
                                ),
                                *([self.style_dropdown] if self._alternatives else []),
                                ft.ResponsiveRow(
                                    controls=patch_columns,
                                    spacing=12,
                                    run_spacing=12,
                                ),
                                *(child.control for child in self.children),
                            ],
                            spacing=12,
                        ),
                        padding=ft.padding.Padding(left=16, top=8, right=16, bottom=16),
                    )
                ],
            ),
            bgcolor=PANEL,
            border=ft.Border.all(1, "#2A3A36"),
            border_radius=8,
            padding=16,
            margin=ft.margin.Margin(left=0, top=0, right=0, bottom=12),
        )

    def _select(self, panel: PatchPanel) -> None:
        """Show `panel` in place of the selected one, handing the playing
        state over so a running group switches style without a gap."""
        current = self._selected
        if not self._alternatives or current is None or panel is current:
            return
        was_on = current.enabled
        current.apply_enabled(False)
        self._selected = panel
        for each, box in self._boxes.items():
            box.visible = each is panel
        self.style_dropdown.value = str(self.panels.index(panel))
        panel.apply_enabled(was_on)

    def _handle_style(self, e: ft.ControlEvent) -> None:
        self._select(self.panels[int(e.control.value)])
        e.page.update()

    def reveal_enabled(self) -> None:
        """After values were loaded from outside, show the style that is on."""
        if self._alternatives:
            on = next((p for p in self.panels if p.enabled), None)
            if on is not None:
                self._select_shown(on)

    def _select_shown(self, panel: PatchPanel) -> None:
        self._selected = panel
        for each, box in self._boxes.items():
            box.visible = each is panel
        self.style_dropdown.value = str(self.panels.index(panel))

    def walk(self) -> list[PatchGroup]:
        """This group then every group nested inside it, depth-first."""
        return [self, *(nested for child in self.children for nested in child.walk())]

    def set_engine_ready(self, ready: bool) -> None:
        self._engine_ready = ready
        self._propagate()

    def set_parent_enabled(self, enabled: bool) -> None:
        self._parent_enabled = enabled
        self._propagate()

    def _propagate(self) -> None:
        self.switch.disabled = not self._engine_ready or not self._parent_enabled
        active = self.enabled and self._parent_enabled
        for panel in self.panels:
            panel.set_group_enabled(active)
        for child in self.children:
            child.set_engine_ready(self._engine_ready)
            child.set_parent_enabled(active)

    def _handle_enabled(self, e: ft.ControlEvent) -> None:
        self.enabled = bool(e.control.value)
        self._propagate()
        e.page.update()


class PatchRackApp:
    """A scrollable page of `PatchPanel`s for one `Rack`, sharing one Pyo
    `Server`, one clock, and one JSON preset catalog - the generic shape
    behind both the single-patch `patch` app and the multi-patch rack
    apps."""

    def __init__(
        self,
        page: ft.Page,
        title: str,
        subtitle: str,
        rack: Rack,
        catalog_dir: Path,
        variants: dict[str, Callable[[], tuple[Rack, Path]]] | None = None,
        variant: str | None = None,
    ) -> None:
        self.page = page
        self.title = title
        self.subtitle = subtitle
        self.rack = rack
        self.variants = variants or {}
        self.variant = variant
        self.server: Server
        self.clock: Clock
        self.context: BuildContext
        self.running = False
        self.paused = False
        self._paused_panels: set[str] = set()
        self.master_output = rack.master_output_default
        self.preset_store = PresetStore(catalog_dir)
        self._bind_rack(rack)

        self.status = ft.Text("Engine stopped", color=MUTED, size=13)
        self.engine_button = ft.Button(
            "Start engine",
            icon=ft.Icons.POWER_SETTINGS_NEW,
            bgcolor=ACCENT,
            color="#07110F",
            on_click=self._handle_engine,
        )
        self.pause_button = ft.Button(
            "Pause",
            icon=ft.Icons.PAUSE,
            disabled=True,
            on_click=self._handle_pause,
        )
        self.master_output_text = ft.Text(
            f"{self.master_output:.2f}",
            color=ACCENT,
            size=13,
            weight=ft.FontWeight.BOLD,
        )
        self.master_output_slider = ft.Slider(
            min=0,
            max=rack.master_output_max,
            divisions=20,
            value=self.master_output,
            active_color=ACCENT,
            inactive_color="#31403D",
            on_change=self._handle_master_output,
        )
        self.preset_dropdown = ft.Dropdown(
            label="Preset",
            options=[ft.dropdown.Option(name) for name in self.preset_store.names()],
            expand=True,
        )
        self.preset_name_field = ft.TextField(
            label="Save as", value="my_preset", expand=True
        )
        self.key_dropdown = ft.Dropdown(
            label="Key",
            options=[
                ft.dropdown.Option(key=str(pitch_class), text=name)
                for pitch_class, name in enumerate(NOTE_NAMES)
            ],
            value=str(rack.harmony.key),
            width=140,
            on_select=self._handle_key,
        )

        self.progression_dropdown = ft.Dropdown(
            label="Progression",
            options=[
                ft.dropdown.Option(key=str(i), text=name)
                for i, name in enumerate(Progression.labels())
            ],
            value=self._progression_value(),
            width=180,
            on_select=self._handle_progression,
        )

        self.variant_dropdown = ft.Dropdown(
            label="Style",
            options=[ft.dropdown.Option(name) for name in self.variants],
            value=variant,
            width=180,
            on_select=self._handle_variant,
        )

        self._configure_page()
        self._build_view()

    def _bind_rack(self, rack: Rack) -> None:
        """Make `rack` the live rack: one panel per patch and the group views."""
        self.rack = rack
        patches = [patch for group in rack.groups for patch in group.patches]
        self.panels = {patch.name: PatchPanel(patch) for patch in patches}
        if len(self.panels) != len(patches):
            raise ValueError("Patch names must be unique across rack groups")
        self.groups = [self._patch_group(group) for group in rack.groups]
        self.control_sliders = [
            slider
            for top in self.groups
            for group in top.walk()
            for slider in group.control_sliders
        ]

    def _patch_group(self, group: GroupRuntime, path: str = "") -> PatchGroup:
        """The view of `group` and, recursively, the groups nested in it."""
        here = f"{path}/{group.title}" if path else group.title
        return PatchGroup(
            group,
            [self.panels[patch.name] for patch in group.own_patches],
            [self._patch_group(child, here) for child in group.children],
            path=path,
            on_control_change=self.sync_panels,
        )

    # -- page setup ------------------------------------------------------

    def _configure_page(self) -> None:
        self.page.title = self.title
        self.page.bgcolor = BACKGROUND
        self.page.padding = 0
        self.page.theme = ft.Theme(font_family="Avenir Next")
        self.page.window.full_screen = False
        self.page.window.maximized = True
        self.page.window.width = 1100
        self.page.window.height = 900
        self.page.window.min_width = 420
        self.page.window.min_height = 600
        self.page.on_close = self.close

    def _build_view(self) -> None:
        rack_controls: list[ft.Control] = [
            ft.Row(
                controls=[
                    *([self.variant_dropdown] if self.variants else []),
                    self.engine_button,
                    self.pause_button,
                    self.key_dropdown,
                    self.progression_dropdown,
                ],
                alignment=ft.MainAxisAlignment.END,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                spacing=8,
                run_spacing=8,
            ),
            ft.Row(
                controls=[
                    self.preset_dropdown,
                    ft.Button("Load", on_click=self._load_preset),
                ],
                spacing=8,
            ),
            ft.Row(
                controls=[
                    self.preset_name_field,
                    ft.Button("Save", icon=ft.Icons.SAVE, on_click=self._save_preset),
                ],
                spacing=8,
            ),
        ]
        level_controls: list[ft.Control] = []
        level_controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Master output", color=TEXT, size=14),
                                self.master_output_text,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        self.master_output_slider,
                        ft.Text(
                            f"Safety-capped at {self.rack.master_output_max:.2f}; starts at {self.rack.master_output_default:.2f}.",
                            color=MUTED,
                            size=11,
                        ),
                    ],
                    spacing=2,
                ),
                col={"xs": 12, "md": 6},
            )
        )
        rack_controls.append(
            ft.ResponsiveRow(controls=level_controls, spacing=12, run_spacing=8)
        )
        header = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    self.title.upper(),
                                    size=12,
                                    color=ACCENT,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    self.subtitle,
                                    size=28,
                                    color=TEXT,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                self.status,
                            ],
                            spacing=3,
                        ),
                        col={"xs": 12, "lg": 5},
                    ),
                    ft.Container(
                        content=ft.Column(controls=rack_controls, spacing=8),
                        col={"xs": 12, "lg": 7},
                    ),
                ],
                spacing=24,
                run_spacing=16,
            ),
            padding=28,
            bgcolor="#121D1B",
        )
        group_list = ft.ListView(
            controls=[group.control for group in self.groups],
            spacing=0,
            expand=True,
        )
        self.page.add(
            ft.Column(
                controls=[
                    header,
                    ft.Container(
                        content=group_list,
                        padding=ft.padding.Padding(left=28, top=0, right=28, bottom=0),
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            )
        )

    def sync_panels(self) -> None:
        """Refresh every slider from its patch and group, after values changed
        outside the panels (a group control push)."""
        for panel in self.panels.values():
            panel.sync_sliders()
        for slider in self.control_sliders:
            slider.show()

    # -- engine lifecycle --------------------------------------------------

    def _handle_engine(self, e: ft.ControlEvent) -> None:
        self.toggle_engine()

    def toggle_engine(self) -> None:
        if self.running:
            self._stop_engine()
        else:
            self._start_engine()
        self.page.update()

    def _handle_pause(self, e: ft.ControlEvent) -> None:
        self.toggle_pause()

    def toggle_pause(self) -> None:
        if not self.running:
            return
        if not self.paused:
            self._paused_panels = {
                name for name, panel in self.panels.items() if panel.enabled
            }
            for panel in self.panels.values():
                panel.apply_enabled(False)
            self.paused = True
            self.pause_button.text = "Start"
            self.pause_button.icon = ft.Icons.PLAY_ARROW
        else:
            for name, panel in self.panels.items():
                panel.apply_enabled(name in self._paused_panels)
            self.paused = False
            self.pause_button.text = "Pause"
            self.pause_button.icon = ft.Icons.PAUSE
        self.page.update()

    def _handle_master_output(self, e: ft.ControlEvent) -> None:
        self.master_output = float(e.control.value)
        self.master_output_text.value = f"{self.master_output:.2f}"
        if self.running:
            self.server.setAmp(self.master_output)
        e.page.update()

    def _handle_key(self, e: ft.ControlEvent) -> None:
        self._set_key(int(e.control.value))
        e.page.update()

    def _progression_value(self) -> str | None:
        """The dropdown value for the rack's chord roots; None (blank) when
        the rack's own progression isn't one of the named presets."""
        progression = self.rack.harmony.progression
        if isinstance(progression, Progression):
            return str(progression.index)
        return None

    def _progression_preset(self) -> dict[str, str]:
        """The preset entry for a named progression; empty for a rack's own."""
        progression = self.rack.harmony.progression
        if isinstance(progression, Progression):
            return {"progression": Progression.labels()[progression.index]}
        return {}

    def _handle_progression(self, e: ft.ControlEvent) -> None:
        # patches read the progression on each note, so no rebuild is needed
        self._set_progression(int(e.control.value))
        e.page.update()

    def _set_progression(self, index: int) -> None:
        self.rack.harmony.progression = Progression.by_index(index)
        self.progression_dropdown.value = str(index)

    def _set_key(self, pitch_class: int) -> None:
        # patches read the key on each note, so no rebuild is needed
        self.rack.harmony.key = pitch_class
        self.key_dropdown.value = str(pitch_class)

    def _start_engine(self) -> None:
        try:
            server = start_server(nchnls=self.rack.nchnls)
        except (OSError, PyoError, RuntimeError) as error:
            self.status.value = f"Audio error: {error}"
            self.status.color = ERROR
            return
        self.server = server
        self.server.setAmp(self.master_output)
        tempo = Tempo(bpm=self.rack.bpm)
        self.clock = Clock(tempo, ticks_per_bar=self.rack.ticks_per_bar)
        self.clock.start()
        for group in self.rack.evolving_groups:
            group.start(self.clock)
        context = BuildContext(tempo, self.clock, self.rack.harmony)
        self.context = context
        self.running = True
        self.page.run_task(self._animate_sweeps)
        for panel in self.panels.values():
            panel.engine_started(context)
        for group in self.groups:
            group.set_engine_ready(True)

        self.status.value = "Engine running"
        self.status.color = ACCENT
        self.engine_button.text = "Stop engine"
        self.engine_button.icon = ft.Icons.STOP
        self.pause_button.disabled = False

    async def _animate_sweeps(self) -> None:
        """While the engine runs, move every live sweep marker ~10 times a
        second; the sweeps themselves run in pyo, this only draws them."""
        while self.running:
            moving = [panel.refresh_sweeps() for panel in self.panels.values()]
            if any(moving):
                self.page.update()
            await asyncio.sleep(0.1)

    def _stop_engine(self) -> None:
        if not self.running:
            return
        self.running = False
        self.paused = False
        self._paused_panels = set()
        for group in self.groups:
            group.set_engine_ready(False)
        for panel in self.panels.values():
            panel.engine_stopped()
        for group in self.rack.evolving_groups:
            group.stop()
        self.clock.stop()
        self.server.stop()
        self.server.shutdown()
        self.status.value = "Engine stopped"
        self.status.color = MUTED
        self.engine_button.text = "Start engine"
        self.engine_button.icon = ft.Icons.POWER_SETTINGS_NEW
        self.pause_button.text = "Pause"
        self.pause_button.icon = ft.Icons.PAUSE
        self.pause_button.disabled = True

    # -- style variants ----------------------------------------------------

    def _handle_variant(self, e: ft.ControlEvent) -> None:
        name = e.control.value
        if name and name != self.variant:
            self._swap_variant(name)
        self.page.update()

    def _swap_variant(self, name: str) -> None:
        """Replace the rack with another variant's, keeping the audio server,
        clock and key. The new variant is switched on (starting the engine
        first if it is stopped)."""
        for panel in self.panels.values():
            panel.engine_stopped()
        if self.running:
            for group in self.rack.evolving_groups:
                group.stop()
        key = self.rack.harmony.key
        rack, catalog_dir = self.variants[name]()
        rack.harmony.key = key
        self.variant = name
        self.preset_store = PresetStore(catalog_dir)
        self.preset_dropdown.options = [
            ft.dropdown.Option(n) for n in self.preset_store.names()
        ]
        self.preset_dropdown.value = None
        self._bind_rack(rack)
        self.progression_dropdown.value = self._progression_value()
        self.paused = False
        self.pause_button.text = "Pause"
        self.pause_button.icon = ft.Icons.PAUSE
        if self.running:
            self.context = BuildContext(self.context.tempo, self.clock, rack.harmony)
            for group in rack.evolving_groups:
                group.start(self.clock)
            for panel in self.panels.values():
                panel.engine_started(self.context)
            for group in self.groups:
                group.set_engine_ready(True)
        else:
            self._start_engine()
        if self.running:
            for panel in self.panels.values():
                panel.apply_enabled(True)
            for top in self.groups:
                for group in top.walk():
                    group.reveal_enabled()
        self.page.controls.clear()
        self._build_view()

    # -- presets -------------------------------------------------------------

    def _load_preset(self, e: ft.ControlEvent) -> None:
        name = self.preset_dropdown.value
        if not name:
            return
        try:
            preset = self.preset_store.load(name)
        except (OSError, json.JSONDecodeError) as error:
            self.status.value = f"Could not load preset: {error}"
            self.status.color = ERROR
            self.page.update()
            return
        rack_values = preset.get(RACK_PRESET_KEY, {})
        if rack_values.get("key") in NOTE_NAMES:
            self._set_key(NOTE_NAMES.index(rack_values["key"]))
        if rack_values.get("progression") in Progression.labels():
            self._set_progression(
                Progression.labels().index(rack_values["progression"])
            )
        control_values = rack_values.get("controls", {})
        for control in self.control_sliders:
            if control.path in control_values:
                control.set_value(float(control_values[control.path]))
        for patch_name, panel in self.panels.items():
            if patch_name in preset:
                panel.apply_preset(preset[patch_name])
        for top in self.groups:
            for group in top.walk():
                group.reveal_enabled()
        self.page.update()

    def _save_preset(self, e: ft.ControlEvent) -> None:
        name = (self.preset_name_field.value or "").strip()
        if not name:
            return
        values: dict[str, Any] = {
            patch_name: panel.to_preset() for patch_name, panel in self.panels.items()
        }
        values[RACK_PRESET_KEY] = {
            "key": NOTE_NAMES[self.rack.harmony.key],
            **self._progression_preset(),
            "controls": {
                control.path: control.group.values[control.control]
                for control in self.control_sliders
            },
        }
        self.preset_store.save(name, values)
        self.preset_dropdown.options = [
            ft.dropdown.Option(n) for n in self.preset_store.names()
        ]
        self.preset_dropdown.value = name
        self.status.value = f"Saved preset '{name}'"
        self.status.color = ACCENT
        self.page.update()

    def close(self, e: ft.ControlEvent) -> None:
        self._stop_engine()
