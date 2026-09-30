import unittest

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import render
from pyoscillate.harmony import C, Harmony
from pyoscillate.patches.tonal.pluck.pluck import (
    FULL_PATTERN,
    SPARSE_PATTERN,
    PluckHook,
)
from pyoscillate.patches.utility.notes import notes
from pyoscillate.patches.utility.notes.notes import freq_to_midi


class FixedClock:
    """Stands in for the shared clock and its division: `tick` is the step
    index since every step is one tick wide."""

    steps = 1

    def __init__(self, tick: int) -> None:
        self.tick = tick


class PluckHookTests(unittest.TestCase):
    @staticmethod
    def hit_steps(patch: PluckHook) -> set[int]:
        hits: set[int] = set()
        for tick in range(PluckHook.cycle):
            patch._clock = FixedClock(tick)
            patch._division = FixedClock(tick)
            if patch._step().hit:
                hits.add(tick)
        return hits

    def test_pattern_evolution_alternates_sparse_and_full_phrases(self) -> None:
        patch = PluckHook()

        patch.on_evolve(0)
        self.assertEqual(self.hit_steps(patch), set(SPARSE_PATTERN))
        patch.on_evolve(1)
        self.assertEqual(self.hit_steps(patch), set(FULL_PATTERN))

    def test_hook_tracks_diatonic_chord_triads_in_upper_register(self) -> None:
        patch = PluckHook()
        patch.harmony = Harmony(key=C, progression=(2, 7, 0, 9))
        expected_roots = (notes.D4, notes.G4, notes.C4, notes.A4)

        for bar_index, expected in enumerate(expected_roots):
            with self.subTest(bar=bar_index):
                actual = patch._note_frequency(0, bar_index)
                self.assertAlmostEqual(
                    freq_to_midi(actual), freq_to_midi(expected), places=4
                )

    def test_sparse_phrase_leaves_rests(self) -> None:
        self.assertLess(len(SPARSE_PATTERN), PluckHook.cycle)
        self.assertEqual(len(FULL_PATTERN), PluckHook.cycle)

    def test_render_is_silent_until_the_shared_clock_ticks(self) -> None:
        result = features(
            render(
                "pyoscillate.patches.tonal.pluck.pluck",
                {},
                seconds=0.5,
                clock_running=False,
            )
        )

        self.assertLess(result.peak, 1e-4)

    def test_render_sounds_after_the_shared_clock_starts(self) -> None:
        result = features(
            render(
                "pyoscillate.patches.tonal.pluck.pluck",
                {},
                seconds=0.5,
                clock_running=True,
            )
        )

        self.assertGreater(result.peak, 1e-4)


if __name__ == "__main__":
    unittest.main()
