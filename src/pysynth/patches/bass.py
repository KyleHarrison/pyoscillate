from __future__ import annotations

from pyo.lib.filters import MoogLP
from pyo.lib.generators import LFO
from pyo.lib.pattern import Pattern
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable
from pyo.lib.triggers import Trig, TrigEnv

from pysynth.patches.base import Patch
from pysynth.tempo import Tempo

# one bar = 16 steps (16th notes)
# semitone offsets per step (root-heavy techno bassline, occasional octave/fifth stabs)
# 0 = root, 12 = octave up, 7 = fifth
NOTE_PATTERN = [0, 0, 0, 0, 0, 0, 12, 0, 0, 0, 7, 0, 0, 0, 0, 0]

# louder on the "and" of each beat for a driving feel
ACCENT_PATTERN = [1.0, 0.6, 0.6, 0.6, 0.9, 0.6, 0.6, 0.6, 1.0, 0.6, 0.6, 0.6, 0.9, 0.6, 0.6, 0.7]

ROOT_FREQ = 55  # A1, classic techno bass register


def build(tempo: Tempo, root_freq: float = ROOT_FREQ) -> Patch:
    """Rolling 16-step bassline through a resonant, LFO-swept lowpass filter."""
    step_trig = Trig()

    envelope_table = CosTable([(0, 0), (100, 1), (2000, 0.3), (8191, 0)])
    amp_env = TrigEnv(step_trig, table=envelope_table, dur=tempo.sixteenth * 0.9, mul=1.0)

    bass_table = HarmTable([1, 0, 0.4, 0, 0.2, 0, 0.1])
    bass_osc = Osc(table=bass_table, freq=root_freq, mul=amp_env)

    # filter cutoff LFO for movement: one full sweep per bar, riding on a base cutoff
    cutoff_lfo = LFO(freq=1 / tempo.bar, type=0, mul=400, add=900)
    voice = MoogLP(bass_osc, freq=cutoff_lfo, res=0.75)

    step = {"i": 0}

    def next_step() -> None:
        i = step["i"] % len(NOTE_PATTERN)
        bass_osc.freq = root_freq * pow(2, NOTE_PATTERN[i] / 12)
        amp_env.mul = ACCENT_PATTERN[i]
        step_trig.play()
        step["i"] += 1

    sequencer = Pattern(next_step, time=tempo.sixteenth)
    return Patch(sequencer=sequencer, voice=voice)
