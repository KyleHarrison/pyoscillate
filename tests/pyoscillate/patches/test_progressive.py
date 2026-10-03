import unittest

from pyoscillate.patches.common import Progressive
from pyoscillate.patches.evolve import Evolve
from pyoscillate.patches.tonal.keys.keys import Keys
from pyoscillate.patches.tonal.pluck.pluck import PluckHook
from pyoscillate.projects.deep_house.rack import DeepHouseRack
from pyoscillate.theory.phrase import Hooks, PhraseRole, Phrases, Progressions


class ProgressionPhraseTests(unittest.TestCase):
    def test_progressions_are_phrases_with_their_own_role(self) -> None:
        self.assertEqual(
            Phrases.for_roles(PhraseRole.PROGRESSION).members(),
            Progressions.members(),
        )

    def test_no_role_but_progression_offers_a_progression_as_a_pattern(self) -> None:
        hook_catalog = Phrases.for_roles(PhraseRole.HOOK)
        self.assertFalse(set(hook_catalog.members()) & set(Progressions.members()))


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

        patch.on_evolve(0)
        self.assertIs(patch.selected_progression, Progressions.FOUR_CHORD)
        patch.on_evolve(1)
        self.assertIs(patch.selected_progression, Progressions.JAZZ_TURNAROUND)
        patch.on_evolve(2)
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

        patch.on_evolve(0)

        self.assertIsNot(patch.selected_phrase, start)
        self.assertIs(patch.selected_progression, Progressions.DOO_WOP)

    def test_one_progression_ticked_holds_still(self) -> None:
        patch = Keys(progression=Progressions.DOO_WOP)
        patch.on_evolve(0)
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
