"""Rhythmic contract for the forest bass: it rests on every beat, where the
kick lands, and rolls the three 16ths between kicks.

Steps are 16ths at 160 BPM. The first bar sits under `Patch.start()`'s
fade-in, so the beat measured is the third one (step 8).
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import to_db
from pyoscillate.analysis.render import Render, render
from pyoscillate.theory.intervals import Melody

MODULE = "pyoscillate.patches.tonal.bass.groove"
BPM = 160
SIXTEENTH = 60 / BPM / 4
LATENCY = 0.006


@cache
def _render() -> Render:
    return render(MODULE, {"style": "forest"}, seconds=2.0, bpm=BPM)


def _step_rms_db(result: Render, step: int) -> float:
    onset = step * SIXTEENTH + LATENCY
    rate = result.sample_rate
    window = result.samples[round(onset * rate) : round((onset + 0.06) * rate)]
    return to_db(float(np.sqrt(np.mean(window**2))))


class ForestBassTests(unittest.TestCase):
    def test_gates_rest_on_every_beat(self) -> None:
        steps = Melody.BASS_FOREST.steps

        self.assertEqual(
            [step for step in range(16) if step not in steps], [0, 4, 8, 12]
        )

    def test_rests_on_the_beat_and_rolls_between_kicks(self) -> None:
        result = _render()
        rest = _step_rms_db(result, 8)

        for step in (9, 10, 11):
            with self.subTest(step=step):
                self.assertGreater(_step_rms_db(result, step) - rest, 15)


if __name__ == "__main__":
    unittest.main()
