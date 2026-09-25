# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone
from __future__ import annotations

from typing import Any, ClassVar

from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM, Sine

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

# mostly small steps so the pitch glides rather than leaps
DRONE_INTERVALS = [0, -5, -3, 2, 0, -7, -5, 3]

DRONE_ROOT = notes.Fs3  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A1,
        notes.A3,
        1,
        DRONE_ROOT,
        "Register",
        "Moves the drone's register; higher brings it closer to the arp and reads as more melodic, lower pushes it toward a sustained sub layer.",
        (PyoParamRef(FM, "carrier"),),
        scale="note",
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


VOLUME_DEFAULT = 1.0


class Drone(Patch):
    """Slow-winding FM drone: note changes once every 8 bars, with a continuously drifting timbre."""

    title = "Drone"
    summary = "Slow-winding sustained drone that rarely changes note."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    needs_tempo: ClassVar[bool] = True
    needs_clock: ClassVar[bool] = True

    root_freq: float
    reverb_size: float
    reverb_damp: float
    reverb_bal: float

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        self.configure(**values)
        # the drone changes note far more slowly than the bass (per 16th),
        # arp (per 8th), or either hat
        step_time = tempo.bar * 8

        # glides to each new frequency over most of the step time instead of snapping
        drone_freq = SigTo(value=self.root_freq, time=step_time * 0.9)

        # ratio and index each ride their own slow LFO, with periods measured in
        # whole drone steps, so the tone keeps evolving independently of pitch changes
        ratio_lfo = Sine(freq=1 / (step_time * 1.3), mul=0.2, add=1.5)
        index_lfo = Sine(freq=1 / (step_time * 0.7), mul=2, add=3)

        fm_voice = FM(carrier=drone_freq, ratio=ratio_lfo, index=index_lfo, mul=0.2)
        voice = Freeverb(fm_voice, size=self.reverb_size, damp=self.reverb_damp, bal=self.reverb_bal)

        root_freq = self.root_freq
        step = {"i": 0}

        def next_step() -> None:
            i = step["i"] % len(DRONE_INTERVALS)
            drone_freq.value = root_freq * pow(2, DRONE_INTERVALS[i] / 12)
            step["i"] += 1

        self.sequencer = clock.subscribe(clock.bar * 8, next_step)
        self.voice = voice
        self.controls = {
            "root_freq": lambda value: setattr(drone_freq, "value", value),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        }
        self.resources = [drone_freq, ratio_lfo, index_lfo, fm_voice]
        return self
