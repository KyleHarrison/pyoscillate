"""Perceptual contract for the drawbar organ (`keys/organ.py`): each drawbar
sounds its own harmonic, in 3 dB steps; Percussion chimes on the front of the
note at the pitch it names and for as long as Percussion decay says; Key click
adds a tick; Leslie turns the level and Drive adds harmonics without changing
the loudness; and the loudest corner stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The first hit sits under `Patch.start()`'s fade-in, so tests
measure the second, at 0.5 s of a sparse hook on the eighth grid.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum, Wobble
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.keys.organ import Organ
from pyoscillate.theory.phrase import Hooks, Rhythms
from pyoscillate.theory.pitch import Note

RATE = 44100
BPM = 120
MODULE = "pyoscillate.patches.tonal.keys.organ"
# the first note of the figure is the key's root nearest the Register: A3; the
# second, struck at 0.5 s, is the major third above it
ROOT = Note.A3
THIRD = Note.transpose(ROOT, 4)
HOOK = Organ.phrase.catalog.index_of(Hooks.SPARSE_HOOK)
BAR = Organ.phrase.catalog.index_of(Rhythms.BAR_PULSE)
# every drawbar and what it is a harmonic of
DRAWBARS = (
    ("sub", 0.5),
    ("sub_fifth", 1.5),
    ("fundamental", 1.0),
    ("octave", 2.0),
    ("twelfth", 3.0),
    ("fifteenth", 4.0),
    ("tierce", 5.0),
    ("nazard", 6.0),
    ("fife", 8.0),
)
OFF = {name: 0 for name, _ in DRAWBARS}
# a single drawbar and nothing else in the signal
PURE = {
    **OFF,
    "percussion": 0,
    "click": 0,
    "leslie": 0,
    "drive": 0,
    "reverb_bal": 0,
    "vibrato": 0,
}
SETTLED = (0.2, 0.45)
STRIKE = (0.5, 0.56)


@cache
def _render(seconds: float = 1.2, **params: float) -> Render:
    return render(MODULE, {"phrase": HOOK, **params}, seconds=seconds, bpm=BPM)


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _rms(result: Render, span: tuple[float, float]) -> float:
    return float(np.sqrt((_window(result, span) ** 2).mean()))


def _single(drawbar: str, setting: float = 8, **params: float) -> Render:
    return _render(**{**PURE, drawbar: setting, **params})


class HealthTests(unittest.TestCase):
    def test_render_is_silent_until_the_shared_clock_ticks(self) -> None:
        result = features(render(MODULE, {}, seconds=0.5, clock_running=False))

        self.assertLess(result.peak, 1e-4)

    def test_render_sounds_after_the_shared_clock_starts(self) -> None:
        self.assertGreater(features(_render()).peak, 1e-3)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for phrase in (HOOK, BAR):
            with self.subTest(phrase=phrase):
                result = _render(seconds=2.4, phrase=phrase)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)

    def test_the_loudest_corner_stays_under_the_patch_ceiling(self) -> None:
        loudest = {
            **{name: Organ.fundamental.spec.maximum for name, _ in DRAWBARS},
            "percussion": Organ.percussion.spec.maximum,
            "click": Organ.click.spec.maximum,
            "leslie": Organ.leslie.spec.maximum,
            "drive": Organ.drive.spec.maximum,
            "reverb_bal": Organ.reverb_bal.spec.maximum,
        }
        for phrase in (HOOK, BAR):
            with self.subTest(phrase=phrase):
                result = _render(seconds=2.4, phrase=phrase, **loudest)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)


class DrawbarTests(unittest.TestCase):
    def test_each_drawbar_sounds_its_own_harmonic_of_the_note(self) -> None:
        for name, ratio in DRAWBARS:
            spectrum = Spectrum.of(_window(_single(name), SETTLED), RATE)

            with self.subTest(drawbar=name):
                self.assertAlmostEqual(
                    spectrum.peak_frequency(20, 5000), ROOT * ratio, delta=3
                )

    def test_a_drawbar_off_is_silent(self) -> None:
        self.assertLess(_rms(_single("fundamental", 0), SETTLED), 1e-4)

    def test_each_step_of_a_drawbar_is_3_db(self) -> None:
        def level(setting: float) -> float:
            return 20 * np.log10(_rms(_single("fundamental", setting), SETTLED))

        # 8 to 5 is three steps: 9 dB
        self.assertAlmostEqual(level(8) - level(5), 3 * Organ.drawbar_step, delta=1.0)

    def test_the_drawbar_scale_runs_from_silence_to_unity(self) -> None:
        patch = Organ()

        self.assertEqual(patch.drawbar_level(0), 0.0)
        self.assertAlmostEqual(patch.drawbar_level(Organ.drawbar_steps), 1.0)
        self.assertAlmostEqual(
            patch.drawbar_level(Organ.drawbar_steps - 1),
            10 ** (-Organ.drawbar_step / 20),
        )

    def test_a_full_set_of_drawbars_is_not_a_great_deal_louder_than_one(self) -> None:
        one = _rms(_single("fundamental", reverb_bal=0), SETTLED)
        full = _rms(_render(**{**PURE, **{name: 8 for name, _ in DRAWBARS}}), SETTLED)

        self.assertLess(20 * np.log10(full / one), 12)


class PercussionTests(unittest.TestCase):
    def _fall(self, **params: float) -> float:
        """The level of the front of a note against the level that follows."""
        result = _single("fundamental", **params)
        return _rms(result, STRIKE) / _rms(result, (0.8, 0.95))

    def test_percussion_chimes_on_the_front_of_each_note(self) -> None:
        self.assertGreater(self._fall(percussion=1), 1.5 * self._fall(percussion=0))

    def test_percussion_chimes_at_the_harmonic_it_names(self) -> None:
        def chime(pitch: float) -> np.ndarray:
            result = _single("fundamental", percussion=1, percussion_pitch=pitch)
            return Spectrum.of(_window(result, STRIKE), RATE).partial_levels(THIRD, 3)

        second, third = chime(0), chime(1)

        self.assertGreater(second[1] - second[2], 3)
        self.assertGreater(third[2] - third[1], 3)

    def test_a_longer_percussion_decay_lets_the_chime_ring_on(self) -> None:
        def ring(decay: float) -> float:
            result = _single(
                "fundamental", percussion=1, percussion_decay=decay, percussion_pitch=1
            )
            return Spectrum.of(_window(result, (0.7, 0.9)), RATE).band(
                THIRD * 3 - 5, THIRD * 3 + 5
            )

        self.assertGreater(ring(0.8), 10 * ring(0.05))


class ClickTests(unittest.TestCase):
    def test_key_click_adds_a_tick_to_the_front_of_the_note(self) -> None:
        def tick(click: float) -> float:
            result = _single("fundamental", click=click)
            return Spectrum.of(_window(result, (0.498, 0.52)), RATE).band(3000, 20000)

        self.assertGreater(tick(1), 10 * tick(0))


class LeslieTests(unittest.TestCase):
    # a held chord, slurred from bar to bar, after the rotors have reached
    # their speed (they take about a second)
    HELD = (2.2, 3.4)

    def _held(self, **params: float) -> np.ndarray:
        result = _render(
            seconds=3.6,
            phrase=BAR,
            **{**PURE, "fundamental": 8, "legato": 1, **params},
        )
        return _window(result, self.HELD)

    def test_leslie_pulses_the_level(self) -> None:
        steady = Wobble.level(self._held(leslie=0), RATE, 0.1)
        turning = Wobble.level(self._held(leslie=1, rotor_rate=2), RATE, 0.1)

        self.assertLess(steady, 0.1)
        self.assertGreater(turning, 0.4)
        self.assertGreater(turning, 5 * steady)

    def test_the_level_pulses_at_the_rotor_speed(self) -> None:
        for rate in (2.0, 6.0):
            samples = self._held(leslie=1, rotor_rate=rate)

            with self.subTest(rotor_rate=rate):
                self.assertAlmostEqual(
                    Wobble.level_rate(samples, RATE), rate, delta=0.8
                )


class DriveTests(unittest.TestCase):
    def test_drive_adds_harmonics_to_the_tone(self) -> None:
        def top(drive: float) -> float:
            result = _single("fundamental", drive=drive)
            return Spectrum.of(_window(result, SETTLED), RATE).share(ROOT * 1.5, 20000)

        self.assertGreater(top(1), 100 * top(0))

    def test_drive_keeps_the_organ_at_one_loudness(self) -> None:
        levels = [
            20 * np.log10(_rms(_single("fundamental", drive=drive), SETTLED))
            for drive in (0, 0.5, 1)
        ]

        self.assertLess(max(levels) - min(levels), 4)


if __name__ == "__main__":
    unittest.main()
