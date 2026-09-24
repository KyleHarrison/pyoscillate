from __future__ import annotations

from ipywidgets import VBox
from pyo.lib._core import Sig
from pyo.lib.filters import ButHP, ButLP
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import ExpTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

CUTOFF_FREQ = 3000  # lower than the main hat (10300) so this reads as a darker, lower accent
DECAY = 0.12
BASE_DIVISION = NoteDivision.QUARTER
# the top-end roll-off tracks the high-pass at this ratio, keeping the voice
# a darker band of noise rather than a full-range hiss with the lows removed
TOP_RATIO = 3.0
DECAY_CURVE = 5

PARAMETERS = (
    SliderSpec(
        "cutoff_freq",
        1000,
        6000,
        100,
        CUTOFF_FREQ,
        "Darkness",
        "Sets how dark and low this accent sits against the main hat; lower is closer to a thud, higher brightens it toward the main hat's character.",
        (PyoParamRef(ButHP, "freq"), PyoParamRef(ButLP, "freq")),
    ),
    SliderSpec(
        "level",
        0,
        1,
        0.05,
        0.55,
        "Presence",
        "Controls how prominent this accent is against the main hat.",
        (PyoParamRef(TrigEnv, "mul"),),
    ),
    SliderSpec(
        "decay",
        0.03,
        0.6,
        0.01,
        DECAY,
        "Tail length",
        "Shapes the accent's decay; shorter feels tight and clipped, longer trails into a dubbier tock.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the accent pattern speed for each step away from its quarter-note grid.",
    ),
)


def build(
    tempo: Tempo,
    clock: Clock,
    cutoff_freq: float = CUTOFF_FREQ,
    level: float = 0.55,
    decay: float = DECAY,
    rate: float = 0,
) -> Patch:
    """Darker noise tick, once per quarter note, as a rarer, dubbier accent.

    Args:
        tempo: Shared tempo grid; the level swell is derived from
            `tempo.eighth`.
        clock: Shared master pulse; the tick fires every quarter note
            (`clock.fourth`), phase-locked to every other patch on the clock.
        cutoff_freq: Lower edge (Hz) of the noise band; the upper edge
            follows at `TOP_RATIO` times this. The default (3000) is much
            lower than the main hat's (10300), which keeps more lower-mid
            body and less air, so this voice reads as darker and closer.
            Raising it brings it toward the main hat in character; lowering
            it further makes it darker and closer to a low thud than a hiss.
        level: Peak amplitude of each noise burst, before the swell and
            filters are applied. Raising it makes this accent louder and
            more prominent against the main hat; lowering it keeps it as a
            subtler undercurrent.
        decay: Length (seconds) of the tick's exponential amplitude decay.
            Keep it short for a tight, clipped accent, or lengthen it for a
            longer decaying tock.
    """
    hat_trig = Trig()
    hat_noise = Noise()

    # same immediate, strongly exponential envelope shape as the main hat
    envelope_table = ExpTable([(0, 1), (8191, 0)], exp=DECAY_CURVE)
    hat_env = TrigEnv(hat_trig, table=envelope_table, dur=decay, mul=level)
    hat_burst = hat_noise * hat_env

    hat_swell = Sine(freq=1 / (32 * tempo.eighth), mul=0.3, add=0.8)

    # a gentler high-pass than the main hat keeps lower-mid body while still
    # clearing the kick and bass; the linked low-pass removes the airy top
    low_edge = Sig(cutoff_freq)
    high_edge = low_edge * TOP_RATIO
    body = ButHP(hat_burst, freq=low_edge)
    voice = ButLP(body, freq=high_edge, mul=hat_swell)

    sequencer = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), hat_trig.play)
    return Patch(
        sequencer=sequencer,
        voice=voice,
        controls={
            "cutoff_freq": lambda value: setattr(low_edge, "value", value),
            "level": lambda value: setattr(hat_env, "mul", value),
            "decay": lambda value: setattr(hat_env, "dur", value),
            "rate": lambda value: setattr(
                sequencer, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        },
        resources=(
            hat_trig,
            hat_noise,
            envelope_table,
            hat_env,
            hat_burst,
            hat_swell,
            low_edge,
            high_edge,
            body,
        ),
    )


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
) -> VBox:
    """Create low-hat controls."""
    return patch_widget(
        rack,
        "low_hat",
        build,
        PARAMETERS,
        controller=controller,
        volume_default=0.2,
        build_kwargs={"tempo": tempo, "clock": clock},
    )
