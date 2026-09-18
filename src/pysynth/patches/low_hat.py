from __future__ import annotations

from pyo.lib.filters import ButHP
from pyo.lib.generators import Noise, Sine
from pyo.lib.pattern import Pattern
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pysynth.patches.base import Patch
from pysynth.tempo import Tempo

CUTOFF_FREQ = 3000  # lower than the main hat (8000) so this reads as a darker, lower accent


def build(tempo: Tempo) -> Patch:
    """Darker noise tick, once per quarter note, as a rarer, dubbier accent."""
    hat_trig = Trig()
    hat_noise = Noise(mul=0.3)

    # same short, tight envelope shape as the main hat
    envelope_table = CosTable([(0, 0), (30, 1), (800, 0)])
    hat_env = TrigEnv(hat_trig, table=envelope_table, dur=0.5, mul=hat_noise)

    hat_swell = Sine(freq=1 / (32 * tempo.eighth), mul=0.3, add=0.8)

    voice = ButHP(hat_env, freq=CUTOFF_FREQ, mul=hat_swell, add=-0.2)

    sequencer = Pattern(hat_trig.play, time=tempo.fourth)
    return Patch(sequencer=sequencer, voice=voice)
