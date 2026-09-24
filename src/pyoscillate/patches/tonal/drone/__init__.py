from __future__ import annotations

from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM, Sine

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.tempo import Tempo

# mostly small steps so the pitch glides rather than leaps
DRONE_INTERVALS = [0, -5, -3, 2, 0, -7, -5, 3]

DRONE_ROOT = 186  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        55,
        220,
        1,
        DRONE_ROOT,
        "Register",
        "Moves the drone's register; higher brings it closer to the arp and reads as more melodic, lower pushes it toward a sustained sub layer.",
        (PyoParamRef(FM, "carrier"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.7,
        "Space",
        "Sets how vast the drone's reverb tail feels, from a tighter presence to a huge, cavernous wash.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.7,
        "Tail darkness",
        "Controls how bright or muffled the reverb tail sounds as it decays; lower keeps it shimmering, higher makes it warmer and duller.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.9,
        "Distance",
        "Blends dry tone against reverb; higher dissolves the drone into a diffuse atmospheric bed, lower keeps the raw pitch more present.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
)


def build(
    tempo: Tempo,
    clock: Clock,
    root_freq: float = DRONE_ROOT,
    reverb_size: float = 0.7,
    reverb_damp: float = 0.7,
    reverb_bal: float = 0.9,
) -> Patch:
    """Slow-winding FM drone: note changes once every 8 bars, with a continuously drifting timbre.

    Args:
        tempo: Shared tempo grid; one drone step is `tempo.bar * 8`, and the
            ratio/index LFO periods are derived from that step time.
        clock: Shared master pulse; the drone steps every 8 bars
            (`clock.bar * 8`), phase-locked to every other patch on the clock.
        root_freq: Fundamental frequency (Hz) the drone glides between, before
            the `DRONE_INTERVALS` semitone offsets are applied each step.
            Raising it brings the drone closer to the arp's register and
            makes it easier to pick out as a melodic voice; lowering it
            moves it toward the bass and makes it read more as a sustained
            sub layer.
        reverb_size: Freeverb room size (0-1). Larger values give the drone a
            huge, cavernous decay that smears note changes into each other;
            smaller values keep each glide more distinct and present.
        reverb_damp: Freeverb high-frequency damping (0-1). The default is
            low (0.3) so the drone's reverb tail stays bright and shimmering
            rather than going dark and muffled; raise it for a warmer, more
            subdued wash.
        reverb_bal: Freeverb dry/wet balance (0 = fully dry, 1 = fully wet).
            The default is high (0.9) so the drone is heard almost entirely
            through the reverb, which is what makes it sit as a diffuse
            atmospheric bed rather than a distinct pitched voice; lowering
            it brings the raw FM tone forward.
    """
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
    voice = Freeverb(fm_voice, size=reverb_size, damp=reverb_damp, bal=reverb_bal)

    step = {"i": 0}

    def next_step() -> None:
        i = step["i"] % len(DRONE_INTERVALS)
        drone_freq.value = root_freq * pow(2, DRONE_INTERVALS[i] / 12)
        step["i"] += 1

    sequencer = clock.subscribe(clock.bar * 8, next_step)
    return Patch(
        sequencer=sequencer,
        voice=voice,
        controls={
            "root_freq": lambda value: setattr(drone_freq, "value", value),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        },
        resources=(drone_freq, ratio_lfo, index_lfo, fm_voice),
    )
