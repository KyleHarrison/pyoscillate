"""Perceptual contract for the whistle (`vocal/whistling.py`) and for the
held-voice pitch controls it shows cleanly (a whistle is near a sine, so its
pitch can be tracked): the whistle sits on the note, Vibrato rocks it and
blooms in, Unsteadiness makes it wander, Glide slides into the next note, Edge
adds a harder overtone, Purity sharpens the breath and Brightness covers it.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md.

Findings
========

1. Edge was not a faint overtone
--------------------------------
Error:
    At full Edge the second harmonic measured -0.2 dB against the tone: as loud
    as the whistle itself, so the whistle turned into an octave rather than a
    harder, shriller tone, and the help text promises "a harder overtone rides
    on the whistle".
Cause:
    The overtone's level followed the Edge slider one to one, so its maximum was
    the tone's own level.
Change:
    The level is scaled by `edge_max` (0.35, so the overtone reaches about
    -9 dB at full Edge).
Status:
    fixed - src/pyoscillate/patches/tonal/vocal/whistling.py.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum, Wobble
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.vocal.whistling import Whistling
from pyoscillate.theory.pitch import Note

RATE = 44100
BPM = 120
MODULE = "pyoscillate.patches.tonal.vocal.whistling"
# a sparse hook on the eighth grid: A5 at 0, the third above at 0.5 s. The
# first note's window is after the fade-in and attack, before the second
FIRST = (0.12, 0.47)
SETTLED = (0.3, 0.45)
SECOND = (0.52, 0.58)
PURE = {"breath": 0, "vibrato": 0, "unsteadiness": 0, "reverb_bal": 0, "edge": 0}
NOTE = Note.A5
THIRD = Note.transpose(Note.A5, 4)


@cache
def _render(seconds: float = 1.2, **params: float) -> Render:
    return render(MODULE, {**PURE, **params}, seconds=seconds, bpm=BPM)


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _settled(**params: float) -> Spectrum:
    return Spectrum.of(_window(_render(**params), SETTLED), RATE)


def _swing(seconds: float = 1.2, **params: float) -> float:
    return Wobble.pitch(_window(_render(seconds, **params), FIRST), RATE, 500, 2500)


class HealthTests(unittest.TestCase):
    def test_render_is_silent_until_the_shared_clock_ticks(self) -> None:
        result = features(render(MODULE, {}, seconds=0.5, clock_running=False))

        self.assertLess(result.peak, 1e-4)

    def test_render_sounds_after_the_shared_clock_starts(self) -> None:
        self.assertGreater(features(render(MODULE, {}, seconds=0.8)).peak, 1e-3)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        loudest = {
            "brightness": Whistling.brightness.spec.maximum,
            "breath": Whistling.breath.spec.maximum,
            "edge": Whistling.edge.spec.maximum,
            "purity": Whistling.purity.spec.maximum,
            "reverb_bal": Whistling.reverb_bal.spec.maximum,
        }
        for name, params in (("default", {}), ("loudest corner", loudest)):
            with self.subTest(settings=name):
                result = render(MODULE, params, seconds=2.4, bpm=BPM)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)


class PitchTests(unittest.TestCase):
    def test_the_whistle_sits_on_the_note(self) -> None:
        self.assertAlmostEqual(_settled().peak_frequency(500, 2500), NOTE, delta=3)

    def test_vibrato_rocks_the_pitch_by_about_its_depth(self) -> None:
        steady = _swing(vibrato=0, vibrato_bloom=0.01)
        rocking = _swing(vibrato=100, vibrato_bloom=0.01)

        self.assertLess(steady, 5)
        # a swing of +-100 cents is 200 cents from low to high; the window
        # holds a little under two cycles of the default speed
        self.assertGreater(rocking, 100)
        self.assertLess(rocking, 260)

    def test_vibrato_blooms_in_after_the_note_starts(self) -> None:
        early = _swing(vibrato=100, vibrato_bloom=0.01)
        blooming = _swing(vibrato=100, vibrato_bloom=2.0)

        self.assertGreater(early, 3 * blooming)

    def test_unsteadiness_makes_the_pitch_wander(self) -> None:
        steady = _swing(seconds=3.2, unsteadiness=0)
        wandering = _swing(seconds=3.2, unsteadiness=1)

        self.assertLess(steady, 1)
        self.assertGreater(wandering, 3)

    def test_glide_slides_into_the_next_note(self) -> None:
        def second_note(glide: float) -> float:
            samples = _window(_render(glide=glide), SECOND)
            return Spectrum.of(samples, RATE).peak_frequency(500, 2500)

        # without a glide the second note is already on the third above;
        # with one it is still on its way up from the first
        self.assertAlmostEqual(second_note(0), THIRD, delta=8)
        self.assertLess(second_note(0.3), THIRD - 50)


class ToneTests(unittest.TestCase):
    def test_edge_adds_a_harder_overtone(self) -> None:
        def overtone(edge: float) -> float:
            levels = _settled(edge=edge).partial_levels(NOTE, 2)
            return float(levels[1] - levels[0])

        self.assertGreater(overtone(1), overtone(0) + 60)
        # a harder tone, not an octave: the overtone stays below the whistle
        self.assertLess(overtone(1), 0)

    def test_purity_gathers_the_breath_around_the_pitch(self) -> None:
        def nearness(purity: float) -> float:
            spectrum = _settled(breath=1, purity=purity)
            tone = spectrum.band(NOTE - 20, NOTE + 20)
            near = spectrum.band(NOTE * 0.9, NOTE * 1.1) - tone
            wide = spectrum.band(NOTE * 0.3, NOTE * 3) - tone
            return near / wide

        self.assertGreater(nearness(80), 1.5 * nearness(4))

    def test_breath_adds_hiss_around_the_whistle(self) -> None:
        def hiss(breath: float) -> float:
            spectrum = _settled(breath=breath)
            return spectrum.band(NOTE * 0.9, NOTE * 1.1) - spectrum.band(
                NOTE - 40, NOTE + 40
            )

        self.assertGreater(hiss(1), 3 * hiss(0))

    def test_brightness_covers_a_shrill_whistle(self) -> None:
        def level(brightness: float) -> float:
            samples = _window(_render(brightness=brightness), SETTLED)
            return float(np.sqrt((samples**2).mean()))

        self.assertGreater(level(9000), 2 * level(500))


if __name__ == "__main__":
    unittest.main()
