# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.wash
from __future__ import annotations

from typing import Any

from pyo.lib.effects import Chorus, Delay, Freeverb
from pyo.lib.generators import Rossler, SuperSaw

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousVoice
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes

ROOT_FREQ = notes.E3  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A1,
        notes.A4,
        1,
        ROOT_FREQ,
        "Register",
        "Sets the wash's base pitch.",
        scale="note",
    ),
    SliderSpec(
        "detune",
        0,
        1,
        0.05,
        0.6,
        "Thickness",
        "Spreads the oscillators apart in pitch; higher makes the wash thicker and hazier, lower keeps it cleaner and more focused.",
    ),
    SliderSpec(
        "detune_bal",
        0,
        1,
        0.05,
        0.7,
        "Detune blend",
        "Balances how much of the detuned layers come through versus the centered tone; higher leans further into the thick, chorused character.",
    ),
    SliderSpec(
        "pitch_drift",
        0,
        1,
        0.01,
        0.03,
        "Instability",
        "Adds slow pitch wobble; higher makes the wash feel more alive and unstable, lower keeps it steadier.",
    ),
    SliderSpec(
        "chorus_depth",
        0,
        5,
        0.1,
        2.5,
        "Shimmer",
        "Deepens the chorus modulation for a wider, more shimmering movement; lower keeps it subtler and more static.",
    ),
    SliderSpec(
        "chorus_feedback",
        0,
        1,
        0.05,
        0.35,
        "Chorus density",
        "Adds more layered repeats to the chorus effect for a denser, more swirling texture.",
    ),
    SliderSpec(
        "chorus_bal",
        0,
        1,
        0.05,
        0.6,
        "Chorus blend",
        "Blends how much of the chorused signal is heard versus the dry tone; higher leans further into the wide, shimmering effect.",
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.9,
        "Space",
        "Sets how large and distant the wash's room feels, from a tight presence to a huge, cavernous decay.",
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.35,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower settings stay bright and shimmering.",
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.9,
        "Distance",
        "Blends how much of the wash is heard through the reverb versus dry; higher dissolves it into the atmosphere, lower keeps it present.",
    ),
    SliderSpec(
        "delay_time",
        0.05,
        2,
        0.05,
        0.8,
        "Echo spacing",
        "Sets the time between echo repeats, smearing the wash across time.",
    ),
    SliderSpec(
        "delay_feedback",
        0,
        0.9,
        0.05,
        0.25,
        "Echo density",
        "Sets how many times each echo repeats before fading; higher creates a denser, more layered wash.",
    ),
)
VOLUME_DEFAULT = 0.6


class SoundscapeWash(ContinuousVoice):
    """Washy detuned pad: a SuperSaw voice smeared with chorus, reverb, and delay for a shoegaze-style dream-pop ambience.

    Unlike `SoundscapeFm`/`SoundscapeFilter`, the "evolving" quality here
    comes mostly from spatial smear (chorus/reverb/delay) rather than
    timbral or filter movement - the character is width and haze rather
    than wander.
    """

    title = "Soundscape - washy detuned pad"
    summary = "Wide, hazy detuned wash that dissolves into echoing space."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    root_freq: float
    detune: float
    detune_bal: float
    pitch_drift: float
    chorus_depth: float
    chorus_feedback: float
    chorus_bal: float
    reverb_size: float
    reverb_damp: float
    reverb_bal: float
    delay_time: float
    delay_feedback: float

    def build(self, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        live = self.live_all(
            "root_freq",
            "detune",
            "detune_bal",
            "pitch_drift",
            "chorus_depth",
            "chorus_feedback",
            "chorus_bal",
            "reverb_size",
            "reverb_damp",
            "reverb_bal",
            "delay_time",
            "delay_feedback",
        )

        # subtle, slow pitch instability rather than a discrete note pattern -
        # keeps the pad "dreamy" without ever resolving to a new pitch
        pitch_wander = Rossler(
            pitch=0.02, chaos=0.4, mul=live["pitch_drift"], add=live["root_freq"]
        )

        saw_voice = SuperSaw(
            freq=pitch_wander, detune=live["detune"], bal=live["detune_bal"], mul=0.2
        )
        chorused = Chorus(
            saw_voice,
            depth=live["chorus_depth"],
            feedback=live["chorus_feedback"],
            bal=live["chorus_bal"],
        )
        reverb_voice = Freeverb(
            chorused,
            size=live["reverb_size"],
            damp=live["reverb_damp"],
            bal=live["reverb_bal"],
        )
        voice = Delay(
            reverb_voice,
            delay=live["delay_time"],
            feedback=live["delay_feedback"],
            maxdelay=2,
        )
        self.retain(pitch_wander, saw_voice, chorused, reverb_voice)
        return self.finish(voice)
