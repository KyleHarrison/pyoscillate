from __future__ import annotations

from ipywidgets import VBox
from pyo.lib.filters import ButHP
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

CUTOFF_FREQ = 10300

PARAMETERS = (
    SliderSpec(
        "cutoff_freq",
        2000,
        12000,
        100,
        CUTOFF_FREQ,
        "Brightness",
        "Moves the tick from fuller and more present (lower) to thinner, airier, and more distant-sounding (higher).",
        (PyoParamRef(ButHP, "freq"),),
    ),
    SliderSpec(
        "level",
        0,
        1,
        0.05,
        0.2,
        "Presence",
        "Sets how upfront the tick sits in the mix, from a subtle texture to a louder, more foregrounded pulse.",
        (PyoParamRef(Noise, "mul"),),
    ),
    SliderSpec(
        "decay",
        0.05,
        1,
        0.05,
        0.75,
        "Tightness",
        "Shapes the tick's tail; shorter feels tight and click-like, longer blurs into more of a hiss.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
)


def build(
    tempo: Tempo,
    clock: Clock,
    cutoff_freq: float = CUTOFF_FREQ,
    level: float = 0.2,
    decay: float = 0.75,
) -> Patch:
    """Subtle high-passed noise tick, once per 8th note, for top-end texture.

    Args:
        tempo: Shared tempo grid; the level swell is derived from
            `tempo.sixteenth`.
        clock: Shared master pulse; the hat ticks every 8th note
            (`clock.eighth`), phase-locked to every other patch on the clock.
        cutoff_freq: ButHP high-pass cutoff (Hz). Raising it strips away more
            low and mid content, making the tick thinner, more distant, and
            more "sizzly"; lowering it lets more body through, making the
            tick fatter and more present but less airy.
        level: Peak amplitude of the raw noise burst feeding the envelope,
            before the swell and high-pass are applied. Raising it makes
            the whole hat louder and more upfront in the mix; lowering it
            pushes it further back as a subtle texture.
        decay: Length (seconds) of the tick's amplitude envelope. Shorter
            values give a tighter, click-like tick; longer values let it
            decay into more of a hiss, blurring the individual 8th notes
            together.
    """
    hat_trig = Trig()
    hat_noise = Noise(mul=level)

    # short, tight envelope so the hat ticks rather than hisses
    envelope_table = CosTable([(0, 0), (30, 1), (800, 0)])
    hat_env = TrigEnv(hat_trig, table=envelope_table, dur=decay, mul=hat_noise)

    # slow swell over 32 steps so the ticks don't sit at a fixed level
    hat_swell = Sine(freq=1 / (32 * tempo.sixteenth), mul=0.3, add=0.8)

    # high-pass to keep it thin and airy, not a full noise burst
    voice = ButHP(hat_env, freq=cutoff_freq, mul=hat_swell, add=-0.2)

    sequencer = clock.subscribe(clock.eighth, hat_trig.play)
    return Patch(
        sequencer=sequencer,
        voice=voice,
        controls={
            "cutoff_freq": lambda value: setattr(voice, "freq", value),
            "level": lambda value: setattr(hat_noise, "mul", value),
        },
        resources=(hat_trig, hat_noise, envelope_table, hat_env, hat_swell),
    )


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
) -> VBox:
    """Create hi-hat controls."""
    return patch_widget(
        rack,
        "hat",
        build,
        PARAMETERS,
        controller=controller,
        volume_default=0.2,
        rebuild_parameters=("decay",),
        build_kwargs={"tempo": tempo, "clock": clock},
    )
