# Run: uv run flet run src/flet/minimal/app.py
"""Minimal crackle bisect harness: one source, no graphs, no rack UI.

Start from the plainest case (a pure pyo sine, no framework) and add one
feature at a time until the crackle appears. Every option is a checkbox or a
dropdown; changing the engine-level ones (buffer size) needs Stop/Start.

Sources
- Sine: a bare pyo `Sine`, no Patch, no Clock - the control. If this crackles,
  it's the audio device/server, not the framework.
- Keys / Bass: the real patch class, built and started like the rack does
  (limiter, fade, clock, sequencer).

Options
- Patch limiter chain: use `Patch.start()` (Compress + Clip + fade) vs. the
  raw voice sent straight to the output.
- Clock running: the shared `Clock` pattern that triggers notes. Off = a held
  patch with no notes, so Keys is silent; use Bass/drone-like sources or Sine.
- UI ticker: a 10 Hz `page.update()` loop that changes some text, like the rack
  app's `_animate_sweeps` loop.
- UI churn: the same loop updating 60 controls, to make the Python UI thread
  busy. Worst case for GIL contention with pyo's callbacks.
- Deep house rack source: the real `DeepHouseRack` (132 BPM, 512 clock ticks
  a bar, kick -> bass sidechain). Tick the patches to play; sidechains link
  as in the app, and kicks start before whatever ducks off them.
- Clock ticks/bar and BPM override: the clock's Pattern fires `ticks_per_bar`
  times a bar from inside the audio callback, so a high count at a high BPM
  (deep house: a callback every ~3.5 ms, shorter than the 5.8 ms buffer) is
  much more Python work per buffer than a slow rack.
- Sidechain ducking: off clears each patch's declared sidechains.
- Sweeps & evolve: off disables the rack-declared sweeps and evolutions.
- Patch graphs: the rack's `AnalysisView` (waveform + spectrum canvases) on
  the first patch, fed by a `LiveAnalyser` (a C-side `TableRec`, read on the
  UI thread) and refreshed 10x a second like an expanded tile in the rack app.
  The rack app has no master graph.
- Phrase dropdown: picks the patch's `phrase` live, the same `Param.write` +
  rebuild-if-needed path the rack's dropdown takes. Only for phrased patches.
- Auto-evolve phrase: the patch's own phrase `Evolution`, stepping through
  every phrase each bar on the shared clock (a stress test of runtime phrase
  changes).
- Phrase timeline UI: the rack's `EvolveTimeline` canvas for that evolution,
  redrawn by the ticker. Needs the UI ticker on to animate.
"""

from __future__ import annotations

import asyncio
import time

from pyo import Sine
from pyo.lib.server import Server

import flet as ft
from pyoscillate.analysis.live import LiveAnalyser
from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch, start_server
from pyoscillate.patches.tonal.bass.hover import BassHover
from pyoscillate.patches.tonal.keys.keys import Keys
from pyoscillate.projects.deep_house.rack import DeepHouseRack
from pyoscillate.tempo import Tempo
from src.flet.analysis import AnalysisView
from src.flet.timeline import EvolveTimeline

RACK_SOURCE = "Deep house rack (pick patches below)"
SOURCES: dict[str, type[Patch] | None] = {
    "Sine (pure pyo, no framework)": None,
    "Keys": Keys,
    "Bass hover": BassHover,
    RACK_SOURCE: None,
}
BUFFERS = (256, 512, 1024, 2048)
# `Clock` ticks per bar: the Pattern behind every patch fires this often per bar
TICKS = ("rack default", "32", "128", "512", "1024")
# the deep-house patches ticked by default: the kick, and the bass that ducks off it
RACK_DEFAULTS = ("kick_round", "bass_rolling")


