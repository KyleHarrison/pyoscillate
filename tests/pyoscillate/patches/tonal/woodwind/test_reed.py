"""Perceptual contract for the reed winds (`woodwind/reed/`): each sits on the
rack's note, Bore fades the even harmonics in (a clarinet's cylinder keeps only
the odd ones, a cone the whole series), Reed edge brings the upper harmonics
in, neither changes the loudness, Nasal rings the double reeds' fixed
resonance, the bass clarinet sounds an octave under the clarinet, and the
bagpipes' drone sounds a fixed note under the line.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The phrase is every wind's default (`Leads.WIND_DRIFT`): the
second note, the minor sixth above the chord root, starts at 0.625 s. The
render's chord root is an A, so a style's note is the A nearest its Register
(`root_freq` default) plus 8 semitones. A note is measured once its attack is
over.
"""

import math
import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.woodwind.reed.bagpipes import Bagpipes
from pyoscillate.patches.tonal.woodwind.reed.double import (
    Bassoon,
    Contrabassoon,
    EnglishHorn,
    Oboe,
)
from pyoscillate.patches.tonal.woodwind.reed.single import Clarinet, ClarinetBass
from pyoscillate.patches.tonal.woodwind.wind import Wind
from pyoscillate.theory.pitch import Note

RATE = 44100
BPM = 120
SINGLE = "pyoscillate.patches.tonal.woodwind.reed.single"
DOUBLE = "pyoscillate.patches.tonal.woodwind.reed.double"
BAGPIPES = "pyoscillate.patches.tonal.woodwind.reed.bagpipes"
# module, style, class for every reed
REEDS = (
    (SINGLE, "clarinet", Clarinet),
    (SINGLE, "bass", ClarinetBass),
    (DOUBLE, "oboe", Oboe),
    (DOUBLE, "horn", EnglishHorn),
    (DOUBLE, "bassoon", Bassoon),
    (DOUBLE, "contrabassoon", Contrabassoon),
    (BAGPIPES, "", Bagpipes),
)
SETTLED = (0.78, 0.93)
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
    "brightness": 12000,
    "release": 0.03,
}


def _note(patch: type[Wind]) -> float:
    """The second note of the default phrase: 8 semitones above the A nearest
    the style's Register."""
    default = patch.root_freq.spec.default
    return Note.transpose(Note.A1 * 2 ** round(math.log2(default / Note.A1)), 8)


@cache
def _render(module: str, style: str, **params: float) -> Render:
    named = {"style": style} if style else {}
    return render(module, {**PURE, **named, **params}, seconds=1.2, bpm=BPM)


def _settled(module: str, style: str, **params: float) -> Spectrum:
    samples = _render(module, style, **params).samples
    window = samples[round(SETTLED[0] * RATE) : round(SETTLED[1] * RATE)]
    return Spectrum.of(window, RATE)


def _rms(module: str, style: str, **params: float) -> float:
    samples = _render(module, style, **params).samples
    window = samples[round(SETTLED[0] * RATE) : round(SETTLED[1] * RATE)]
    return float(np.sqrt((window**2).mean()))


class HealthTests(unittest.TestCase):
    def test_every_reed_sounds_on_the_note(self) -> None:
        for module, style, patch in REEDS:
            with self.subTest(reed=patch.__name__):
                note = _note(patch)
                spectrum = _settled(module, style)

                self.assertAlmostEqual(
                    spectrum.peak_frequency(note * 0.8, note * 1.25),
                    note,
                    delta=0.01 * note,
                )

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for module, style, patch in REEDS:
            with self.subTest(reed=patch.__name__):
                loudest = {
                    "brightness": patch.brightness.spec.maximum,
                    "breath": patch.breath.spec.maximum,
                    "tongue": patch.tongue.spec.maximum,
                    "cone": 1,
                    "edge": 1,
                    "nasal": 1,
                    "tremolo": patch.tremolo.spec.maximum,
                    "tracking": patch.tracking.spec.maximum,
                    "reverb_bal": patch.reverb_bal.spec.maximum,
                }
                named = {"style": style} if style else {}
                result = render(module, {**named, **loudest}, seconds=2.4, bpm=BPM)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)

    def test_a_reed_plays_with_its_defaults(self) -> None:
        for module, style, patch in REEDS:
            with self.subTest(reed=patch.__name__):
                named = {"style": style} if style else {}

                self.assertGreater(
                    features(render(module, named, seconds=0.8)).peak, 1e-3
                )


class BoreTests(unittest.TestCase):
    def test_a_cylinder_keeps_only_the_odd_harmonics(self) -> None:
        note = _note(Clarinet)
        levels = _settled(SINGLE, "clarinet", cone=0).partial_levels(note, 4)

        # the second and fourth harmonics are far below the first and third
        self.assertLess(levels[1], levels[0] - 25)
        self.assertLess(levels[3], levels[2] - 25)

    def test_a_cone_keeps_the_whole_series(self) -> None:
        note = _note(Clarinet)

        def second(cone: float) -> float:
            levels = _settled(SINGLE, "clarinet", cone=cone).partial_levels(note, 2)
            return float(levels[1] - levels[0])

        self.assertGreater(second(1), second(0) + 20)

    def test_reed_edge_brings_in_the_upper_harmonics(self) -> None:
        note = _note(Oboe)

        def eighth(edge: float) -> float:
            levels = _settled(DOUBLE, "oboe", edge=edge).partial_levels(note, 8)
            return float(levels[7] - levels[0])

        self.assertGreater(eighth(1), eighth(0) + 10)

    def test_bore_and_reed_edge_do_not_change_the_loudness(self) -> None:
        for name, values in (("cone", (0, 1)), ("edge", (0, 1))):
            with self.subTest(control=name):
                low, high = (_rms(DOUBLE, "oboe", **{name: value}) for value in values)
                quiet, loud = sorted((low, high))

                self.assertLess(20 * np.log10(loud / quiet), 1.5)


class ColourTests(unittest.TestCase):
    def test_nasal_rings_the_double_reeds_resonance(self) -> None:
        def ring(nasal: float) -> float:
            spectrum = _settled(DOUBLE, "oboe", nasal=nasal)
            return spectrum.band(Oboe.nasal_freq * 0.7, Oboe.nasal_freq * 1.4)

        self.assertGreater(ring(1), 1.5 * ring(0))

    def test_the_bass_clarinet_sounds_an_octave_under_the_clarinet(self) -> None:
        clarinet = _settled(SINGLE, "clarinet").peak_frequency(100, 1000)
        bass = _settled(SINGLE, "bass").peak_frequency(60, 500)

        self.assertAlmostEqual(clarinet / bass, 2.0, delta=0.05)


class DroneTests(unittest.TestCase):
    def test_the_drone_sounds_a_fixed_note_under_the_line(self) -> None:
        drone = Bagpipes.root_freq.spec.default * Bagpipes.drone_ratio

        def power(level: float) -> float:
            spectrum = _settled(BAGPIPES, "", drone=level)
            return spectrum.band(drone * 0.97, drone * 1.03)

        self.assertGreater(power(1), 20 * power(0))


if __name__ == "__main__":
    unittest.main()
