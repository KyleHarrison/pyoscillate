from __future__ import annotations

from pyo.lib.filters import ButHP
from pyo.lib.generators import Noise, Sine
from pyo.lib.pattern import Pattern
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pysynth.patches.base import Patch
from pysynth.tempo import Tempo

CUTOFF_FREQ = 8000


def build(tempo: Tempo) -> Patch:
    """Subtle high-passed noise tick, once per 8th note, for top-end texture."""
    hat_trig = Trig()
    hat_noise = Noise(mul=0.5)

    # short, tight envelope so the hat ticks rather than hisses
    envelope_table = CosTable([(0, 0), (30, 1), (800, 0)])
    hat_env = TrigEnv(hat_trig, table=envelope_table, dur=0.2, mul=hat_noise)

    # slow swell over 32 steps so the ticks don't sit at a fixed level
    hat_swell = Sine(freq=1 / (32 * tempo.sixteenth), mul=0.3, add=0.8)

    # high-pass to keep it thin and airy, not a full noise burst
    voice = ButHP(hat_env, freq=CUTOFF_FREQ, mul=hat_swell, add=-0.2)

    sequencer = Pattern(hat_trig.play, time=tempo.eighth)
    return Patch(sequencer=sequencer, voice=voice)
