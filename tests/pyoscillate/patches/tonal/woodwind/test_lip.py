"""Perceptual contract for the lip winds (`woodwind/lip/`): each sits on the
rack's note, Buzz brings in the upper harmonics without changing the loudness,
and Mouth sweeps a resonance through the tone that Mouth speed moves.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The phrase is every wind's default (`Leads.WIND_DRIFT`): the
second note, the minor sixth above the chord root, starts at 0.625 s. The
render's chord root is an A, so a style's note is the A nearest its Register
(`root_freq` default) plus 8 semitones.
"""

import math
import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.woodwind.lip.natural import ConchShell, Didgeridoo
from pyoscillate.patches.tonal.woodwind.wind import Wind
from pyoscillate.theory.pitch import Note

RATE = 44100
BPM = 120
MODULE = "pyoscillate.patches.tonal.woodwind.lip.natural"
LIPS = (("shell", ConchShell), ("didgeridoo", Didgeridoo))
SETTLED = (0.78, 0.93)
# with the rate halved the second note lasts from 1.25 s to 2.0 s
SLOW = {"rate": -1, "legato": 1.0, "attack": 0.01, "release": 0.03}
SLOW_SETTLED = (1.45, 1.95)
PURE = {
    "breath": 0,
    "vibrato": 0,
    "unsteadiness": 0,
    "tremolo": 0,
    "tongue": 0,
    "bend": 0,
    "opening": 0,
    "tracking": 0,
    "reverb_bal": 0,
    "mouth": 0,
    "brightness": 12000,
    "release": 0.03,
}


def _note(patch: type[Wind]) -> float:
    """The second note of the default phrase: 8 semitones above the A nearest
    the style's Register."""
    default = patch.root_freq.spec.default
    return Note.transpose(Note.A1 * 2 ** round(math.log2(default / Note.A1)), 8)


@cache
def _render(style: str, seconds: float = 1.2, **params: float) -> Render:
    return render(MODULE, {**PURE, "style": style, **params}, seconds=seconds, bpm=BPM)


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _settled(style: str, **params: float) -> Spectrum:
    return Spectrum.of(_window(_render(style, **params), SETTLED), RATE)


class HealthTests(unittest.TestCase):
    def test_every_lip_wind_sounds_on_the_note(self) -> None:
        for style, patch in LIPS:
            with self.subTest(wind=patch.__name__):
                note = _note(patch)

                self.assertAlmostEqual(
                    _settled(style).peak_frequency(note * 0.8, note * 1.25),
                    note,
                    delta=0.01 * note,
                )

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for style, patch in LIPS:
            with self.subTest(wind=patch.__name__):
                loudest = {
                    "brightness": patch.brightness.spec.maximum,
                    "breath": patch.breath.spec.maximum,
                    "tongue": patch.tongue.spec.maximum,
                    "buzz": 1,
                    "mouth": 1,
                    "tremolo": patch.tremolo.spec.maximum,
                    "tracking": patch.tracking.spec.maximum,
                    "reverb_bal": patch.reverb_bal.spec.maximum,
                }
                result = render(
                    MODULE, {"style": style, **loudest}, seconds=2.4, bpm=BPM
                )

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)

    def test_a_lip_wind_plays_with_its_defaults(self) -> None:
        for style, patch in LIPS:
            with self.subTest(wind=patch.__name__):
                result = render(MODULE, {"style": style}, seconds=0.8)

                self.assertGreater(features(result).peak, 1e-3)


class BuzzTests(unittest.TestCase):
    def test_buzz_brings_in_the_upper_harmonics(self) -> None:
        note = _note(Didgeridoo)

        def eighth(buzz: float) -> float:
            levels = _settled("didgeridoo", buzz=buzz).partial_levels(note, 8)
            return float(levels[7] - levels[0])

        self.assertGreater(eighth(1), eighth(0) + 10)

    def test_buzz_does_not_change_the_loudness(self) -> None:
        def level(buzz: float) -> float:
            return float(
                np.sqrt(
                    (_window(_render("didgeridoo", buzz=buzz), SETTLED) ** 2).mean()
                )
            )

        quiet, loud = sorted((level(0), level(1)))
        self.assertLess(20 * np.log10(loud / quiet), 1.5)


class MouthTests(unittest.TestCase):
    def test_mouth_rings_a_resonance_through_the_tone(self) -> None:
        def ring(mouth: float) -> float:
            samples = _window(
                _render("didgeridoo", 2.1, **SLOW, mouth=mouth), SLOW_SETTLED
            )
            spectrum = Spectrum.of(samples, RATE)
            return spectrum.band(Didgeridoo.mouth_low, Didgeridoo.mouth_high)

        self.assertGreater(ring(1), 1.5 * ring(0))


if __name__ == "__main__":
    unittest.main()
