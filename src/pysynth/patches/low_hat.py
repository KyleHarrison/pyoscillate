from __future__ import annotations

from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox, interactive_output
from pyo.lib.filters import ButHP
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pysynth.clock import FOURTH, Clock
from pysynth.patches.base import Patch, PatchRack
from pysynth.tempo import Tempo

CUTOFF_FREQ = 3000  # lower than the main hat (8000) so this reads as a darker, lower accent


def build(
    tempo: Tempo,
    clock: Clock,
    cutoff_freq: float = CUTOFF_FREQ,
    level: float = 0.55,
    decay: float = 0.25,
) -> Patch:
    """Darker noise tick, once per quarter note, as a rarer, dubbier accent.

    Args:
        tempo: Shared tempo grid; the level swell is derived from
            `tempo.eighth`.
        clock: Shared master pulse; the tick fires every quarter note
            (`FOURTH`), phase-locked to every other patch on the clock.
        cutoff_freq: ButHP high-pass cutoff (Hz). The default (3000) is much
            lower than the main hat's (8000), which is what makes this
            voice read as darker and lower. Raising it brings it closer to
            the main hat in character; lowering it further makes it darker
            and closer to a low thud than a hiss.
        level: Peak amplitude of the raw noise burst feeding the envelope,
            before the swell and high-pass are applied. Raising it makes
            this accent louder and more prominent against the main hat;
            lowering it keeps it as a subtler undercurrent.
        decay: Length (seconds) of the tick's amplitude envelope. The
            default (0.5) is longer than the main hat's (0.2), giving it
            more of a dubby tail; shorten it for a tighter, more clipped
            accent, or lengthen it for a longer decaying tock.
    """
    hat_trig = Trig()
    hat_noise = Noise(mul=level)

    # same short, tight envelope shape as the main hat
    envelope_table = CosTable([(0, 0), (30, 1), (800, 0)])
    hat_env = TrigEnv(hat_trig, table=envelope_table, dur=decay, mul=hat_noise)

    hat_swell = Sine(freq=1 / (32 * tempo.eighth), mul=0.3, add=0.8)

    voice = ButHP(hat_env, freq=cutoff_freq, mul=hat_swell, add=-0.2)

    sequencer = clock.subscribe(FOURTH, hat_trig.play)
    return Patch(sequencer=sequencer, voice=voice)


def widget(rack: PatchRack, tempo: Tempo, clock: Clock) -> VBox:
    """Create low-hat controls with parameter descriptions beside each slider."""

    def set_params(enabled, cutoff_freq, level, decay, volume):
        if not enabled:
            rack.stop("low_hat")
            return

        low_hat_patch = build(tempo, clock, cutoff_freq, level, decay)
        low_hat_patch.volume = volume
        rack.start("low_hat", low_hat_patch)

    enabled = Checkbox(value=False, description="low hat on/off")
    cutoff_freq = FloatSlider(
        min=1000, max=6000, step=100, value=CUTOFF_FREQ, description="cutoff_freq"
    )
    level = FloatSlider(min=0, max=1, step=0.05, value=0.55, description="level")
    decay = FloatSlider(min=0.05, max=1, step=0.05, value=0.25, description="decay")
    volume = FloatSlider(min=0, max=2, step=0.1, value=0.2, description="volume")

    output = interactive_output(
        set_params,
        {
            "enabled": enabled,
            "cutoff_freq": cutoff_freq,
            "level": level,
            "decay": decay,
            "volume": volume,
        },
    )
    slider_rows = [
        HBox([cutoff_freq, HTML("High-pass cutoff - lower than the main hat for a darker tone.")]),
        HBox([level, HTML("Loudness of the raw noise burst before shaping.")]),
        HBox([decay, HTML("Envelope length - longer than the main hat for a dubbier tail.")]),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
