from __future__ import annotations

from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox, interactive_output
from pyo.lib.filters import MoogLP, Tone
from pyo.lib.generators import BrownNoise, Sine

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.psyambient.common import ContinuousSequencer

SUB_FREQ = 41  # E1, current notebook default


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
    noise_voice = MoogLP(BrownNoise(mul=noise_level), freq=noise_cutoff, res=0)
    sub_voice = Tone(Sine(freq=sub_freq, mul=sub_level), freq=tone_cutoff)
    voice = noise_voice + sub_voice

    return Patch(sequencer=ContinuousSequencer(), voice=voice)


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create bass_rumble controls with parameter descriptions beside each slider."""

    def set_params(enabled, sub_freq, sub_level, noise_level, noise_cutoff, tone_cutoff, volume):
        if controller is not None and controller.applying:
            return
        if not enabled:
            rack.stop("bass_rumble")
            return

        patch = build(sub_freq, sub_level, noise_level, noise_cutoff, tone_cutoff)
        patch.volume = volume
        rack.start("bass_rumble", patch)

    enabled = Checkbox(value=False, description="bass_rumble on/off")
    sub_freq = FloatSlider(min=20, max=80, step=1, value=SUB_FREQ, description="sub_freq")
    sub_level = FloatSlider(min=0, max=1, step=0.05, value=0.5, description="sub_level")
    noise_level = FloatSlider(min=0, max=1, step=0.05, value=0.5, description="noise_level")
    noise_cutoff = FloatSlider(min=40, max=300, step=5, value=90, description="noise_cutoff")
    tone_cutoff = FloatSlider(min=100, max=1000, step=10, value=300, description="tone_cutoff")
    volume = FloatSlider(min=0, max=2, step=0.1, value=0.8, description="volume")

    controls = {
        "enabled": enabled,
        "sub_freq": sub_freq,
        "sub_level": sub_level,
        "noise_level": noise_level,
        "noise_cutoff": noise_cutoff,
        "tone_cutoff": tone_cutoff,
        "volume": volume,
    }
    if controller is not None:
        controller.register(
            "bass_rumble",
            controls,
            lambda: set_params(**{name: widget.value for name, widget in controls.items()}),
        )

    output = interactive_output(set_params, controls)
    slider_rows = [
        HBox([sub_freq, HTML("Frequency of the faint sine layer under the noise.")]),
        HBox(
            [sub_level, HTML("Level of the sine layer - higher feels more grounded and pitched.")]
        ),
        HBox([noise_level, HTML("Level of the filtered noise layer - the main rumbling content.")]),
        HBox([noise_cutoff, HTML("Noise lowpass cutoff - lower keeps only the deepest rumble.")]),
        HBox(
            [
                tone_cutoff,
                HTML("Sine layer lowpass cutoff - rounds it off to blend with the noise."),
            ]
        ),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
