from __future__ import annotations

from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox, interactive_output
from pyo.lib.filters import MoogLP
from pyo.lib.generators import LFO
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable
from pyo.lib.triggers import Trig, TrigEnv

from pysynth.clock import SIXTEENTH, Clock
from pysynth.patches.base import Patch, PatchRack
from pysynth.tempo import Tempo

# one bar = 16 steps (16th notes)
# semitone offsets per step (root-heavy techno bassline, occasional octave/fifth stabs)
# 0 = root, 12 = octave up, 7 = fifth
NOTE_PATTERN = [0, 0, 0, 0, 0, 0, 12, 0, 0, 0, 7, 0, 0, 0, 0, 0]

# louder on the "and" of each beat for a driving feel
ACCENT_PATTERN = [1.0, 0.6, 0.6, 0.6, 0.9, 0.6, 0.6, 0.6, 1.0, 0.6, 0.6, 0.6, 0.9, 0.6, 0.6, 0.7]

ROOT_FREQ = 92  # A#2, current notebook default


def build(
    tempo: Tempo,
    clock: Clock,
    root_freq: float = ROOT_FREQ,
    filter_res: float = 0.75,
    filter_base: float = 1380,
    filter_range: float = 400,
) -> Patch:
    """Rolling 16-step bassline through a resonant, LFO-swept lowpass filter.

    Args:
        tempo: Shared tempo grid; the filter sweep completes one cycle per
            `tempo.bar`.
        clock: Shared master pulse; the bassline steps every 16th note
            (`SIXTEENTH`), phase-locked to every other patch on the clock.
        root_freq: Fundamental frequency (Hz) of the bassline's root note,
            before the `NOTE_PATTERN` semitone offsets are applied each
            step. Raising it thins the bass out and brings it closer to the
            drone's register; lowering it digs deeper into the sub range.
        filter_res: MoogLP resonance (0-1ish, self-oscillates as it
            approaches/exceeds 1). Higher values emphasize frequencies right
            at the cutoff, giving the bass a more pronounced, whistling,
            "squelchy" character as the LFO sweeps past them; lower values
            give a smoother, less colored lowpass response.
        filter_base: Center cutoff frequency (Hz) the sweep LFO rides on top
            of. Raising it lets more of the bassline's harmonics through on
            average, for a brighter, more present tone; lowering it darkens
            and rounds off the bass.
        filter_range: How far (Hz) the LFO swings the cutoff above and below
            `filter_base` over each bar. Larger values make the filter sweep
            more dramatic - the bass audibly opens up and closes down each
            bar; smaller values keep the cutoff nearly static for a more
            constant tone.
    """
    step_trig = Trig()

    envelope_table = CosTable([(0, 0), (100, 1), (2000, 0.3), (8191, 0)])
    amp_env = TrigEnv(step_trig, table=envelope_table, dur=tempo.sixteenth * 0.9, mul=1.0)

    bass_table = HarmTable([1, 0, 0.4, 0, 0.2, 0, 0.1])
    bass_osc = Osc(table=bass_table, freq=root_freq, mul=amp_env)

    # filter cutoff LFO for movement: one full sweep per bar, riding on a base cutoff
    cutoff_lfo = LFO(freq=1 / tempo.bar, type=0, mul=filter_range, add=filter_base)
    voice = MoogLP(bass_osc, freq=cutoff_lfo, res=filter_res)

    step = {"i": 0}

    def next_step() -> None:
        i = step["i"] % len(NOTE_PATTERN)
        bass_osc.freq = root_freq * pow(2, NOTE_PATTERN[i] / 12)
        amp_env.mul = ACCENT_PATTERN[i]
        step_trig.play()
        step["i"] += 1

    sequencer = clock.subscribe(SIXTEENTH, next_step)
    return Patch(sequencer=sequencer, voice=voice)


def widget(rack: PatchRack, tempo: Tempo, clock: Clock) -> VBox:
    """Create bass controls with parameter descriptions beside each slider."""

    def set_params(enabled, root_freq, filter_res, filter_base, filter_range, volume):
        if not enabled:
            rack.stop("bass")
            return

        bass_patch = build(tempo, clock, root_freq, filter_res, filter_base, filter_range)
        bass_patch.volume = volume
        rack.start("bass", bass_patch)

    enabled = Checkbox(value=False, description="bass on/off")
    root_freq = FloatSlider(min=30, max=110, step=1, value=ROOT_FREQ, description="root_freq")
    filter_res = FloatSlider(min=0, max=1, step=0.05, value=0.75, description="filter_res")
    filter_base = FloatSlider(min=200, max=2000, step=10, value=1380, description="filter_base")
    filter_range = FloatSlider(min=0, max=1000, step=10, value=400, description="filter_range")
    volume = FloatSlider(min=0, max=2, step=0.1, value=1.0, description="volume")

    output = interactive_output(
        set_params,
        {
            "enabled": enabled,
            "root_freq": root_freq,
            "filter_res": filter_res,
            "filter_base": filter_base,
            "filter_range": filter_range,
            "volume": volume,
        },
    )
    slider_rows = [
        HBox([root_freq, HTML("Fundamental frequency of the bassline's root note.")]),
        HBox(
            [
                filter_res,
                HTML("Filter resonance - higher gives a more squelchy, whistling character."),
            ]
        ),
        HBox([filter_base, HTML("Center cutoff the sweep rides on - higher is brighter.")]),
        HBox([filter_range, HTML("How far the cutoff sweeps each bar - larger is more dramatic.")]),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
