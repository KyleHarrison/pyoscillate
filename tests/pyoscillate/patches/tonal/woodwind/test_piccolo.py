"""Perceptual contract for the piccolo (`woodwind/flute/piccolo.py`): it sits
on the rack's note an octave above the flute, with the jet wind's near-pure
tone, and the loudest corner stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The phrase is every wind's default (`Leads.WIND_DRIFT`): the
second note, the minor sixth above the chord root, starts at 0.625 s. The
render's chord root is an A, so the note is the A nearest each Register plus 8
semitones: F5 for the flute, F6 for the piccolo.
"""

import unittest
from functools import cache

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.woodwind.flute.piccolo import Piccolo

RATE = 44100
BPM = 120
FLUTE = "pyoscillate.patches.tonal.woodwind.flute.flute"
PICCOLO = "pyoscillate.patches.tonal.woodwind.flute.piccolo"
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


@cache
def _render(module: str) -> Render:
    return render(module, PURE, seconds=1.2, bpm=BPM)


def _peak(module: str) -> float:
    samples = _render(module).samples
    window = samples[round(SETTLED[0] * RATE) : round(SETTLED[1] * RATE)]
    return Spectrum.of(window, RATE).peak_frequency(300, 3000)


class PiccoloTests(unittest.TestCase):
    def test_the_piccolo_sounds_an_octave_above_the_flute(self) -> None:
        self.assertAlmostEqual(_peak(PICCOLO) / _peak(FLUTE), 2.0, delta=0.05)

    def test_the_piccolo_plays_with_its_defaults(self) -> None:
        self.assertGreater(features(render(PICCOLO, {}, seconds=0.8)).peak, 1e-3)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        loudest = {
            "brightness": Piccolo.brightness.spec.maximum,
            "breath": Piccolo.breath.spec.maximum,
            "tongue": Piccolo.tongue.spec.maximum,
            "overtones": Piccolo.overtones.spec.maximum,
            "air_focus": Piccolo.air_focus.spec.maximum,
            "reverb_bal": Piccolo.reverb_bal.spec.maximum,
        }
        result = render(PICCOLO, loudest, seconds=2.4, bpm=BPM)

        self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)


if __name__ == "__main__":
    unittest.main()
