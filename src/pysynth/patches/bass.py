from __future__ import annotations

from pyo.lib.filters import MoogLP
from pyo.lib.generators import LFO
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable
from pyo.lib.triggers import Trig, TrigEnv

from pysynth.clock import SIXTEENTH, Clock
from pysynth.patches.base import Patch
from pysynth.tempo import Tempo

# one bar = 16 steps (16th notes)
# semitone offsets per step (root-heavy techno bassline, occasional octave/fifth stabs)
# 0 = root, 12 = octave up, 7 = fifth
NOTE_PATTERN = [0, 0, 0, 0, 0, 0, 12, 0, 0, 0, 7, 0, 0, 0, 0, 0]

# louder on the "and" of each beat for a driving feel
ACCENT_PATTERN = [1.0, 0.6, 0.6, 0.6, 0.9, 0.6, 0.6, 0.6, 1.0, 0.6, 0.6, 0.6, 0.9, 0.6, 0.6, 0.7]

ROOT_FREQ = 55  # A1, classic techno bass register


def build(
    tempo: Tempo,
    clock: Clock,
    root_freq: float = ROOT_FREQ,
    filter_res: float = 0.75,
    filter_base: float = 900,
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
