import unittest

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import render
from pyoscillate.harmony import Harmony
from pyoscillate.patches.tonal.pluck.pluck import PluckHook
from pyoscillate.theory.phrase import Hooks, Progressions
from pyoscillate.theory.pitch import Note


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
        for tick in range(patch.selected_phrase.cycle):
            patch._clock = FixedClock(tick)
            patch._division = FixedClock(tick)
            if patch._step().hit:
                hits.add(tick)
        return hits

    def test_pattern_evolution_alternates_sparse_and_full_phrases(self) -> None:
        patch = PluckHook()
        patch._base_division = PluckHook.base_division

        # the patch isn't built, so apply the dropdown's control by hand
        patch.evolution.set_choice(Hooks.FULL_HOOK, True)
        patch.use_phrase(patch.selected_phrase)
        self.assertEqual(self.hit_steps(patch), set(Hooks.SPARSE_HOOK.values))
        patch.on_evolve(0)
        patch.use_phrase(patch.selected_phrase)
        self.assertEqual(self.hit_steps(patch), set(Hooks.FULL_HOOK.values))
        patch.on_evolve(1)
        patch.use_phrase(patch.selected_phrase)
        self.assertEqual(self.hit_steps(patch), set(Hooks.SPARSE_HOOK.values))

    def test_hook_tracks_diatonic_chord_triads_in_upper_register(self) -> None:
        patch = PluckHook()
        patch.harmony = Harmony(key=Note.KEY_C)
        patch.progression = Progressions.JAZZ_TURNAROUND
        expected_roots = (Note.D4, Note.G4, Note.C4, Note.A4)

        for bar_index, expected in enumerate(expected_roots):
            with self.subTest(bar=bar_index):
                actual = patch._note_frequency(0, bar_index)
                self.assertAlmostEqual(
                    Note.freq_to_midi(actual), Note.freq_to_midi(expected), places=4
                )

    def test_sparse_phrase_leaves_rests(self) -> None:
        self.assertLess(len(Hooks.SPARSE_HOOK.steps), Hooks.SPARSE_HOOK.cycle)
        self.assertEqual(len(Hooks.FULL_HOOK.steps), Hooks.FULL_HOOK.cycle)

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
