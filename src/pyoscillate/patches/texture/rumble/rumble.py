from __future__ import annotations

from pyo.lib.controls import SigTo
from pyo.lib.filters import MoogLP, Tone
from pyo.lib.generators import BrownNoise, Sine

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousSequencer
from pyoscillate.patches.params import PyoParamRef, SliderSpec

SUB_FREQ = 41  # E1, current default

PARAMETERS = (
    SliderSpec(
        "sub_freq",
        20,
        80,
        1,
        SUB_FREQ,
        "Register",
        "Sets the pitch of the faint sine layer under the rumble.",
        (PyoParamRef(Sine, "freq"),),
    ),
    SliderSpec(
        "sub_level",
        0,
        1,
        0.05,
        0.5,
        "Pitched weight",
        "Blends in a sense of pitch and grounding; higher makes the rumble feel more tonal, lower (or off) keeps it as pure unpitched texture.",
        (PyoParamRef(Sine, "mul"),),
    ),
    SliderSpec(
        "noise_level",
        0,
        1,
        0.05,
        0.5,
        "Rumble amount",
        "Sets how much of the filtered noise texture comes through - the main earthquake-like content of this patch.",
        (PyoParamRef(BrownNoise, "mul"),),
    ),
    SliderSpec(
        "noise_cutoff",
        40,
        300,
        5,
        90,
        "Rumble depth",
        "Sets how deep and dark the noise rumble sits; lower keeps only the deepest content, higher lets more mid-low texture through.",
        (PyoParamRef(MoogLP, "freq"),),
    ),
    SliderSpec(
        "tone_cutoff",
        100,
        1000,
        10,
        300,
        "Sine warmth",
        "Darkens or brightens the faint sine layer sitting under the noise.",
        (PyoParamRef(Tone, "freq"),),
    ),
)


def build(
    sub_freq: float = SUB_FREQ,
    sub_level: float = 0.5,
    noise_level: float = 0.5,
    noise_cutoff: float = 90,
    tone_cutoff: float = 300,
) -> Patch:
    """Textural noise rumble: `BrownNoise` through a very low lowpass, blended with a sub sine, for an unpitched "earthquake" low end rather than a tonal bass.

    Args:
        sub_freq: Frequency (Hz) of the sine layer underneath the noise -
            gives the rumble a faint sense of pitch/weight without making
            it read as a melodic bass note.
        sub_level: Level of the sine layer relative to the noise layer.
            Raising it makes the rumble feel more grounded and pitched;
            lowering it (or setting it to 0) makes the patch read as pure
            unpitched texture.
        noise_level: Level of the filtered noise layer - the main
            "rumbling" content of this patch.
        noise_cutoff: `MoogLP` cutoff (Hz) applied to the noise. Very low
            values (near the default) keep only the deepest rumble content
            and remove any hiss; raising it lets more mid-low texture
            through for a rougher, grittier rumble.
        tone_cutoff: `Tone` cutoff (Hz) applied to the sine layer, rounding
            off its edges so it blends into the noise rather than standing
            out as a clean tone.
    """
    live = {
        name: SigTo(value=value, time=0.15)
        for name, value in {
            "sub_freq": sub_freq,
            "sub_level": sub_level,
            "noise_level": noise_level,
            "noise_cutoff": noise_cutoff,
            "tone_cutoff": tone_cutoff,
        }.items()
    }
    noise = BrownNoise(mul=live["noise_level"])
    noise_voice = MoogLP(noise, freq=live["noise_cutoff"], res=0)
    sub = Sine(freq=live["sub_freq"], mul=live["sub_level"])
    sub_voice = Tone(sub, freq=live["tone_cutoff"])
    voice = noise_voice + sub_voice

    return Patch(
        sequencer=ContinuousSequencer(),
        voice=voice,
        controls={
            name: lambda value, control=control: setattr(control, "value", value)
            for name, control in live.items()
        },
        resources=(*live.values(), noise, noise_voice, sub, sub_voice),
    )
