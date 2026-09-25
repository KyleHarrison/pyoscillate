# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.texture.rumble.rumble
from __future__ import annotations

from typing import Any

from pyo.lib.filters import MoogLP, Tone
from pyo.lib.generators import BrownNoise, Sine

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousVoice
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes

SUB_FREQ = notes.E1  # current default

PARAMETERS = (
    SliderSpec(
        "sub_freq",
        20,
        80,
        1,
        SUB_FREQ,
        "Register",
        "Sets the pitch of the faint sine layer under the rumble.",
    ),
    SliderSpec(
        "sub_level",
        0,
        1,
        0.05,
        0.5,
        "Pitched weight",
        "Blends in a sense of pitch and grounding; higher makes the rumble feel more tonal, lower (or off) keeps it as pure unpitched texture.",
    ),
    SliderSpec(
        "noise_level",
        0,
        1,
        0.05,
        0.5,
        "Rumble amount",
        "Sets how much of the filtered noise texture comes through - the main earthquake-like content of this patch.",
    ),
    SliderSpec(
        "noise_cutoff",
        40,
        300,
        5,
        90,
        "Rumble depth",
        "Sets how deep and dark the noise rumble sits; lower keeps only the deepest content, higher lets more mid-low texture through.",
    ),
    SliderSpec(
        "tone_cutoff",
        100,
        1000,
        10,
        300,
        "Sine warmth",
        "Darkens or brightens the faint sine layer sitting under the noise.",
    ),
)
VOLUME_DEFAULT = 0.8


class BassRumble(ContinuousVoice):
    """Textural noise rumble: `BrownNoise` through a very low lowpass, blended with a sub sine, for an unpitched "earthquake" low end rather than a tonal bass."""

    title = "Bass - textural noise rumble"
    summary = "Unpitched, earthquake-like low-end texture."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    sub_freq: float
    sub_level: float
    noise_level: float
    noise_cutoff: float
    tone_cutoff: float

    def build(self, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        live = self.live_all("sub_freq", "sub_level", "noise_level", "noise_cutoff", "tone_cutoff")

        noise = BrownNoise(mul=live["noise_level"])
        noise_voice = MoogLP(noise, freq=live["noise_cutoff"], res=0)
        sub = Sine(freq=live["sub_freq"], mul=live["sub_level"])
        sub_voice = Tone(sub, freq=live["tone_cutoff"])
        voice = noise_voice + sub_voice
        self.retain(noise, noise_voice, sub, sub_voice)
        return self.finish(voice)
