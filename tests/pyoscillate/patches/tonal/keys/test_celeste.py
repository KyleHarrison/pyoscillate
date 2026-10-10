"""Perceptual contract for the celeste (`keys/celeste.py`): a pure, bell-like
tone with a faint glassy ping, Bark sets that ping, Bite brightens the ring,
Decay sets how long a chord rings, it sits above the electric piano, and the
loudest corner stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The first chord sits under `Patch.start()`'s fade-in, so
tests measure the second, struck at 0.5 s of a quarter-note pulse.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.keys.celeste import Celeste
from pyoscillate.patches.tonal.keys.keys import Keys

RATE = 44100
BPM = 120
MODULE = "pyoscillate.patches.tonal.keys.celeste"
# a quarter pulse strikes a chord every 0.5 s; the ping is the first 60 ms
STRIKE = (0.5, 0.56)
PING = 2000


@cache
def _render(seconds: float = 2.0, **params: float) -> Render:
    return render(MODULE, params, seconds=seconds, bpm=BPM)


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _rms(result: Render, span: tuple[float, float]) -> float:
    return float(np.sqrt((_window(result, span) ** 2).mean()))


class HealthTests(unittest.TestCase):
    def test_render_is_silent_until_the_shared_clock_ticks(self) -> None:
        result = features(render(MODULE, {}, seconds=0.5, clock_running=False))

        self.assertLess(result.peak, 1e-4)

    def test_render_sounds_after_the_shared_clock_starts(self) -> None:
        self.assertGreater(features(_render()).peak, 1e-3)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        self.assertLess(float(abs(_render().samples).max()), PATCH_OUTPUT_CEILING)

    def test_the_loudest_corner_stays_under_the_patch_ceiling(self) -> None:
        result = _render(
            bark=Celeste.bark.spec.maximum,
            bite=Celeste.bite.spec.maximum,
            decay=Celeste.decay.spec.maximum,
            tremolo=Celeste.tremolo.spec.maximum,
        )

        self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)


class ToneTests(unittest.TestCase):
    def test_a_soft_strike_is_a_pure_bell_tone(self) -> None:
        result = _render(bark=0, bite=0, tremolo=0)

        spectrum = Spectrum.of(_window(result, (0.8, 1.2)), RATE)

        # nearly everything sits in the chord's own register, below the ping
        self.assertGreater(spectrum.share(100, 1500), 0.97)

    def test_bark_adds_a_ping_to_the_front_of_the_chord(self) -> None:
        def ping(bark: float) -> float:
            result = _render(bark=bark, bite=0, tremolo=0)
            return Spectrum.of(_window(result, STRIKE), RATE).share(PING, 20000)

        self.assertGreater(ping(6), 3 * ping(0))

    def test_the_ping_clears_and_leaves_the_pure_tone(self) -> None:
        def late(bark: float) -> float:
            result = _render(bark=bark, bite=0, tremolo=0)
            return Spectrum.of(_window(result, (0.9, 1.4)), RATE).share(PING, 20000)

        self.assertLess(late(6), 0.01)

    def test_bite_brightens_the_ring(self) -> None:
        def ring(bite: float) -> float:
            result = _render(bark=0, bite=bite, tremolo=0)
            return Spectrum.of(_window(result, (0.8, 1.2)), RATE).centroid()

        self.assertGreater(ring(Celeste.bite.spec.maximum), 1.2 * ring(0))


class DecayTests(unittest.TestCase):
    def test_a_longer_decay_lets_the_chord_ring_on(self) -> None:
        def fall(decay: float) -> float:
            result = _render(decay=decay, tremolo=0)
            return _rms(result, (0.9, 0.99)) / _rms(result, (0.55, 0.64))

        self.assertGreater(fall(4.0), 1.5 * fall(0.5))


class RegisterTests(unittest.TestCase):
    def test_the_celeste_sits_above_the_electric_piano(self) -> None:
        self.assertGreater(Celeste.root_freq.default, Keys.root_freq.default)
        self.assertGreater(Celeste.root_freq.spec.maximum, Keys.root_freq.spec.maximum)


if __name__ == "__main__":
    unittest.main()
