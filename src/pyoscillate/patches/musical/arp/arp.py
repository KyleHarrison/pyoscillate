# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.arp.arp
from __future__ import annotations

from typing import Any, ClassVar

from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

# major pentatonic - consonant, calm, no leading tones to create tension
MID_INTERVALS = [0, 2, 4, 7, 9, 12, 9, 7, 4, 2]

MID_ROOT = notes.E4  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A2,
        notes.E5,
        1,
        MID_ROOT,
        "Register",
        "Shifts the melody up or down in pitch relative to the pads and bass beneath it.",
        (PyoParamRef(FM, "carrier"),),
        scale="note",
    ),
    SliderSpec(
        "step_bars",
        1,
        8,
        1,
        2,
        "Pace",
        "Sets how often the melody moves; fewer bars feels more active, more bars stretches it into a slower, more spacious unfolding.",
        (),
    ),
    SliderSpec(
        "fm_ratio",
        0.5,
        4,
        0.1,
        1.5,
        "Tone character",
        "Detunes the melody's overtones; near a simple ratio sounds clean and bell-like, drifting away adds a warmer, more unstable shimmer.",
        (PyoParamRef(FM, "ratio"),),
    ),
    SliderSpec(
        "fm_index",
        0,
        6,
        0.1,
        1.5,
        "Brightness",
        "Moves the melody from a plain, mellow tone to a brighter, buzzier, more harmonically complex one.",
        (PyoParamRef(FM, "index"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.6,
        "Space",
        "Sets how large and distant the melody's room feels, from a tight presence to a huge, cavernous decay.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.5,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower settings stay bright and shimmering.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.4,
        "Distance",
        "Blends how much of the melody is heard through the reverb versus dry; higher dissolves it into the atmosphere, lower keeps it present and up front.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
)


VOLUME_DEFAULT = 0.6


class Arp(Patch):
    """Slow, fixed pentatonic arpeggio locked to the shared clock, gliding between notes rather than plucking them.

    `step_bars` is a `rebuild_parameters` entry: it sets the `SigTo` glide
    time and the clock division at build time, so changing it live can't
    just update an existing control - the graph has to be rebuilt.
    """

    name = "mid_arp"
    title = "Mid - slow pentatonic arpeggio"
    summary = "Calm, consonant melodic line locked to the groove."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    rebuild_parameters: ClassVar[tuple[str, ...]] = ("step_bars",)
    needs_tempo: ClassVar[bool] = True
    needs_clock: ClassVar[bool] = True

    root_freq: float
    step_bars: int
    fm_ratio: float
    fm_index: float
    reverb_size: float
    reverb_damp: float
    reverb_bal: float

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        self.configure(**values)
        step_time = tempo.bar * self.step_bars

        # glides to each new note over most of the step time instead of
        # snapping, so the melody drifts between pitches rather than
        # plucking them
        mid_freq = SigTo(value=self.root_freq, time=step_time * 0.85)

        fm_voice = FM(carrier=mid_freq, ratio=self.fm_ratio, index=self.fm_index, mul=0.18)
        voice = Freeverb(fm_voice, size=self.reverb_size, damp=self.reverb_damp, bal=self.reverb_bal)

        root_freq = self.root_freq
        step = {"i": 0}

        def next_step() -> None:
            i = step["i"] % len(MID_INTERVALS)
            mid_freq.value = root_freq * pow(2, MID_INTERVALS[i] / 12)
            step["i"] += 1

        self.sequencer = clock.subscribe(clock.bar * self.step_bars, next_step)
        self.voice = voice
        self.controls = {
            "root_freq": lambda value: setattr(mid_freq, "value", value),
            "fm_ratio": lambda value: setattr(fm_voice, "ratio", value),
            "fm_index": lambda value: setattr(fm_voice, "index", value),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        }
        self.resources = [mid_freq, fm_voice]
        return self
