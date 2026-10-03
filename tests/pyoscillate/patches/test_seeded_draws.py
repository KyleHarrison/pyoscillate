"""`SeededDraws`: the same seed replays the same draws, a different seed or
an evolve re-roll changes them, and the mixin is on the random patches."""

import unittest

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import SeededDraws
from pyoscillate.patches.musical.canon.canon import Canon
from pyoscillate.patches.musical.generative.generative import Generative


class _Melody(SeededDraws, Patch):
    def build(self, context):
        return self

    def line(self) -> list[int]:
        return [self.draws.choice(range(100)) for _ in range(12)]


def _melody(seed: float) -> _Melody:
    patch = _Melody(seed=seed)
    SeededDraws.seed.control(patch, patch.seed)
    return patch


class SeededDrawsTests(unittest.TestCase):
    def test_same_seed_replays_the_same_melody(self) -> None:
        self.assertEqual(_melody(3).line(), _melody(3).line())

    def test_different_seeds_differ(self) -> None:
        self.assertNotEqual(_melody(3).line(), _melody(4).line())

    def test_evolve_rerolls_deterministically(self) -> None:
        first, again = _melody(3), _melody(3)
        before = first.line()
        first.on_evolve(0)
        again.on_evolve(0)

        rolled = first.line()
        self.assertNotEqual(rolled, before)
        self.assertEqual(rolled, again.line())

    def test_evolve_index_changes_the_roll(self) -> None:
        one, two = _melody(3), _melody(3)
        one.on_evolve(0)
        two.on_evolve(1)

        self.assertNotEqual(one.line(), two.line())

    def test_random_patches_use_it(self) -> None:
        for patch in (Generative, Canon):
            with self.subTest(patch=patch.__name__):
                self.assertTrue(issubclass(patch, SeededDraws))


if __name__ == "__main__":
    unittest.main()
