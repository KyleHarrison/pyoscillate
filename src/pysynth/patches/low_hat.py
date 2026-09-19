from __future__ import annotations

from pyo.lib.filters import ButHP
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pysynth.clock import FOURTH, Clock
from pysynth.patches.base import Patch
from pysynth.tempo import Tempo

CUTOFF_FREQ = 3000  # lower than the main hat (8000) so this reads as a darker, lower accent


def build(
    tempo: Tempo,
    clock: Clock,
    cutoff_freq: float = CUTOFF_FREQ,
    level: float = 0.3,
    decay: float = 0.5,
) -> Patch:
    """Darker noise tick, once per quarter note, as a rarer, dubbier accent.

    Args:
        tempo: Shared tempo grid; the level swell is derived from
            `tempo.eighth`.
        clock: Shared master pulse; the tick fires every quarter note
            (`FOURTH`), phase-locked to every other patch on the clock.
        cutoff_freq: ButHP high-pass cutoff (Hz). The default (3000) is much
            lower than the main hat's (8000), which is what makes this
            voice read as darker and lower. Raising it brings it closer to
            the main hat in character; lowering it further makes it darker
            and closer to a low thud than a hiss.
        level: Peak amplitude of the raw noise burst feeding the envelope,
            before the swell and high-pass are applied. Raising it makes
            this accent louder and more prominent against the main hat;
            lowering it keeps it as a subtler undercurrent.
        decay: Length (seconds) of the tick's amplitude envelope. The
            default (0.5) is longer than the main hat's (0.2), giving it
            more of a dubby tail; shorten it for a tighter, more clipped
            accent, or lengthen it for a longer decaying tock.
    """
    hat_trig = Trig()
    hat_noise = Noise(mul=level)

    # same short, tight envelope shape as the main hat
    envelope_table = CosTable([(0, 0), (30, 1), (800, 0)])
    hat_env = TrigEnv(hat_trig, table=envelope_table, dur=decay, mul=hat_noise)

    hat_swell = Sine(freq=1 / (32 * tempo.eighth), mul=0.3, add=0.8)

    voice = ButHP(hat_env, freq=cutoff_freq, mul=hat_swell, add=-0.2)

    sequencer = clock.subscribe(FOURTH, hat_trig.play)
    return Patch(sequencer=sequencer, voice=voice)
