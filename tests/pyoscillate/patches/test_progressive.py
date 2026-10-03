import unittest

from pyoscillate.patches.common import Progressive
from pyoscillate.patches.evolve import Evolve
from pyoscillate.patches.tonal.keys.keys import Keys
from pyoscillate.patches.tonal.pluck.pluck import PluckHook
from pyoscillate.projects.deep_house.rack import DeepHouseRack
from pyoscillate.theory.phrase import Hooks, Phrases
from pyoscillate.theory.progression import Progressions


class ProgressionPhraseTests(unittest.TestCase):
    def test_a_progression_is_not_offered_as_a_phrase(self) -> None:
        self.assertFalse(set(Phrases.members()) & set(Progressions.members()))


class ProgressiveEvolutionTests(unittest.TestCase):
    def test_a_patch_starts_on_the_static_tonic(self) -> None:
        self.assertIs(Keys().selected_progression, Progressions.STATIC)

    def test_evolve_rotates_the_ticked_progressions_on_the_patch(self) -> None:
        patch = Keys()
        patch.declare_evolution(
            Evolve(
                4,
                (Progressions.FOUR_CHORD, Progressions.JAZZ_TURNAROUND),
            )
        )

        patch.progression_evolution.advance()
        self.assertIs(patch.selected_progression, Progressions.FOUR_CHORD)
        patch.progression_evolution.advance()
        self.assertIs(patch.selected_progression, Progressions.JAZZ_TURNAROUND)
        patch.progression_evolution.advance()
        self.assertIs(patch.selected_progression, Progressions.FOUR_CHORD)

    def test_phrases_and_progressions_rotate_independently(self) -> None:
        patch = PluckHook()
        patch.declare_evolution(
            Evolve(
                4,
                (
                    Hooks.SPARSE_HOOK,
                    Hooks.FULL_HOOK,
                    Progressions.DOO_WOP,
                    Progressions.MINOR_POP,
                ),
            )
        )
        start = patch.selected_phrase

        patch.progression_evolution.advance()

        # the progression moved, the phrase did not: each has its own timer
        self.assertIs(patch.selected_phrase, start)
        self.assertIs(patch.selected_progression, Progressions.DOO_WOP)

        patch.phrase_evolution.advance()

        self.assertIsNot(patch.selected_phrase, start)
        self.assertIs(patch.selected_progression, Progressions.DOO_WOP)

    def test_choices_go_to_the_dropdown_that_offers_them(self) -> None:
        patch = PluckHook()
        patch.declare_evolution(
            Evolve(4, (Hooks.FULL_HOOK, Progressions.DOO_WOP, Progressions.MINOR_POP))
        )

        self.assertEqual(patch.phrase_evolution.choices, (Hooks.FULL_HOOK,))
        self.assertEqual(
            patch.progression_evolution.choices,
            (Progressions.DOO_WOP, Progressions.MINOR_POP),
        )

    def test_the_two_timers_keep_their_own_intervals(self) -> None:
        patch = PluckHook()
        patch.declare_evolution(Evolve(4, (Hooks.FULL_HOOK, Progressions.DOO_WOP)))
        patch.progression_evolution.configure(16)

        self.assertEqual(patch.phrase_evolution.bars, 4)
        self.assertEqual(patch.progression_evolution.bars, 16)

    def test_choices_for_one_dropdown_leave_the_other_off(self) -> None:
        patch = PluckHook()
        patch.declare_evolution(Evolve(4, (Hooks.FULL_HOOK,)))

        self.assertTrue(patch.phrase_evolution.enabled)
        self.assertFalse(patch.progression_evolution.enabled)

    def test_one_progression_ticked_holds_still(self) -> None:
        patch = Keys(progression=Progressions.DOO_WOP)
        patch.progression_evolution.advance()
        self.assertIs(patch.selected_progression, Progressions.DOO_WOP)


class RackSeedingTests(unittest.TestCase):
    def test_the_rack_puts_every_chord_following_patch_on_its_progression(self) -> None:
        rack = DeepHouseRack()
        followers = [
            patch
            for group in rack.groups
            for patch in group.patches
            if isinstance(patch, Progressive)
        ]

        self.assertTrue(followers)
        for patch in followers:
            self.assertIs(patch.selected_progression, Progressions.DEEP_HOUSE_MINOR)


if __name__ == "__main__":
    unittest.main()
