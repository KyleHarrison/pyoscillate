from __future__ import annotations

from ipywidgets import VBox
from pyo.lib.controls import SigTo
from pyo.lib.filters import MoogLP, Tone
from pyo.lib.generators import BrownNoise, Sine

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.psyambient.common import ContinuousSequencer
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget

SUB_FREQ = 41  # E1, current notebook default

PARAMETERS = (
    SliderSpec(
        "sub_freq",
        20,
        80,
        1,
        SUB_FREQ,
        "Sub frequency",
        "Frequency of the sine layer.",
        (PyoParamRef(Sine, "freq"),),
    ),
    SliderSpec(
        "sub_level",
        0,
        1,
        0.05,
        0.5,
        "Sub level",
        "Level of the sine layer.",
        (PyoParamRef(Sine, "mul"),),
    ),
    SliderSpec(
        "noise_level",
        0,
        1,
        0.05,
        0.5,
        "Noise level",
        "Level of the filtered noise.",
        (PyoParamRef(BrownNoise, "mul"),),
    ),
    SliderSpec(
        "noise_cutoff",
        40,
        300,
        5,
        90,
        "Noise cutoff",
        "Lowpass cutoff for the noise.",
        (PyoParamRef(MoogLP, "freq"),),
    ),
    SliderSpec(
        "tone_cutoff",
        100,
        1000,
        10,
        300,
        "Tone cutoff",
        "Lowpass cutoff for the sine layer.",
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
    noise_voice = MoogLP(BrownNoise(mul=live["noise_level"]), freq=live["noise_cutoff"], res=0)
    sub_voice = Tone(Sine(freq=live["sub_freq"], mul=live["sub_level"]), freq=live["tone_cutoff"])
    voice = noise_voice + sub_voice

    return Patch(
        sequencer=ContinuousSequencer(),
        voice=voice,
        controls={
            name: lambda value, control=control: setattr(control, "value", value)
            for name, control in live.items()
        },
    )


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create bass_rumble controls."""
    return patch_widget(
        rack,
        "bass_rumble",
        build,
        PARAMETERS,
        controller=controller,
        volume_default=0.8,
    )
