"""Shared Flet <-> Pyo patch plumbing.

This module abstracts the conversion between a `Patch` subclass instance (as
exposed by the modules under `pyoscillate.patches`) and a Flet UI: one patch
per `PatchPanel`, rendering an enable switch, parameter sliders, and a volume
slider. `PatchRackApp` composes any number
of `PatchPanel`s into a single scrollable page with an audio-engine
start/stop control and JSON preset save/load, so the same code drives a
single-patch app (`soundscape_fm`) or a whole rack of patches (`deep_house`,
`psyambient`, `rack_demo`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyo.lib._core import PyoError
from pyo.lib.server import Server

import flet as ft
from pyoscillate.clock import Clock
from pyoscillate.controller import EvolvingRuntime, GroupRuntime
from pyoscillate.harmony import NOTE_NAMES
from pyoscillate.patches.base import BuildContext, Patch, start_server
from pyoscillate.patches.params import Param
from pyoscillate.projects.base import Macro, Rack
from pyoscillate.tempo import Tempo

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

        self.switch = ft.Switch(
            value=False,
            active_color=ACCENT,
            on_change=self._handle_enabled,
            disabled=True,
        )
        self.control = self._build_control()

    # -- UI construction -------------------------------------------------

    def _slider_row(self, param: Param) -> ft.Container:
        spec = param.spec
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
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(spec.description, color=TEXT, size=14),
                            value_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(spec.help_text, color=MUTED, size=12),
                    slider,
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

    def _show(self, param: Param, value: float) -> None:
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
            self.patch.start()
            self._built_values = {
                param: param.read(self.patch) for param in self.patch.rebuild_params
            }

    # -- presets -------------------------------------------------------------

    def to_preset(self) -> dict[str, Any]:
        values = {param.name: param.read(self.patch) for param in self.patch.params}
        return {"enabled": self.enabled, **values}

    def apply_preset(self, data: dict[str, Any]) -> None:
        self.enabled = bool(data.get("enabled", False))
        self.switch.value = self.enabled
        for param in self.patch.params:
            if param.name in data:
                value = param.spec.snap(float(data[param.name]))
                param.write(self.patch, value)
                self._show(param, value)
        self._apply()


GROUP_CONTROLLER_BARS_MAX = 64
GROUP_CONTROLLER_REPEAT_MAX = 16


class PatchGroup:
    """Titled group control that gates a row of related patch panels, plus
    (for an `EvolvingRuntime`) the live sliders for its own interval/repeat -
    the group-level evolution timer described in `controller.py`, distinct
    from any patch's own parameters."""

    def __init__(self, group_def: GroupRuntime, panels: list[PatchPanel]) -> None:
        self.group_def = group_def
        self.panels = panels
        self.enabled = True
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
        controller_rows = (
            self._evolution_rows(self.group_def)
            if isinstance(self.group_def, EvolvingRuntime)
            else []
        )

        patch_columns = []
        panel_column = 12 if len(self.panels) == 1 or len(self.panels) > 2 else 6
        for panel in self.panels:
            patch_columns.append(
                ft.Container(content=panel.control, col={"xs": 12, "md": panel_column})
            )

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
                                ft.ResponsiveRow(
                                    controls=patch_columns,
                                    spacing=12,
                                    run_spacing=12,
                                ),
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

    def set_engine_ready(self, ready: bool) -> None:
        self.switch.disabled = not ready
        for panel in self.panels:
            panel.set_group_enabled(self.enabled)

    def _handle_enabled(self, e: ft.ControlEvent) -> None:
        self.enabled = bool(e.control.value)
        for panel in self.panels:
            panel.set_group_enabled(self.enabled)
        e.page.update()


class MacroSlider:
    """A rack `Macro`'s slider and value readout."""

    def __init__(self, rack: Rack, macro: Macro, app: PatchRackApp) -> None:
        self.rack = rack
        self.macro = macro
        self.app = app
        spec = macro.slider
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
        self.control = ft.Container(
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
                ],
                spacing=2,
            ),
            col={"xs": 12, "md": 6},
        )

    def set_value(self, value: float) -> None:
        self.slider.value = value
        self.text.value = self.macro.slider.format(value)
        self.macro.apply(self.rack, value)
        self.app.sync_panels()

    def _handle_change(self, e: ft.ControlEvent) -> None:
        self.set_value(float(e.control.value))
        e.page.update()


class PatchRackApp:
    """A scrollable page of `PatchPanel`s for one `Rack`, sharing one Pyo
    `Server`, one clock, and one JSON preset catalog - the generic shape
    behind both the single-patch `soundscape_fm` app and the multi-patch rack
    apps."""

    def __init__(
        self,
        page: ft.Page,
        title: str,
        subtitle: str,
        rack: Rack,
        catalog_dir: Path,
    ) -> None:
        self.page = page
        self.title = title
        self.subtitle = subtitle
        self.rack = rack
        self.server: Server
        self.clock: Clock
        self.running = False
        self.paused = False
        self._paused_panels: set[str] = set()
        self.master_output = rack.master_output_default
        self.preset_store = PresetStore(catalog_dir)
        patches = [patch for group in rack.groups for patch in group.patches]
        self.panels = {patch.name: PatchPanel(patch) for patch in patches}
        if len(self.panels) != len(patches):
            raise ValueError("Patch names must be unique across rack groups")
        self.groups = [
            PatchGroup(group, [self.panels[patch.name] for patch in group.patches])
            for group in rack.groups
        ]

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
        self.macro_sliders = [MacroSlider(rack, macro, self) for macro in rack.macros]

        self._configure_page()
        self._build_view()

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
                controls=[self.engine_button, self.pause_button, self.key_dropdown],
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
        level_controls: list[ft.Control] = [
            macro.control for macro in self.macro_sliders
        ]
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
                            f"Safety-capped at {self.rack.master_output_max:.2f}; starts at a low level.",
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
        """Refresh every slider from its patch, after values changed outside
        the panels (a macro push)."""
        for panel in self.panels.values():
            panel.sync_sliders()

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
        self.running = True
        for panel in self.panels.values():
            panel.engine_started(context)
        for group in self.groups:
            group.set_engine_ready(True)

        self.status.value = "Engine running"
        self.status.color = ACCENT
        self.engine_button.text = "Stop engine"
        self.engine_button.icon = ft.Icons.STOP
        self.pause_button.disabled = False

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
        macro_values = rack_values.get("macros", {})
        for control in self.macro_sliders:
            if control.macro.slider.name in macro_values:
                control.set_value(float(macro_values[control.macro.slider.name]))
        for patch_name, panel in self.panels.items():
            if patch_name in preset:
                panel.apply_preset(preset[patch_name])
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
            "macros": {
                control.macro.slider.name: control.slider.value
                for control in self.macro_sliders
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
