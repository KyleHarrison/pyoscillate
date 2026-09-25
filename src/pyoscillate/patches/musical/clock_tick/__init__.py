# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.clock_tick
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from pyo.lib.filters import ButBP, ButHP, ButLP
from pyo.lib.generators import Noise
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv

from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
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
    ),
    SliderSpec(
        "wood_q",
        1,
        10,
        0.5,
        3,
        "Wood tone",
        "Focuses the woodblock tock around a single pitch for a more tonal, ringing sound, or widens it into a duller, more percussive thud.",
    ),
    SliderSpec(
        "glass_q",
        1,
        15,
        0.5,
        6,
        "Glass tone",
        "Focuses the metallic tick around a single ringing pitch, or widens it into a softer, less metallic click.",
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


VOLUME_DEFAULT = 1.0


class ClockTick(Patch):
    """Pink Floyd "Time"-style clock shop: four noise ticks, each on its own
    free-running period measured in real seconds rather than the tempo grid.
    Like a room of clocks that were never wound together, they drift past
    each other instead of locking into the groove or into each other.
    """

    title = "Clock tick"
    summary = "Drifting clockwork texture of overlapping ticks."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    needs_tempo: ClassVar[bool] = True

    level: float
    wood_q: float
    glass_q: float

    def build(self, tempo: Tempo, **values: Any) -> Patch:
        del tempo  # deliberately free-running, not tied to the tempo grid
        self.configure(**values)

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
        wood_voice = ButBP(wood_env, freq=500, q=self.wood_q)
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
        glass_voice = ButBP(glass_env, freq=4200, q=self.glass_q)
        keepalive += [glass_noise, glass_env, glass_voice]

        source = bright_voice + wood_voice + deep_voice + glass_voice
        keepalive.append(source)
        voice = source * self.level
        self.sequencer = _Clocks(metros=metros, keepalive=keepalive)
        self.voice = voice
        self.controls = {
            "level": lambda value: setattr(voice, "mul", value),
            "wood_q": lambda value: setattr(wood_voice, "q", value),
            "glass_q": lambda value: setattr(glass_voice, "q", value),
        }
        self.resources = keepalive
        return self
