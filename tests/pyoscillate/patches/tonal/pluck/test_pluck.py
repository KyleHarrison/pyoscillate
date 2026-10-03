import unittest

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import render
from pyoscillate.patches.tonal.pluck.pluck import PluckHook
from pyoscillate.theory import notes
from pyoscillate.theory.harmony import C, Harmony
from pyoscillate.theory.intervals import ChordTones
from pyoscillate.theory.notes import freq_to_midi


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
        for tick in range(patch.selected_figure.cycle):
            patch._clock = FixedClock(tick)
            patch._division = FixedClock(tick)
            if patch._step().hit:
                hits.add(tick)
        return hits

    def test_pattern_evolution_alternates_sparse_and_full_phrases(self) -> None:
        patch = PluckHook()
        patch._base_division = PluckHook.base_division

        # the patch isn't built, so apply the dropdown's control by hand
        patch.on_evolve(0)
        patch.use_figure(patch.selected_figure)
        self.assertEqual(self.hit_steps(patch), set(ChordTones.SPARSE_HOOK.steps))
        patch.on_evolve(1)
        patch.use_figure(patch.selected_figure)
        self.assertEqual(self.hit_steps(patch), set(ChordTones.FULL_HOOK.steps))

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
        self.assertLess(len(ChordTones.SPARSE_HOOK.steps), ChordTones.SPARSE_HOOK.cycle)
        self.assertEqual(len(ChordTones.FULL_HOOK.steps), ChordTones.FULL_HOOK.cycle)

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
