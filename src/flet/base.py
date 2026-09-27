"""Shared Flet <-> Pyo patch plumbing.

This module abstracts the conversion between a `Patch` subclass instance (as
exposed by the modules under `pyoscillate.patches`) and a Flet UI: one patch
per `PatchPanel`, rendering an enable switch, parameter sliders, and a volume
slider, all wired to a shared `PatchRack`. `PatchRackApp` composes any number
of `PatchPanel`s into a single scrollable page with an audio-engine
start/stop control and JSON preset save/load, so the same code drives a
single-patch app (`soundscape_fm`) or a whole rack of patches (`deep_house`,
`psyambient`, `rack_demo`).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyo.lib._core import PyoError
from pyo.lib.analysis import Follower2
from pyo.lib.dynamics import Clip
from pyo.lib.server import Server

import flet as ft
from pyoscillate.clock import DEFAULT_TICKS_PER_BAR, Clock
from pyoscillate.controller import GroupController
from pyoscillate.harmony import NOTE_NAMES, Harmony
from pyoscillate.patches.base import Patch, PatchRack, start_server
from pyoscillate.patches.params import SliderSpec
from pyoscillate.projects.base import MacroSpec, Rack
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

    `self.patch`'s own attributes (one per `SliderSpec`, seeded at
    construction and kept current by `Patch.set()`) are the only copy of a
    slider's current value - this panel never shadows them in a separate
    dict. A slider move calls `patch.set(...)` immediately, which live-updates
    the running Pyo graph when one exists; `_apply()` only decides whether
    that move also requires a full rebuild (one of `rebuild_parameters`
    changed since the last build).
    """

    def __init__(
        self,
        rack: PatchRack,
        patch: Patch,
        resolve_group_patch: Callable[[str], Patch | None] | None = None,
    ) -> None:
        self.rack = rack
        self.patch = patch
        self._resolve_group_patch = resolve_group_patch
        self.enabled = False
        self.volume = patch.volume_default
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
        value = getattr(self.patch, spec.name)
        value_text = ft.Text(spec.format(value), color=ACCENT, size=13, weight=ft.FontWeight.BOLD)
        self._value_texts[spec.name] = value_text
        # the track runs in the spec's position space (semitones for a note
        # slider), so its ticks are what the slider can actually produce
        slider = ft.Slider(
            min=spec.to_position(spec.minimum),
            max=spec.to_position(spec.maximum),
            divisions=spec.divisions,
            value=spec.to_position(value),
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
                    ft.Text(spec.help_text, color=MUTED, size=12),
                    slider,
                ],
                spacing=2,
            ),
            col={"xs": 12, "md": 6},
            padding=ft.padding.Padding(left=0, top=4, right=0, bottom=4),
        )

    def _build_control(self) -> ft.Control:
        rows = [self._slider_row(spec) for spec in self.patch.parameters]
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
                col={"xs": 12, "md": 6},
                padding=ft.padding.Padding(left=0, top=4, right=0, bottom=4),
            )
        )
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(self.patch.title, color=TEXT, weight=ft.FontWeight.BOLD),
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

    # -- engine lifecycle --------------------------------------------------

    def set_engine_ready(self, ready: bool, build_kwargs: dict[str, Any] | None = None) -> None:
        self._engine_ready = ready
        self.build_kwargs = build_kwargs or {}
        self.switch.disabled = not ready
        if not ready:
            self.enabled = False
            self.switch.value = False
            self._built_values = None
            self.rack.stop(self.patch.name)

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
        patch = self.rack.get(self.patch.name)
        if patch is not None:
            patch.set("volume", self.volume)
        e.page.update()

    def _handle_slider(self, spec: SliderSpec, e: ft.ControlEvent) -> None:
        value = spec.from_position(float(e.control.value))
        self.patch.set(spec.name, value)
        self._value_texts[spec.name].value = spec.format(value)
        self._apply()
        e.page.update()

    def _apply(self) -> None:
        name = self.patch.name
        if not self.enabled or not self._engine_ready or not self._group_enabled:
            self.rack.stop(name)
            return

        running = self.rack.get(name)
        rebuild = running is None or (
            self._built_values is not None
            and any(
                getattr(self.patch, key) != self._built_values[key]
                for key in self.patch.rebuild_parameters
            )
        )
        if rebuild:
            running = self.patch.build(**self.build_kwargs)
            self._wire_sidechain(running)
            self.rack.start(name, running)
        running.set("volume", self.volume)
        self._built_values = {
            key: getattr(self.patch, key) for key in self.patch.rebuild_parameters
        }

    def _wire_sidechain(self, patch: Patch) -> None:
        """If this patch declares a `SidechainSource` and that source
        group's currently active patch is already built, duck this patch's
        voice off the source's live signal. See `SidechainSource` for the
        resolution-order limitation."""
        sidechain = patch.sidechain
        if sidechain is None or self._resolve_group_patch is None:
            return
        source = self._resolve_group_patch(sidechain.group_name)
        if source is None:
            return
        follower = Follower2(source.voice, falltime=sidechain.release)
        duck = 1 - Clip(follower, min=0, max=1) * sidechain.depth
        patch.voice = patch.voice * duck
        patch.retain(follower, duck)

    # -- presets -------------------------------------------------------------

    def to_preset(self) -> dict[str, Any]:
        values = {spec.name: getattr(self.patch, spec.name) for spec in self.patch.parameters}
        return {"enabled": self.enabled, **values, "volume": self.volume}

    def apply_preset(self, data: dict[str, Any]) -> None:
        self.enabled = bool(data.get("enabled", False))
        self.switch.value = self.enabled
        for spec in self.patch.parameters:
            if spec.name in data:
                value = spec.snap(float(data[spec.name]))
                self.patch.set(spec.name, value)
                self._sliders[spec.name].value = spec.to_position(value)
                self._value_texts[spec.name].value = spec.format(value)
        self.volume = float(data.get("volume", self.patch.volume_default))
        self.volume_slider.value = self.volume
        self.volume_text.value = f"{self.volume:.1f}"
        self._apply()


