"""Effect add-ons: each amount defaults to 0 (the voice is untouched) and is a
live, sweepable Param; renders use the real server in a subprocess."""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.fx import Comb, Disperse, Flood
from pyoscillate.patches.tonal.strings.strings import Strings

STRINGS = "pyoscillate.patches.tonal.strings.strings"


@cache
def _render(**params: float) -> Render:
    return render(STRINGS, dict(params), seconds=4.0)


class FxParamTests(unittest.TestCase):
    def test_amounts_default_off_and_sweep(self) -> None:
        for param in (Comb.comb, Disperse.disperse, Flood.flood):
            with self.subTest(param=param.spec.default):
                self.assertEqual(param.spec.default, 0.0)
                self.assertTrue(param.sweep)

    def test_strings_takes_all_three(self) -> None:
        for param in (Strings.comb, Strings.disperse, Strings.flood):
            self.assertIsNotNone(param)


class FxRenderTests(unittest.TestCase):
    @staticmethod
    def _rms(render_: Render) -> float:
        return float(np.sqrt(np.mean(np.square(render_.samples))))

    def test_default_leaves_the_voice_audible(self) -> None:
        self.assertGreater(self._rms(_render()), 0.001)

    def test_each_effect_changes_the_sound(self) -> None:
        dry = _render().samples
        for name in ("comb", "disperse", "flood"):
            with self.subTest(effect=name):
                wet = _render(**{name: 1.0}).samples
                n = min(len(dry), len(wet))
                self.assertGreater(float(np.mean(np.abs(dry[:n] - wet[:n]))), 1e-4)
                self.assertTrue(np.all(np.isfinite(wet)))


if __name__ == "__main__":
    unittest.main()
