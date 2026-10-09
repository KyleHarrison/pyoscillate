"""What is specific to the electric guitar: the amplifier (the string, its
Body and the rest are covered for every plucked instrument in `test_string.py`)."""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import spectral_centroid
from pyoscillate.analysis.render import Render, render

MODULE = "pyoscillate.patches.tonal.pluck.guitar"
BPM = 120
RATE = 44100
# the electric strikes every quarter second, and its output fades in over
# ~0.2 s: measure the first strike once the fade is over and before the next
FIRST = (0.3, 0.45)


@cache
def _render(**params: float) -> Render:
    return render(MODULE, {"style": "electric", **params}, seconds=1.2, bpm=BPM)


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _rms(samples: np.ndarray) -> float:
    return float(np.sqrt((samples**2).mean()))


def _centroid(result: Render, span: tuple[float, float]) -> float:
    return spectral_centroid(_window(result, span), RATE)


class GuitarElectricTests(unittest.TestCase):
    # the electric strikes every quarter second: measure inside one note
    ELECTRIC_STRIKE = (0.51, 0.57)
    ELECTRIC_TAIL = (0.7, 0.74)

    def test_drive_flattens_the_note_so_the_tail_keeps_up_with_the_strike(
        self,
    ) -> None:
        def tail_to_strike(drive: float) -> float:
            result = _render(drive=drive)
            return _rms(_window(result, self.ELECTRIC_TAIL)) / _rms(
                _window(result, self.ELECTRIC_STRIKE)
            )

        self.assertGreater(tail_to_strike(1.0), 1.1 * tail_to_strike(0.0))

    def test_tone_brightens_the_amp(self) -> None:
        dark = _centroid(_render(tone=0.0), FIRST)
        bright = _centroid(_render(tone=1.0), FIRST)

        self.assertGreater(bright, 1.2 * dark)

    def test_drive_keeps_the_note_at_a_similar_level(self) -> None:
        clean = _rms(_window(_render(drive=0.0), FIRST))
        driven = _rms(_window(_render(drive=1.0), FIRST))

        self.assertLess(driven, 2.0 * clean)
        self.assertGreater(driven, 0.5 * clean)


if __name__ == "__main__":
    unittest.main()
