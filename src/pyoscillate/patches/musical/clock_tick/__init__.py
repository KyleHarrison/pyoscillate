from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ipywidgets import VBox
from pyo.lib.filters import ButBP, ButHP, ButLP
from pyo.lib.generators import Noise
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

OVERALL_LEVEL = 0.5  # background texture, not a groove element - keep it low in the mix

PARAMETERS = (
    SliderSpec(
        "level",
        0,
        1,
        0.05,
        OVERALL_LEVEL,
        "Presence",
        "Sets how far forward the clock-shop texture sits in the mix, from a background murmur to a foreground element.",
        (),
    ),
    SliderSpec(
        "wood_q",
        1,
        10,
        0.5,
        3,
        "Wood tone",
        "Focuses the woodblock tock around a single pitch for a more tonal, ringing sound, or widens it into a duller, more percussive thud.",
        (PyoParamRef(ButBP, "q"),),
    ),
    SliderSpec(
        "glass_q",
        1,
        15,
        0.5,
        6,
        "Glass tone",
        "Focuses the metallic tick around a single ringing pitch, or widens it into a softer, less metallic click.",
        (PyoParamRef(ButBP, "q"),),
    ),
)


@dataclass
class _Clocks:
    """Fans play()/stop() out over several independent Metros, so one Patch
    can drive multiple free-running clocks that never share a downbeat.

    Also holds a strong reference to every intermediate pyo object built
    for the four voices (envelope table, TrigEnvs, filtered voices) via
    `keepalive`, not just the summed `voice` chain and the Metros. In
    isolation the summed chain's own internal references were enough to
    keep everything alive; alongside another `Pattern`-driven callback (as
    used by `Clock`, which every other patch ticks from) those same locals
    would intermittently get torn down mid-callback and crash the process
    with a segfault, or silently stop ticking. Keeping direct strong
    references here, rather than relying on the chain, closes that off.
    """

    metros: list[Metro]
    keepalive: list[Any] = field(default_factory=list)

    def play(self) -> None:
        for metro in self.metros:
            metro.play()

    def stop(self) -> None:
        for metro in self.metros:
            metro.stop()


def build(
    tempo: Tempo,
    level: float = OVERALL_LEVEL,
    wood_q: float = 3,
    glass_q: float = 6,
) -> Patch:
    """Pink Floyd "Time"-style clock shop: four noise ticks, each on its own
    free-running period measured in real seconds rather than the tempo grid.
    Like a room of clocks that were never wound together, they drift past
    each other instead of locking into the groove or into each other.

    Args:
        tempo: Unused - this patch is deliberately free-running in real
            seconds rather than locked to the tempo grid, so all four clocks
            drift in and out of phase with the beat instead of syncing to
            it.
        level: Overall output level applied to the summed four voices.
            Raising it brings the clock shop forward as a foreground
            texture; the low default keeps it a background element that
            only becomes noticeable in the gaps between other patches.
        wood_q: ButBP resonance (Q) of the woodblock-ish tock. Higher values
            narrow the band around 500 Hz, making the tock ring more at a
            single pitch (more tonal, more "block"-like); lower values
            widen the band for a duller, more percussive thud.
        glass_q: ButBP resonance (Q) of the thin metallic escapement tick.
            Higher values narrow the band around 4200 Hz for a more
            pronounced, ringing glassy pitch; lower values widen it for a
            softer, less metallic click.
    """
    del tempo  # deliberately free-running, not tied to the tempo grid

    # same short, tight click shape used by the other hats - a tick, not a hiss
    tick_envelope = CosTable([(0, 0), (20, 1), (400, 0)])

    metros: list[Metro] = []
    keepalive: list[Any] = [tick_envelope]

    # bright, thin wristwatch tick - fastest and quietest of the four
    bright_metro = Metro(time=0.63)
    metros.append(bright_metro)
    bright_noise = Noise(mul=0.3)
    bright_env = TrigEnv(bright_metro, table=tick_envelope, dur=0.05, mul=bright_noise)
    bright_voice = ButHP(bright_env, freq=6500)
    keepalive += [bright_noise, bright_env, bright_voice]

    # woodblock-ish tock - band-passed around a low-mid resonance
    wood_metro = Metro(time=0.97)
    metros.append(wood_metro)
    wood_noise = Noise(mul=0.4)
    wood_env = TrigEnv(wood_metro, table=tick_envelope, dur=0.1, mul=wood_noise)
    wood_voice = ButBP(wood_env, freq=500, q=wood_q)
    keepalive += [wood_noise, wood_env, wood_voice]

    # deep pendulum tock - warm, longer decay, the slowest of the four
    deep_metro = Metro(time=1.58)
    metros.append(deep_metro)
    deep_noise = Noise(mul=0.45)
    deep_env = TrigEnv(deep_metro, table=tick_envelope, dur=0.2, mul=deep_noise)
    deep_voice = ButLP(deep_env, freq=350)
    keepalive += [deep_noise, deep_env, deep_voice]

    # thin metallic tick - like a mantel clock's escapement, rarer and brighter
    glass_metro = Metro(time=2.44)
    metros.append(glass_metro)
    glass_noise = Noise(mul=0.3)
    glass_env = TrigEnv(glass_metro, table=tick_envelope, dur=0.06, mul=glass_noise)
    glass_voice = ButBP(glass_env, freq=4200, q=glass_q)
    keepalive += [glass_noise, glass_env, glass_voice]

    source = bright_voice + wood_voice + deep_voice + glass_voice
    keepalive.append(source)
    voice = source * level
    sequencer = _Clocks(metros=metros, keepalive=keepalive)
    return Patch(
        sequencer=sequencer,
        voice=voice,
        controls={
            "level": lambda value: setattr(voice, "mul", value),
            "wood_q": lambda value: setattr(wood_voice, "q", value),
            "glass_q": lambda value: setattr(glass_voice, "q", value),
        },
        resources=tuple(keepalive),
    )


def widget(rack: PatchRack, tempo: Tempo, controller: PresetController | None = None) -> VBox:
    """Create clock-tick controls."""
    return patch_widget(
        rack,
        "clock_tick",
        build,
        PARAMETERS,
        controller=controller,
        build_kwargs={"tempo": tempo},
    )
