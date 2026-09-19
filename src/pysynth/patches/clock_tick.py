from __future__ import annotations

from dataclasses import dataclass

from pyo.lib.filters import ButBP, ButHP, ButLP
from pyo.lib.generators import Noise
from pyo.lib.pattern import Pattern
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pysynth.patches.base import Patch
from pysynth.tempo import Tempo

OVERALL_LEVEL = 0.5  # background texture, not a groove element - keep it low in the mix


@dataclass
class _MultiSequencer:
    """Fans play()/stop() out over several independent Patterns, so one Patch
    can drive multiple free-running clocks that never share a downbeat.

    Also holds a strong reference to each clock's Trig. pyo's Pattern only
    keeps a weak reference to its callback target, and summing the four
    voices together (`bright_voice + wood_voice + ...`) drops the only other
    strong reference to each per-tick chain - without this, the Trigs get
    garbage collected shortly after build() returns and playback dies with
    "ReferenceError: weakly-referenced object no longer exists".
    """

    patterns: list[Pattern]
    triggers: list[Trig]

    def play(self) -> None:
        for pattern in self.patterns:
            pattern.play()

    def stop(self) -> None:
        for pattern in self.patterns:
            pattern.stop()


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

    patterns: list[Pattern] = []
    triggers: list[Trig] = []

    # bright, thin wristwatch tick - fastest and quietest of the four
    bright_trig = Trig()
    bright_env = TrigEnv(bright_trig, table=tick_envelope, dur=0.05, mul=Noise(mul=0.3))
    bright_voice = ButHP(bright_env, freq=6500)
    patterns.append(Pattern(bright_trig.play, time=0.63))
    triggers.append(bright_trig)

    # woodblock-ish tock - band-passed around a low-mid resonance
    wood_trig = Trig()
    wood_env = TrigEnv(wood_trig, table=tick_envelope, dur=0.1, mul=Noise(mul=0.4))
    wood_voice = ButBP(wood_env, freq=500, q=wood_q)
    patterns.append(Pattern(wood_trig.play, time=0.97))
    triggers.append(wood_trig)

    # deep pendulum tock - warm, longer decay, the slowest of the four
    deep_trig = Trig()
    deep_env = TrigEnv(deep_trig, table=tick_envelope, dur=0.2, mul=Noise(mul=0.45))
    deep_voice = ButLP(deep_env, freq=350)
    patterns.append(Pattern(deep_trig.play, time=1.58))
    triggers.append(deep_trig)

    # thin metallic tick - like a mantel clock's escapement, rarer and brighter
    glass_trig = Trig()
    glass_env = TrigEnv(glass_trig, table=tick_envelope, dur=0.06, mul=Noise(mul=0.3))
    glass_voice = ButBP(glass_env, freq=4200, q=glass_q)
    patterns.append(Pattern(glass_trig.play, time=2.44))
    triggers.append(glass_trig)

    voice = (bright_voice + wood_voice + deep_voice + glass_voice) * level
    sequencer = _MultiSequencer(patterns=patterns, triggers=triggers)
    return Patch(sequencer=sequencer, voice=voice)
