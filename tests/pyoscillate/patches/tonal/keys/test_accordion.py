"""Perceptual contract for the accordion (`keys/accordion.py`): each register
adds its own rank of reeds, the musette's two 8' ranks beat against each other
as far as Musette tuning detunes them, Reed edge and Brightness open the top
of the reeds, Bellows shake pulses the level at Shake speed, Chiff puffs air on
the front of the note, and the loudest corner stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The first hit sits under `Patch.start()`'s fade-in, so tests
measure later ones.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum, Wobble
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.keys.accordion import Accordion
from pyoscillate.theory.phrase import Hooks, Rhythms
from pyoscillate.theory.pitch import Note

RATE = 44100
BPM = 120
MODULE = "pyoscillate.patches.tonal.keys.accordion"
# the first note of the figure is the key's root nearest the Register: A3
ROOT = Note.A3
HOOK = Accordion.phrase.catalog.index_of(Hooks.SPARSE_HOOK)
BAR = Accordion.phrase.catalog.index_of(Rhythms.BAR_PULSE)
SETTLED = (0.2, 0.45)
STRIKE = (0.5, 0.56)
# one rank of reeds and nothing else in the signal
PURE = {
    "bassoon": 0,
    "clarinet": 1,
    "musette": 0,
    "piccolo": 0,
    "shake": 0,
    "chiff": 0,
    "musette_tuning": 0,
}


@cache
def _render(seconds: float = 1.2, **params: float) -> Render:
    return render(MODULE, {"phrase": HOOK, **PURE, **params}, seconds=seconds, bpm=BPM)


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _settled(**params: float) -> Spectrum:
    return Spectrum.of(_window(_render(**params), SETTLED), RATE)


class HealthTests(unittest.TestCase):
    def test_render_is_silent_until_the_shared_clock_ticks(self) -> None:
        result = features(render(MODULE, {}, seconds=0.5, clock_running=False))

        self.assertLess(result.peak, 1e-4)

    def test_render_sounds_after_the_shared_clock_starts(self) -> None:
        self.assertGreater(features(render(MODULE, {}, seconds=0.8)).peak, 1e-3)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for phrase in (HOOK, BAR):
            with self.subTest(phrase=phrase):
                result = render(MODULE, {"phrase": phrase}, seconds=2.4, bpm=BPM)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)

    def test_the_loudest_corner_stays_under_the_patch_ceiling(self) -> None:
        loudest = {
            "bassoon": 1,
            "clarinet": 1,
            "musette": 1,
            "piccolo": 1,
            "reed_edge": Accordion.reed_edge.spec.maximum,
            "brightness": Accordion.brightness.spec.maximum,
            "chiff": Accordion.chiff.spec.maximum,
            "shake": Accordion.shake.spec.maximum,
        }
        for phrase in (HOOK, BAR):
            with self.subTest(phrase=phrase):
                result = render(
                    MODULE, {"phrase": phrase, **loudest}, seconds=2.4, bpm=BPM
                )

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)


class RegisterTests(unittest.TestCase):
    def test_the_bassoon_rank_adds_the_octave_below(self) -> None:
        without = _settled(bassoon=0).peak_near(ROOT / 2, 3)
        with_rank = _settled(bassoon=1).peak_near(ROOT / 2, 3)

        self.assertGreater(with_rank, 100 * without)

    def test_the_piccolo_rank_adds_the_octave_above(self) -> None:
        def octave(piccolo: float) -> float:
            levels = _settled(piccolo=piccolo).partial_levels(ROOT, 2)
            return float(levels[1] - levels[0])

        self.assertGreater(octave(1), octave(0) + 3)

    def test_a_rank_left_out_is_silent(self) -> None:
        spectrum = _settled(clarinet=0)

        self.assertLess(spectrum.power.sum(), 1e-6)


class MusetteTests(unittest.TestCase):
    def test_the_two_8_foot_ranks_beat_as_far_as_they_are_detuned(self) -> None:
        def beating(cents: float) -> float:
            result = _render(
                seconds=3.0, phrase=BAR, musette=1, musette_tuning=cents, legato=1
            )
            return Wobble.level(_window(result, (0.3, 1.8)), RATE, 0.05)

        # even in tune the chord's upper partials beat a little against each
        # other, as any equal-tempered chord's do
        self.assertGreater(beating(30), 2.5 * beating(0))

    def test_the_beats_are_the_difference_between_the_ranks_in_hz(self) -> None:
        def rate(cents: float) -> float:
            result = _render(
                seconds=3.6, phrase=BAR, musette=1, musette_tuning=cents, legato=1
            )
            return Wobble.level_rate(_window(result, (0.3, 1.8)), RATE, 0.005, 0.3, 40)

        # the chord's three notes each beat at their own pitch times the
        # detuning: the root's is the slowest, the top note's the fastest
        slowest = ROOT * (Note.semitone_ratio(30 / 100) - 1)
        fastest = slowest * Note.transpose(ROOT, 7) / ROOT

        self.assertGreater(rate(30), slowest - 1)
        self.assertLess(rate(30), fastest + 1)
        self.assertLess(rate(10), rate(30))


class ReedTests(unittest.TestCase):
    def test_a_sharper_reed_has_more_high_partials(self) -> None:
        mellow = _settled(reed_edge=0.3).share(2000, 20000)
        buzzy = _settled(reed_edge=1.0).share(2000, 20000)

        self.assertGreater(buzzy, 2 * mellow)

    def test_brightness_opens_the_top_of_the_reeds(self) -> None:
        dull = _settled(brightness=800).share(2000, 20000)
        bright = _settled(brightness=12000).share(2000, 20000)

        self.assertGreater(bright, 5 * dull)


class BellowsTests(unittest.TestCase):
    def _held(self, **params: float) -> np.ndarray:
        result = _render(seconds=2.4, phrase=BAR, legato=1, **params)
        return _window(result, (0.3, 1.8))

    def test_the_bellows_shake_pulses_the_level(self) -> None:
        steady = Wobble.level(self._held(shake=0), RATE, 0.05)
        shaken = Wobble.level(self._held(shake=1, shake_speed=8), RATE, 0.05)

        self.assertGreater(shaken, 0.4)
        self.assertGreater(shaken, 2.5 * steady)

    def test_the_level_pulses_at_the_shake_speed(self) -> None:
        for speed in (5.0, 10.0):
            samples = self._held(shake=1, shake_speed=speed)

            with self.subTest(shake_speed=speed):
                self.assertAlmostEqual(
                    Wobble.level_rate(samples, RATE, 0.005, 2, 20), speed, delta=1.0
                )


class ChiffTests(unittest.TestCase):
    def test_chiff_puffs_air_on_the_front_of_the_note(self) -> None:
        def air(chiff: float) -> float:
            result = _render(chiff=chiff, brightness=12000)
            return Spectrum.of(_window(result, (0.5, 0.54)), RATE).band(1500, 3500)

        self.assertGreater(air(1), 1.5 * air(0))


class AttackTests(unittest.TestCase):
    def test_a_slower_attack_lets_the_bellows_take_longer_to_get_the_reed_going(
        self,
    ) -> None:
        def front(attack: float) -> float:
            result = _render(attack=attack)
            return float(np.sqrt((_window(result, STRIKE) ** 2).mean()))

        self.assertGreater(front(0.005), 3 * front(1.5))


if __name__ == "__main__":
    unittest.main()