GROUP_CONTROLLER_BARS_MAX = 64
GROUP_CONTROLLER_REPEAT_MAX = 16


class PatchGroup:
    """Named group control that gates a row of related patch panels, plus
    (when `group_def.bars` is set) the live sliders for that
    `GroupController`'s own interval/repeat - the group-level evolution
    timer described in `controller.py`, distinct from any patch's own
    parameters."""

    def __init__(self, group_def: GroupController, panels: list[PatchPanel]) -> None:
        self.group_def = group_def
        self.panels = panels
        self.enabled = True
        self.switch = ft.Switch(
            value=True,
            active_color=ACCENT,
            on_change=self._handle_enabled,
            disabled=True,
        )
        self.controller = group_def if group_def.bars is not None else None
        if self.controller is not None:
            self.bars_text = ft.Text(
                f"{self.controller.bars}", color=ACCENT, size=13, weight=ft.FontWeight.BOLD
            )
            self.bars_slider = ft.Slider(
                min=1,
                max=GROUP_CONTROLLER_BARS_MAX,
                divisions=GROUP_CONTROLLER_BARS_MAX - 1,
                value=self.controller.bars,
                active_color=ACCENT,
                inactive_color="#31403D",
                on_change=self._handle_bars,
            )
            self.repeat_text = ft.Text(
                f"{self.controller.repeat}", color=ACCENT, size=13, weight=ft.FontWeight.BOLD
            )
            self.repeat_slider = ft.Slider(
                min=1,
                max=GROUP_CONTROLLER_REPEAT_MAX,
                divisions=GROUP_CONTROLLER_REPEAT_MAX - 1,
                value=self.controller.repeat,
                active_color=ACCENT,
                inactive_color="#31403D",
                on_change=self._handle_repeat,
            )
        self.control = self._build_control()

    def _controller_row(self, label: str, help_text: str, text: ft.Text, slider: ft.Slider) -> ft.Container:
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

    def _handle_bars(self, e: ft.ControlEvent) -> None:
        assert self.controller is not None
        value = round(float(e.control.value))
        self.controller.set_bars(value)
        self.bars_text.value = f"{value}"
        e.page.update()

    def _handle_repeat(self, e: ft.ControlEvent) -> None:
        assert self.controller is not None
        value = round(float(e.control.value))
        self.controller.set_repeat(value)
        self.repeat_text.value = f"{value}"
        e.page.update()

    def _build_control(self) -> ft.Control:
        controller_rows = []
        if self.controller is not None:
            controller_rows.append(
                self._controller_row(
                    "Evolve every (bars)",
                    "How many bars pass before this group's evolution moves on.",
                    self.bars_text,
                    self.bars_slider,
                )
            )
            controller_rows.append(
                self._controller_row(
                    "Repeat",
                    "How many times each step repeats before advancing to the next.",
                    self.repeat_text,
                    self.repeat_slider,
                )
            )

        patch_columns = []
        panel_column = 12 if len(self.panels) == 1 or len(self.panels) > 2 else 6
        for panel in self.panels:
            patch_columns.append(
                ft.Container(content=panel.control, col={"xs": 12, "md": panel_column})
            )

        return ft.Container(
            content=ft.ExpansionTile(
                title=ft.Text(self.group_def.title, color=TEXT, size=18, weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(self.group_def.summary, color=MUTED, size=12)
                if self.group_def.summary
                else None,
                leading=self.switch,
                expanded=False,
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                *(
                                    [ft.ResponsiveRow(controls=controller_rows, spacing=16)]
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
    macro: MacroSpec | None = None
    group_controllers: tuple[GroupController, ...] = ()


class PatchRackApp:
    """A scrollable page of `PatchPanel`s sharing one `PatchRack`, one Pyo
    `Server`, and one JSON preset catalog - the generic shape behind both
    the single-patch `soundscape_fm` app and the multi-patch rack apps."""

    def __init__(
        self,
        page: ft.Page,
        title: str,
        subtitle: str,
        rack: Rack,
        catalog_dir: Path | None = None,
    ) -> None:
        patch_groups = list(rack.groups)
        engine = rack.engine_spec()
        self.page = page
        self.title = title
        self.subtitle = subtitle
        self.engine = engine
        self.server: Server | None = None
        self.tempo: Tempo | None = None
        self.clock: Clock | None = None
        self.harmony = engine.harmony
        self.group_controllers = engine.group_controllers
        self.rack = PatchRack()
        self.master_output = engine.master_output_default
        self.preset_store = PresetStore(catalog_dir or Path.cwd() / "presets")
        patches = [patch for group in patch_groups for patch in group.patches]
        self.panels = {
            patch.name: PatchPanel(self.rack, patch, resolve_group_patch=self._resolve_group_patch)
            for patch in patches
        }
        if len(self.panels) != len(patches):
            raise ValueError("Patch names must be unique across rack groups")
        self.groups = [
            PatchGroup(group, [self.panels[patch.name] for patch in group.patches])
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
        self.macro: MacroSpec | None = engine.macro
        self.macro_slider: ft.Slider | None = None
        self.macro_text: ft.Text | None = None
        if self.macro is not None:
            spec = self.macro.slider
            self.macro_text = ft.Text(
                spec.format(spec.default), color=ACCENT, size=13, weight=ft.FontWeight.BOLD
            )
            self.macro_slider = ft.Slider(
                min=spec.minimum,
                max=spec.maximum,
                divisions=spec.divisions,
                value=spec.default,
                active_color=ACCENT,
                inactive_color="#31403D",
                on_change=self._handle_macro,
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
        rack_controls: list[ft.Control] = [
            ft.Row(
                controls=[
                    self.engine_button,
                    *([self.key_dropdown] if self.key_dropdown is not None else []),
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
        if self.macro is not None:
            level_controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(self.macro.slider.description, color=TEXT, size=14),
                                    self.macro_text,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            self.macro_slider,
                        ],
                        spacing=2,
                    ),
                    col={"xs": 12, "md": 6},
                )
            )
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
                            f"Safety-capped at {self.engine.master_output_max:.2f}; starts at a low level.",
                            color=MUTED,
                            size=11,
                        ),
                    ],
                    spacing=2,
                ),
                col={"xs": 12, "md": 6 if self.macro is not None else 12},
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
                                    self.subtitle, size=28, color=TEXT, weight=ft.FontWeight.BOLD
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

    def _handle_macro(self, e: ft.ControlEvent) -> None:
        self._set_macro(float(e.control.value))
        e.page.update()

    def _set_macro(self, value: float) -> None:
        if self.macro is None or self.macro_slider is None or self.macro_text is None:
            return
        self.macro_slider.value = value
        self.macro_text.value = self.macro.slider.format(value)
        self.macro.apply(value, self._resolve_group_patch)

    def _resolve_group_patch(self, name: str) -> Patch | None:
        """The `Patch` instance currently active (built and running) in the
        named group, or `None` if the group has no patch on right now. Reuses
        the same rack lookup a panel's own switch already relies on, rather
        than tracking a second "which patch is on" state."""
        for group in self.groups:
            if group.group_def.name != name:
                continue
            for panel in group.panels:
                patch = self.rack.get(panel.patch.name)
                if patch is not None:
                    return patch
            return None
        return None

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
                    for controller in self.group_controllers:
                        controller.start(self.clock, self._resolve_group_patch)

            for panel in self.panels.values():
                kwargs: dict[str, Any] = {}
                if panel.patch.needs_tempo and self.tempo is not None:
                    kwargs["tempo"] = self.tempo
                if panel.patch.needs_clock and self.clock is not None:
                    kwargs["clock"] = self.clock
                if panel.patch.needs_harmony and self.harmony is not None:
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
        for controller in self.group_controllers:
            controller.stop()
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
        rack_values = preset.get(RACK_PRESET_KEY, {})
        rack_key = rack_values.get("key")
        if rack_key in NOTE_NAMES:
            self._set_key(NOTE_NAMES.index(rack_key))
        macro_value = rack_values.get("macro")
        if macro_value is not None:
            self._set_macro(float(macro_value))
        for patch_name, panel in self.panels.items():
            if patch_name in preset:
                panel.apply_preset(preset[patch_name])
        self.page.update()

    def _save_preset(self, e: ft.ControlEvent) -> None:
        name = (self.preset_name_field.value or "").strip()
        if not name:
            return
        values = {patch_name: panel.to_preset() for patch_name, panel in self.panels.items()}
        if self.harmony is not None or self.macro is not None:
            rack_values: dict[str, Any] = {}
            if self.harmony is not None:
                rack_values["key"] = NOTE_NAMES[self.harmony.key]
            if self.macro is not None and self.macro_slider is not None:
                rack_values["macro"] = self.macro_slider.value
            values[RACK_PRESET_KEY] = rack_values
        self.preset_store.save(name, values)
        self.preset_dropdown.options = [ft.dropdown.Option(n) for n in self.preset_store.names()]
        self.preset_dropdown.value = name
        self.status.value = f"Saved preset '{name}'"
        self.status.color = ACCENT
        self.page.update()

    def close(self, e: ft.ControlEvent | None = None) -> None:
        self._stop_engine()
