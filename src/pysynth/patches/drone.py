from __future__ import annotations

from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM, Sine
from pyo.lib.pattern import Pattern

from pysynth.patches.base import Patch
from pysynth.tempo import Tempo

# mostly small steps so the pitch glides rather than leaps
DRONE_INTERVALS = [0, -5, -3, 2, 0, -7, -5, 3]

DRONE_ROOT = 110  # A2, mid register between the bass (55) and the arp (220)


def build(tempo: Tempo, root_freq: float = DRONE_ROOT) -> Patch:
    """Slow-winding FM drone: note changes once every 8 bars, with a continuously drifting timbre."""
    # the drone changes note far more slowly than the bass (per 16th), arp (per
    # 8th), or either hat
    step_time = tempo.bar * 8

    # glides to each new frequency over most of the step time instead of snapping
    drone_freq = SigTo(value=root_freq, time=step_time * 0.9)

    # ratio and index each ride their own slow LFO, with periods measured in
    # whole drone steps, so the tone keeps evolving independently of pitch changes
    ratio_lfo = Sine(freq=1 / (step_time * 1.3), mul=0.2, add=1.5)
    index_lfo = Sine(freq=1 / (step_time * 0.7), mul=2, add=3)

    fm_voice = FM(carrier=drone_freq, ratio=ratio_lfo, index=index_lfo, mul=0.2)
    voice = Freeverb(fm_voice, size=0.9, damp=0.5, bal=0.45)

    step = {"i": 0}

    def next_step() -> None:
        i = step["i"] % len(DRONE_INTERVALS)
        drone_freq.value = root_freq * pow(2, DRONE_INTERVALS[i] / 12)
        step["i"] += 1

    sequencer = Pattern(next_step, time=step_time)
    return Patch(sequencer=sequencer, voice=voice)
