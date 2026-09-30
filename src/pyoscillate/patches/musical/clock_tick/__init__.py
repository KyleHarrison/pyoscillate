# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.clock_tick
"""Four independent free-running noise-tick voices, each on its own
real-seconds period and shaped by a different filter (high-pass, two
band-passes, low-pass) into a distinct clock-like timbre, summed into one
drifting clockwork texture.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.filters import ButBP, ButHP, ButLP
from pyo.lib.generators import Noise
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import SequencerGroup
from pyoscillate.patches.params import Param

OVERALL_LEVEL = 0.5  # background texture, not a groove element - keep it low in the mix


class ClockTick(Patch):
    """Pink Floyd "Time"-style clock shop: four noise ticks, each on its own
    free-running period measured in real seconds rather than the tempo grid.
    Like a room of clocks that were never wound together, they drift past
    each other instead of locking into the groove or into each other.
    """

    title = "Clock tick"
    summary = "Drifting clockwork texture of overlapping ticks."
    volume = Patch.volume.replace(default=1.0)

    # same short, tight click shape used by the other hats - a tick, not a hiss
    ENVELOPE_POINTS: ClassVar[list[tuple[int, float]]] = [(0, 0), (20, 1), (400, 0)]

    # bright, thin wristwatch tick - fastest and quietest of the four
    BRIGHT_PERIOD: ClassVar[float] = 0.63
    BRIGHT_LEVEL: ClassVar[float] = 0.3
    BRIGHT_DUR: ClassVar[float] = 0.05
    BRIGHT_FREQ: ClassVar[float] = 6500

    # woodblock-ish tock - band-passed around a low-mid resonance
    WOOD_PERIOD: ClassVar[float] = 0.97
    WOOD_LEVEL: ClassVar[float] = 0.4
    WOOD_DUR: ClassVar[float] = 0.1
    WOOD_FREQ: ClassVar[float] = 500

    # deep pendulum tock - warm, longer decay, the slowest of the four
    DEEP_PERIOD: ClassVar[float] = 1.58
    DEEP_LEVEL: ClassVar[float] = 0.45
    DEEP_DUR: ClassVar[float] = 0.2
    DEEP_FREQ: ClassVar[float] = 350

    # thin metallic tick - like a mantel clock's escapement, rarer and brighter
    GLASS_PERIOD: ClassVar[float] = 2.44
    GLASS_LEVEL: ClassVar[float] = 0.3
    GLASS_DUR: ClassVar[float] = 0.06
    GLASS_FREQ: ClassVar[float] = 4200

    tick_envelope: CosTable
    bright_metro: Metro
    bright_noise: Noise
    bright_env: TrigEnv
    bright_voice: ButHP
    wood_metro: Metro
    wood_noise: Noise
    wood_env: TrigEnv
    wood_voice: ButBP
    deep_metro: Metro
    deep_noise: Noise
    deep_env: TrigEnv
    deep_voice: ButLP
    glass_metro: Metro
    glass_noise: Noise
    glass_env: TrigEnv
    glass_voice: ButBP
    source: PyoObject
    mix: PyoObject

    @Param(
        0,
        1,
        0.05,
        OVERALL_LEVEL,
        "Presence",
        "Sets how far forward the clock-shop texture sits in the mix, from a background murmur to a "
        "foreground element.",
    )
    def level(self, value: float) -> None:
        self.mix.mul = value

    @Param(
        1,
        10,
        0.5,
        3,
        "Wood tone",
        "Focuses the woodblock tock around a single pitch for a more tonal, ringing sound, or widens it "
        "into a duller, more percussive thud.",
    )
    def wood_q(self, value: float) -> None:
        self.wood_voice.q = value

    @Param(
        1,
        15,
        0.5,
        6,
        "Glass tone",
        "Focuses the metallic tick around a single ringing pitch, or widens it into a softer, less "
        "metallic click.",
    )
    def glass_q(self, value: float) -> None:
        self.glass_voice.q = value

    def finish(self, voice: PyoObject) -> Patch:
        """Minimal `finish()` for a musical-structure patch that owns its own
        multi-`Metro` sequencer instead of a `GatedVoice`/`ContinuousVoice`
        one: retain every node stored on `self` and run every `Param`
        control once, same as those bases' own `finish()`."""
        self.voice = voice
        self._bind()
        return self

    def build(self, context: BuildContext) -> Patch:
        del context  # deliberately free-running, not tied to the tempo grid
        self._reset()

        self.tick_envelope = CosTable(self.ENVELOPE_POINTS)

        self.bright_metro = Metro(time=self.BRIGHT_PERIOD)
        self.bright_noise = Noise(mul=self.BRIGHT_LEVEL)
        self.bright_env = TrigEnv(
            self.bright_metro,
            table=self.tick_envelope,
            dur=self.BRIGHT_DUR,
            mul=self.bright_noise,
        )
        self.bright_voice = ButHP(self.bright_env, freq=self.BRIGHT_FREQ)

        self.wood_metro = Metro(time=self.WOOD_PERIOD)
        self.wood_noise = Noise(mul=self.WOOD_LEVEL)
        self.wood_env = TrigEnv(
            self.wood_metro,
            table=self.tick_envelope,
            dur=self.WOOD_DUR,
            mul=self.wood_noise,
        )
        self.wood_voice = ButBP(self.wood_env, freq=self.WOOD_FREQ)

        self.deep_metro = Metro(time=self.DEEP_PERIOD)
        self.deep_noise = Noise(mul=self.DEEP_LEVEL)
        self.deep_env = TrigEnv(
            self.deep_metro,
            table=self.tick_envelope,
            dur=self.DEEP_DUR,
            mul=self.deep_noise,
        )
        self.deep_voice = ButLP(self.deep_env, freq=self.DEEP_FREQ)

        self.glass_metro = Metro(time=self.GLASS_PERIOD)
        self.glass_noise = Noise(mul=self.GLASS_LEVEL)
        self.glass_env = TrigEnv(
            self.glass_metro,
            table=self.tick_envelope,
            dur=self.GLASS_DUR,
            mul=self.glass_noise,
        )
        self.glass_voice = ButBP(self.glass_env, freq=self.GLASS_FREQ)

        self.source = (
            self.bright_voice + self.wood_voice + self.deep_voice + self.glass_voice
        )
        self.mix = self.source * 1.0

        self.sequencer = SequencerGroup(
            sequencers=(
                self.bright_metro,
                self.wood_metro,
                self.deep_metro,
                self.glass_metro,
            )
        )
        return self.finish(self.mix)
