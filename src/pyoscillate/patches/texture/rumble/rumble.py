# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.texture.rumble.rumble
"""Textural noise rumble: `BrownNoise` through a very low lowpass, blended
with a sub sine, for an unpitched "earthquake" low end rather than a tonal
bass.
"""

from __future__ import annotations

from pyo import PyoObject
from pyo.lib.filters import MoogLP, Tone
from pyo.lib.generators import BrownNoise, Sine

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice, Gate
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes

SUB_FREQ = notes.E1  # current default


class BassRumble(Gate, ContinuousVoice):
    """Textural noise rumble: `BrownNoise` through a very low lowpass, blended with a sub sine, for an unpitched "earthquake" low end rather than a tonal bass."""

    title = "Bass - textural noise rumble"
    summary = "Unpitched, earthquake-like low-end texture."
    volume = Patch.volume.replace(default=0.8)

    noise: BrownNoise
    noise_voice: MoogLP
    sub: Sine
    sub_voice: Tone
    mixed: PyoObject

    sub_freq = Param(
        20,
        80,
        1,
        SUB_FREQ,
        "Register",
        "Sets the pitch of the faint sine layer under the rumble.",
    )
    sub_level = Param(
        0,
        1,
        0.05,
        0.5,
        "Pitched weight",
        "Blends in a sense of pitch and grounding; higher makes the rumble feel more tonal, lower (or "
        "off) keeps it as pure unpitched texture.",
        sweep=True,
    )
    noise_level = Param(
        0,
        1,
        0.05,
        0.5,
        "Rumble amount",
        "Sets how much of the filtered noise texture comes through - the main earthquake-like content "
        "of this patch.",
        sweep=True,
    )
    noise_cutoff = Param(
        40,
        300,
        5,
        90,
        "Rumble depth",
        "Sets how deep and dark the noise rumble sits; lower keeps only the deepest content, higher "
        "lets more mid-low texture through.",
        sweep=True,
    )
    tone_cutoff = Param(
        100,
        1000,
        10,
        300,
        "Sine warmth",
        "Darkens or brightens the faint sine layer sitting under the noise.",
        sweep=True,
    )

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        cls = type(self)

        self.noise = BrownNoise(mul=self.live(cls.noise_level))
        self.noise_voice = MoogLP(self.noise, freq=self.live(cls.noise_cutoff), res=0)
        self.sub = Sine(freq=self.live(cls.sub_freq), mul=self.live(cls.sub_level))
        self.sub_voice = Tone(self.sub, freq=self.live(cls.tone_cutoff))
        self.mixed = self.noise_voice + self.sub_voice
        return self.finish(self.add_gate(self.mixed, context))