def main(page: ft.Page) -> None:
    page.title = "Crackle bisect"
    page.scroll = ft.ScrollMode.AUTO
    state: dict[str, object] = {
        "server": None,
        "held": [],
        "running": False,
        "patch": None,
        "context": None,
        "timeline": None,
        "built": {},
        "raw": [],
    }

    status = ft.Text("Stopped")
    ticker_text = ft.Text("")
    churn = [ft.Text("") for _ in range(60)]

    source = ft.Dropdown(
        label="Source",
        value=next(iter(SOURCES)),
        options=[ft.DropdownOption(name) for name in SOURCES],
        width=320,
    )
    buffer = ft.Dropdown(
        label="Buffer size (applies on Start)",
        value="1024",
        options=[ft.DropdownOption(str(size)) for size in BUFFERS],
        width=320,
    )
    ticks = ft.Dropdown(
        label="Clock ticks per bar",
        value="rack default",
        options=[ft.DropdownOption(t) for t in TICKS],
        width=320,
    )
    bpm = ft.TextField(label="BPM override (blank = source default)", width=320)
    sidechain_on = ft.Checkbox(label="Sidechain ducking", value=True)
    automation_on = ft.Checkbox(label="Sweeps & evolve (rack-declared)", value=True)
    rack_names = [p.name for p in DeepHouseRack()._patches.values()]
    rack_boxes = [
        ft.Checkbox(label=name, value=name in RACK_DEFAULTS) for name in rack_names
    ]
    rack_panel = ft.Column(rack_boxes, spacing=0, height=220, scroll=ft.ScrollMode.AUTO)
    limiter = ft.Checkbox(label="Patch limiter chain (Patch.start)", value=True)
    clock_on = ft.Checkbox(label="Clock running", value=True)
    ticker = ft.Checkbox(label="UI ticker (10 Hz page.update)", value=False)
    churn_on = ft.Checkbox(label="UI churn (60 controls per tick)", value=False)
    phrase = ft.Dropdown(
        label="Phrase", options=[], width=320, disabled=True, on_select=None
    )
    evolve_on = ft.Checkbox(label="Auto-evolve phrase (every bar)", value=False)
    timeline_on = ft.Checkbox(label="Phrase timeline UI", value=False)
    timeline_slot = ft.Container()
    analysis_on = ft.Checkbox(label="Patch graphs (scope + spectrum, first patch)")
    patch_analyser = LiveAnalyser()
    patch_view = AnalysisView("First patch, left channel")
    patch_view.control.visible = False
    amp = ft.Slider(min=0, max=1, value=0.8, label="{value}", width=320)
    amp_label = ft.Text("Master amp")

    def on_amp(_: ft.ControlEvent) -> None:
        server = state["server"]
        if isinstance(server, Server):
            server.setAmp(float(amp.value))

    amp.on_change = on_amp

    def phrase_param(patch_class: type[Patch] | None):
        if patch_class is None:
            return None
        return next((p for p in patch_class.params if p.name == "phrase"), None)

    def sync_phrase_options(_: ft.ControlEvent | None = None) -> None:
        """Offer the chosen source's phrases (none for the Sine control)."""
        param = phrase_param(SOURCES[source.value or ""])
        if param is None:
            phrase.options, phrase.value, phrase.disabled = [], None, True
        else:
            phrase.options = [
                ft.dropdown.Option(key=str(i), text=name)
                for i, name in enumerate(param.spec.options)
            ]
            phrase.value = str(int(param.spec.default))
            phrase.disabled = False
        page.update()

    source.on_select = sync_phrase_options

    def rebuild_if_needed(patch: Patch) -> None:
        """Mirror `PatchPanel._apply`: rebuild only when a rebuild param moved."""
        built = state["built"]
        if all(p.read(patch) == built[p] for p in patch.rebuild_params):  # type: ignore[index]
            return
        patch.build(state["context"])  # type: ignore[arg-type]
        context = state["context"]
        patch.start(context.tempo, context.clock)  # type: ignore[attr-defined]
        state["built"] = {p: p.read(patch) for p in patch.rebuild_params}

    def on_phrase(e: ft.ControlEvent) -> None:
        patch = state["patch"]
        param = phrase_param(SOURCES[source.value or ""])
        if isinstance(patch, Patch) and param is not None:
            param.write(patch, float(e.control.value))
            rebuild_if_needed(patch)
            timeline = state["timeline"]
            if isinstance(timeline, EvolveTimeline):
                timeline.redraw()
            page.update()

    phrase.on_select = on_phrase

    def on_evolve(_: ft.ControlEvent) -> None:
        patch = state["patch"]
        param = phrase_param(SOURCES[source.value or ""])
        if not isinstance(patch, Patch) or param is None:
            return
        evolution = patch.evolution_of(param)
        evolution.configure(1)
        evolution.choices = evolution.order(evolution.options)
        evolution.set_enabled(bool(evolve_on.value))
        timeline = state["timeline"]
        if isinstance(timeline, EvolveTimeline):
            timeline.redraw()
        page.update()

    evolve_on.on_change = on_evolve

    def show_timeline() -> None:
        timeline = state["timeline"]
        timeline_slot.content = (
            timeline.control
            if timeline_on.value and isinstance(timeline, EvolveTimeline)
            else None
        )

    def on_timeline(_: ft.ControlEvent) -> None:
        show_timeline()
        page.update()

    timeline_on.on_change = on_timeline

    def prepare(patch: Patch) -> None:
        """Apply the sidechain / automation toggles before a patch starts."""
        if not sidechain_on.value:
            patch.sidechains = ()
        if not automation_on.value:
            for sweep in patch.sweeps.values():
                sweep.enabled = False
            for evolution in patch.evolutions:
                evolution.enabled = False

    def start(_: ft.ControlEvent | None = None) -> None:
        if state["running"]:
            return
        server = start_server(nchnls=2, buffersize=int(buffer.value or 1024))
        server.setAmp(float(amp.value))
        state["server"] = server
        held: list[object] = []
        patch_class = SOURCES[source.value or ""]
        if source.value == RACK_SOURCE:
            rack = DeepHouseRack()
            tempo = Tempo(bpm=float(bpm.value or rack.bpm))
            per_bar = (
                rack.ticks_per_bar
                if ticks.value == "rack default"
                else int(ticks.value or 0)
            )
            clock = Clock(tempo, ticks_per_bar=per_bar)
            context = BuildContext(tempo, clock, rack.harmony)
            chosen = [
                patch
                for patch in rack._patches.values()
                if any(b.label == patch.name and b.value for b in rack_boxes)
            ]
            for patch in chosen:
                patch.build(context)
            held.extend([tempo, clock, rack, *chosen])
            for patch in chosen:
                prepare(patch)
                patch.start(tempo, clock)
            clock.start()
        elif patch_class is None:
            sine = Sine(freq=220, mul=0.1).mix(2).out()
            held.append(sine)
            state["raw"] = [sine]
        else:
            tempo = Tempo(bpm=float(bpm.value or 61))
            per_bar = (
                Clock(tempo).ticks_per_bar
                if ticks.value == "rack default"
                else int(ticks.value or 0)
            )
            clock = Clock(tempo, ticks_per_bar=per_bar)
            context = BuildContext(tempo, clock, Harmony())
            patch = patch_class()
            patch.build(context)
            held.extend([tempo, clock, patch])
            state["patch"] = patch
            state["context"] = context
            state["built"] = {p: p.read(patch) for p in patch.rebuild_params}
            param = phrase_param(patch_class)
            if param is not None:
                state["timeline"] = EvolveTimeline(patch.evolution_of(param))
                show_timeline()
            prepare(patch)
            if limiter.value:
                patch.start(tempo, clock)
            else:
                raw = patch.voice.mix(2).out()
                held.append(raw)
                state["raw"] = [raw]
                patch.sequencer.play()
            if clock_on.value:
                clock.start()
        state["held"] = held
        state["running"] = True
        status.value = (
            f"Running: sr={server.getSamplingRate():.0f} "
            f"buffer={server.getBufferSize()} source={source.value}"
        )
        page.update()

    def stop(_: ft.ControlEvent | None = None) -> None:
        if not state["running"]:
            return
        state["running"] = False
        for item in state["held"]:  # type: ignore[attr-defined]
            if isinstance(item, Patch | Clock):
                item.stop()
        time.sleep(0.4)
        server = state["server"]
        if isinstance(server, Server):
            server.stop()
            server.shutdown()
        patch_analyser.detach()
        patch_view.show([], [], live=False)
        state["held"] = []
        state["raw"] = []
        state["server"] = None
        state["patch"] = state["timeline"] = state["context"] = None
        timeline_slot.content = None
        evolve_on.value = False
        status.value = "Stopped"
        page.update()

    def refresh_analysis() -> None:
        """Reconcile each analyser with what plays now, then redraw its view
        (the rack app's `_refresh_analysis`, once per tick)."""
        held = state["held"]
        patches = [i for i in held if isinstance(i, Patch)]  # type: ignore[union-attr]
        outputs = [o for patch in patches if (o := patch.output) is not None]
        outputs += state["raw"]  # type: ignore[operator]
        signals = outputs[:1] if analysis_on.value and state["running"] else []
        if not patch_analyser.monitors(signals):
            patch_analyser.detach()
            if signals:
                patch_analyser.attach_sum(signals)
        if not signals and not patch_view.live:
            return
        wave, spectrum = patch_analyser.snapshot()
        patch_view.show(wave, spectrum, live=bool(signals))

    def on_analysis(_: ft.ControlEvent) -> None:
        patch_view.control.visible = bool(analysis_on.value)
        page.update()

    analysis_on.on_change = on_analysis

    async def tick() -> None:
        count = 0
        while True:
            refresh_analysis()
            if ticker.value:
                count += 1
                ticker_text.value = f"tick {count}"
                if churn_on.value:
                    for control in churn:
                        control.value = f"{count} {time.perf_counter():.4f}"
                timeline = state["timeline"]
                if timeline_on.value and isinstance(timeline, EvolveTimeline):
                    timeline.redraw()
                page.update()
            await asyncio.sleep(0.1)

    page.add(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Button("Start", on_click=start),
                        ft.Button("Stop", on_click=stop),
                    ]
                ),
                status,
                source,
                buffer,
                limiter,
                clock_on,
                ticks,
                bpm,
                sidechain_on,
                automation_on,
                rack_panel,
                ticker,
                churn_on,
                phrase,
                evolve_on,
                timeline_on,
                timeline_slot,
                analysis_on,
                patch_view.control,
                amp_label,
                amp,
                ticker_text,
                ft.Column(churn, spacing=0),
            ]
        )
    )
    page.run_task(tick)


if __name__ == "__main__":
    ft.run(main)
