"""Shared Flet <-> Pyo patch plumbing.

This module abstracts the conversion between a `Patch` definition (a
`build()` function plus a tuple of `SliderSpec` parameters, as exposed by
the modules under `pyoscillate.patches`) and a Flet UI: one
`PatchDef` per patch, wrapped in a `PatchPanel` that renders an
enable switch, parameter sliders, and a volume slider, all wired to a shared
`PatchRack`. `PatchRackApp` composes any number of `PatchPanel`s into a single
scrollable page with an audio-engine start/stop control and JSON preset
save/load, so the same code drives a single-patch app (`soundscape_fm`) or a
whole rack of patches (`deep_house`, `psyambient`, `rack_demo`).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyo.lib._core import PyoError
from pyo.lib.server import Server

import flet as ft
from pyoscillate.clock import DEFAULT_TICKS_PER_BAR, Clock
from pyoscillate.harmony import NOTE_NAMES, Harmony
from pyoscillate.patches.base import Patch, PatchRack, start_server
from pyoscillate.patches.params import SliderSpec
from pyoscillate.tempo import Tempo

ACCENT = "#00A896"
BACKGROUND = "#101716"
PANEL = "#182220"
TILE_BG = "#1D2B28"
TEXT = "#F4F7F6"
MUTED = "#A9B8B4"
ERROR = "#FF8A80"
MASTER_OUTPUT_DEFAULT = 0.1
MASTER_OUTPUT_MAX = 0.2
# preset entry for rack-wide settings; the leading underscore keeps it from
# colliding with a patch name
RACK_PRESET_KEY = "_rack"

Preset = dict[str, dict[str, Any]]


@dataclass
class PatchDef:
    """Static description of one patch.

    `needs_tempo`/`needs_clock` tell `PatchRackApp` which shared objects to
    inject into `build_kwargs` once the audio engine is running, mirroring
    the `build(tempo, clock, ...)` / `build(tempo, ...)` / `build(...)`
    shapes used across `pyoscillate.patches`. `needs_harmony` injects the
    rack's shared `Harmony` as a `harmony=` keyword, for pitched patches
    that should follow the rack's key and chord changes.
    """

    name: str
    title: str
    summary: str
    build: Callable[..., Patch]
    parameters: tuple[SliderSpec, ...]
    volume_default: float = 0.6
    rebuild_parameters: tuple[str, ...] = ()
    needs_tempo: bool = False
    needs_clock: bool = False
    needs_harmony: bool = False


@dataclass
class PatchGroupDef:
    """A named set of related patch alternatives presented together."""

    name: str
    title: str
    patch_defs: tuple[PatchDef, ...]
    summary: str = ""


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
    """One patch's live controls, wired to a shared `PatchRack`.

    Rebuilds the underlying `Patch` only when one of `rebuild_parameters`
    changes value; every other slider move just calls `Patch.update()` in
    place.
    """

    def __init__(self, rack: PatchRack, patch_def: PatchDef) -> None:
        self.rack = rack
        self.patch_def = patch_def
        self.enabled = False
        self.volume = patch_def.volume_default
        self.values: dict[str, float] = {spec.name: spec.default for spec in patch_def.parameters}
        self.build_kwargs: dict[str, Any] = {}
        self._engine_ready = False
        self._group_enabled = True
        self._built_values: dict[str, Any] | None = None
        self._value_texts: dict[str, ft.Text] = {}
        self._sliders: dict[str, ft.Slider] = {}

        self.switch = ft.Switch(
            value=False, active_color=ACCENT, on_change=self._handle_enabled, disabled=True
        )
        self.volume_slider = ft.Slider(
            min=0,
            max=2,
            divisions=20,
            value=self.volume,
            active_color=ACCENT,
            on_change=self._handle_volume,
        )
        self.volume_text = ft.Text(
            f"{self.volume:.1f}", color=ACCENT, size=13, weight=ft.FontWeight.BOLD
        )
        self.control = self._build_control()

    # -- UI construction -------------------------------------------------

    def _slider_row(self, spec: SliderSpec) -> ft.Container:
        value_text = ft.Text(
            spec.format(spec.default), color=ACCENT, size=13, weight=ft.FontWeight.BOLD
        )
        self._value_texts[spec.name] = value_text
        # the track runs in the spec's position space (semitones for a note
        # slider), so its ticks are what the slider can actually produce
        slider = ft.Slider(
            min=spec.to_position(spec.minimum),
            max=spec.to_position(spec.maximum),
            divisions=spec.divisions,
            value=spec.to_position(spec.default),
            active_color=ACCENT,
            inactive_color="#31403D",
            on_change=lambda e, spec=spec: self._handle_slider(spec, e),
        )
        self._sliders[spec.name] = slider
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[ft.Text(spec.description, color=TEXT, size=14), value_text],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    slider,
                    ft.Text(spec.help_text, color=MUTED, size=11),
                ],
                spacing=2,
            ),
            padding=ft.padding.Padding(left=0, top=4, right=0, bottom=4),
        )

    def _build_control(self) -> ft.Control:
        rows = [self._slider_row(spec) for spec in self.patch_def.parameters]
        rows.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Output level", color=TEXT, size=14),
                                self.volume_text,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        self.volume_slider,
                    ],
                    spacing=2,
                ),
                padding=ft.padding.Padding(left=0, top=4, right=0, bottom=4),
            )
        )
        return ft.Container(
            content=ft.ExpansionTile(
                title=ft.Text(self.patch_def.title, color=TEXT, weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(self.patch_def.summary, color=MUTED, size=12),
                leading=self.switch,
                expanded=False,
                controls=[ft.Container(content=ft.Column(controls=rows, spacing=0), padding=16)],
            ),
            bgcolor=TILE_BG,
            border_radius=8,
            margin=ft.margin.Margin(left=0, top=0, right=0, bottom=8),
        )

    # -- engine lifecycle --------------------------------------------------

    def set_engine_ready(self, ready: bool, build_kwargs: dict[str, Any] | None = None) -> None:
        self._engine_ready = ready
        self.build_kwargs = build_kwargs or {}
        self.switch.disabled = not ready
        if not ready:
            self.enabled = False
            self.switch.value = False
            self._built_values = None
            self.rack.stop(self.patch_def.name)

    def set_group_enabled(self, enabled: bool) -> None:
        self._group_enabled = enabled
        self.switch.disabled = not self._engine_ready or not enabled
        self._apply()

    # -- event handlers ----------------------------------------------------

    def _handle_enabled(self, e: ft.ControlEvent) -> None:
        self.enabled = bool(e.control.value)
        self._apply()
        e.page.update()

    def _handle_volume(self, e: ft.ControlEvent) -> None:
        self.volume = float(e.control.value)
        self.volume_text.value = f"{self.volume:.1f}"
        patch = self.rack.get(self.patch_def.name)
        if patch is not None:
            patch.set("volume", self.volume)
        e.page.update()

    def _handle_slider(self, spec: SliderSpec, e: ft.ControlEvent) -> None:
        value = spec.from_position(float(e.control.value))
        self.values[spec.name] = value
        self._value_texts[spec.name].value = spec.format(value)
        self._apply()
        e.page.update()

    def _apply(self) -> None:
        name = self.patch_def.name
        if not self.enabled or not self._engine_ready or not self._group_enabled:
            self.rack.stop(name)
            return

        patch = self.rack.get(name)
        rebuild = patch is None or (
            self._built_values is not None
            and any(
                self.values[key] != self._built_values[key]
                for key in self.patch_def.rebuild_parameters
            )
        )
        if rebuild:
            patch = self.patch_def.build(**self.build_kwargs, **self.values)
            self.rack.start(name, patch)
        else:
            patch.update(
                {
                    key: value
                    for key, value in self.values.items()
                    if key not in self.patch_def.rebuild_parameters
                }
            )
        patch.set("volume", self.volume)
        self._built_values = dict(self.values)

    # -- presets -------------------------------------------------------------

    def to_preset(self) -> dict[str, Any]:
        return {"enabled": self.enabled, **self.values, "volume": self.volume}

    def apply_preset(self, data: dict[str, Any]) -> None:
        self.enabled = bool(data.get("enabled", False))
        self.switch.value = self.enabled
        for spec in self.patch_def.parameters:
            if spec.name in data:
                value = spec.snap(float(data[spec.name]))
                self.values[spec.name] = value
                self._sliders[spec.name].value = spec.to_position(value)
                self._value_texts[spec.name].value = spec.format(value)
        self.volume = float(data.get("volume", self.patch_def.volume_default))
        self.volume_slider.value = self.volume
        self.volume_text.value = f"{self.volume:.1f}"
        self._apply()


class PatchGroup:
    """Named group control that gates a row of related patch panels."""

    def __init__(self, group_def: PatchGroupDef, panels: list[PatchPanel]) -> None:
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

    def _build_control(self) -> ft.Control:
        heading_controls: list[ft.Control] = [
            ft.Text(self.group_def.title, color=TEXT, size=18, weight=ft.FontWeight.BOLD)
        ]
        if self.group_def.summary:
            heading_controls.append(ft.Text(self.group_def.summary, color=MUTED, size=12))

        patch_columns = []
        for panel in self.panels:
            panel.control.width = 320
            patch_columns.append(panel.control)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(controls=heading_controls, spacing=2, expand=True),
                            self.switch,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=patch_columns,
                        spacing=8,
                        scroll=ft.ScrollMode.AUTO,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ],
                spacing=12,
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


@dataclass
class EngineSpec:
    """How to boot the shared Pyo engine for a `PatchRackApp`: nchnls plus
    an optional shared tempo/clock for patches that need one.

    `bpm` and `ticks_per_bar` should come from the project's own rack module
    (e.g. `pyoscillate.projects.<project>.rack`), not be hardcoded here or
    in `app.py` alone - each project owns its own tempo and clock timing
    resolution. The same goes for `harmony`: when a rack shares one, the
    app shows a Key control that retunes every `needs_harmony` patch
    together, and saves the key with each preset.
    """

    nchnls: int = 2
    bpm: float | None = None
    needs_clock: bool = False
    ticks_per_bar: int = DEFAULT_TICKS_PER_BAR
    master_output_default: float = MASTER_OUTPUT_DEFAULT
    master_output_max: float = MASTER_OUTPUT_MAX
    harmony: Harmony | None = None


class PatchRackApp:
    """A scrollable page of `PatchPanel`s sharing one `PatchRack`, one Pyo
    `Server`, and one JSON preset catalog - the generic shape behind both
    the single-patch `soundscape_fm` app and the multi-patch rack apps."""

    def __init__(
        self,
        page: ft.Page,
        title: str,
        subtitle: str,
        patch_groups: list[PatchGroupDef],
        engine: EngineSpec,
        catalog_dir: Path | None = None,
    ) -> None:
        self.page = page
        self.title = title
        self.subtitle = subtitle
        self.engine = engine
        self.server: Server | None = None
        self.tempo: Tempo | None = None
        self.clock: Clock | None = None
        self.harmony = engine.harmony
        self.rack = PatchRack()
        self.master_output = engine.master_output_default
        self.preset_store = PresetStore(catalog_dir or Path.cwd() / "presets")
        patch_defs = [patch_def for group in patch_groups for patch_def in group.patch_defs]
        self.panels = {patch_def.name: PatchPanel(self.rack, patch_def) for patch_def in patch_defs}
        if len(self.panels) != len(patch_defs):
            raise ValueError("Patch names must be unique across rack groups")
        self.groups = [
            PatchGroup(group, [self.panels[patch_def.name] for patch_def in group.patch_defs])
            for group in patch_groups
        ]

        self.status = ft.Text("Engine stopped", color=MUTED, size=13)
        self.engine_button = ft.Button(
            "Start engine",
            icon=ft.Icons.POWER_SETTINGS_NEW,
            bgcolor=ACCENT,
            color="#07110F",
            on_click=self._toggle_engine,
        )
        self.master_output_text = ft.Text(
            f"{self.master_output:.2f}", color=ACCENT, size=13, weight=ft.FontWeight.BOLD
        )
        self.master_output_slider = ft.Slider(
            min=0,
            max=engine.master_output_max,
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
        self.preset_name_field = ft.TextField(label="Save as", value="my_preset", expand=True)
        self.key_dropdown: ft.Dropdown | None = None
        if self.harmony is not None:
            self.key_dropdown = ft.Dropdown(
                label="Key",
                options=[
                    ft.dropdown.Option(key=str(pitch_class), text=name)
                    for pitch_class, name in enumerate(NOTE_NAMES)
                ],
                value=str(self.harmony.key),
                width=140,
                on_select=self._handle_key,
            )

        self._configure_page()
        self._build_view()

    # -- page setup ------------------------------------------------------

    def _configure_page(self) -> None:
        self.page.title = self.title
        self.page.bgcolor = BACKGROUND
        self.page.padding = 0
        self.page.theme = ft.Theme(font_family="Avenir Next")
        self.page.window.width = 1100
        self.page.window.height = 900
        self.page.window.min_width = 420
        self.page.window.min_height = 600
        self.page.on_close = self.close

    def _build_view(self) -> None:
        header = ft.Container(
            content=ft.Row(
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
                                    self.subtitle, size=28, color=TEXT, weight=ft.FontWeight.BOLD
                                ),
                                self.status,
                            ],
                            spacing=3,
                        ),
                        width=320,
                    ),
                    self.engine_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                run_spacing=12,
            ),
            padding=28,
            bgcolor="#121D1B",
        )
        preset_controls = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.preset_dropdown,
                        ft.Button("Load", on_click=self._load_preset),
                    ]
                ),
                ft.Row(
                    controls=[
                        self.preset_name_field,
                        ft.Button("Save", icon=ft.Icons.SAVE, on_click=self._save_preset),
                    ]
                ),
                *([self.key_dropdown] if self.key_dropdown is not None else []),
            ],
            spacing=8,
        )
        master_row = ft.Container(
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
                        f"Safety-capped at {self.engine.master_output_max:.2f}; starts at a low level.",
                        color=MUTED,
                        size=11,
                    ),
                ],
                spacing=2,
            ),
            padding=ft.padding.Padding(left=28, top=0, right=28, bottom=12),
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
                        content=preset_controls,
                        padding=ft.padding.Padding(left=28, top=12, right=28, bottom=12),
                    ),
                    master_row,
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

    # -- engine lifecycle --------------------------------------------------

    def _toggle_engine(self, e: ft.ControlEvent | None = None) -> None:
        if self.server is not None:
            self._stop_engine()
        else:
            self._start_engine()
        self.page.update()

    def _handle_master_output(self, e: ft.ControlEvent) -> None:
        self.master_output = float(e.control.value)
        self.master_output_text.value = f"{self.master_output:.2f}"
        if self.server is not None:
            self.server.setAmp(self.master_output)
        e.page.update()

    def _handle_key(self, e: ft.ControlEvent) -> None:
        self._set_key(int(e.control.value))
        e.page.update()

    def _set_key(self, pitch_class: int) -> None:
        # patches read the key on each note, so no rebuild is needed
        if self.harmony is None or self.key_dropdown is None:
            return
        self.harmony.key = pitch_class
        self.key_dropdown.value = str(pitch_class)

    def _start_engine(self) -> None:
        try:
            self.server = start_server(nchnls=self.engine.nchnls)
            self.server.setAmp(self.master_output)
            build_kwargs_common: dict[str, Any] = {}
            if self.engine.bpm is not None:
                self.tempo = Tempo(bpm=self.engine.bpm)
                build_kwargs_common["tempo"] = self.tempo
                if self.engine.needs_clock:
                    self.clock = Clock(self.tempo, ticks_per_bar=self.engine.ticks_per_bar)
                    self.clock.start()

            for panel in self.panels.values():
                kwargs: dict[str, Any] = {}
                if panel.patch_def.needs_tempo and self.tempo is not None:
                    kwargs["tempo"] = self.tempo
                if panel.patch_def.needs_clock and self.clock is not None:
                    kwargs["clock"] = self.clock
                if panel.patch_def.needs_harmony and self.harmony is not None:
                    kwargs["harmony"] = self.harmony
                panel.set_engine_ready(True, kwargs)
            for group in self.groups:
                group.set_engine_ready(True)

            self.status.value = "Engine running"
            self.status.color = ACCENT
            self.engine_button.text = "Stop engine"
            self.engine_button.icon = ft.Icons.STOP
        except (OSError, PyoError, RuntimeError) as error:
            self.status.value = f"Audio error: {error}"
            self.status.color = ERROR
            self._stop_engine()

    def _stop_engine(self) -> None:
        for group in self.groups:
            group.set_engine_ready(False)
        for panel in self.panels.values():
            panel.set_engine_ready(False)
        self.rack.stop_all()
        if self.clock is not None:
            self.clock.stop()
            self.clock = None
        self.tempo = None
        if self.server is not None:
            self.server.stop()
            self.server.shutdown()
            self.server = None
        self.status.value = "Engine stopped"
        self.status.color = MUTED
        self.engine_button.text = "Start engine"
        self.engine_button.icon = ft.Icons.POWER_SETTINGS_NEW

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
        rack_key = preset.get(RACK_PRESET_KEY, {}).get("key")
        if rack_key in NOTE_NAMES:
            self._set_key(NOTE_NAMES.index(rack_key))
        for patch_name, panel in self.panels.items():
            if patch_name in preset:
                panel.apply_preset(preset[patch_name])
        self.page.update()

    def _save_preset(self, e: ft.ControlEvent) -> None:
        name = (self.preset_name_field.value or "").strip()
        if not name:
            return
        values = {patch_name: panel.to_preset() for patch_name, panel in self.panels.items()}
        if self.harmony is not None:
            values[RACK_PRESET_KEY] = {"key": NOTE_NAMES[self.harmony.key]}
        self.preset_store.save(name, values)
        self.preset_dropdown.options = [ft.dropdown.Option(n) for n in self.preset_store.names()]
        self.preset_dropdown.value = name
        self.status.value = f"Saved preset '{name}'"
        self.status.color = ACCENT
        self.page.update()

    def close(self, e: ft.ControlEvent | None = None) -> None:
        self._stop_engine()
