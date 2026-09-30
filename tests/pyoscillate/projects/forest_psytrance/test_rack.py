import unittest

from pyoscillate.patches.drums.hat.groove import GrooveForest
from pyoscillate.patches.drums.kick.kick import KickPunch
from pyoscillate.patches.tonal.bass.groove import BassForest
from pyoscillate.patches.tonal.lead.fm import LeadFmSwirl, LeadFmWind
from pyoscillate.patches.utility.notes import notes
from pyoscillate.projects.forest_psytrance.rack import ForestPsytranceRack


class ForestPsytranceRackTests(unittest.TestCase):
    def test_declares_the_groups_in_display_order(self) -> None:
        rack = ForestPsytranceRack()

        self.assertEqual(
            [group.title for group in rack.groups],
            ["Kick", "Bass", "Hi-hats", "Leads"],
        )
        self.assertEqual(
            [[type(patch) for patch in group.patches] for group in rack.groups],
            [[KickPunch], [BassForest], [GrooveForest], [LeadFmWind, LeadFmSwirl]],
        )

    def test_runs_at_160_bpm(self) -> None:
        self.assertEqual(ForestPsytranceRack.bpm, 160)

    def test_bass_ducks_off_the_kick_group(self) -> None:
        rack = ForestPsytranceRack()

        (sidechain,) = rack.bass_forest.sidechains
        self.assertIs(sidechain.group, rack.kick_group)

    def test_leads_evolve_on_their_own_timer(self) -> None:
        rack = ForestPsytranceRack()

        self.assertEqual([group.title for group in rack.evolving_groups], ["Leads"])

    def test_harmony_stays_on_f_and_leans_on_the_flat_second(self) -> None:
        harmony = ForestPsytranceRack().harmony

        roots = [harmony.chord_freq(notes.F1, bar) for bar in range(8)]

        for root, expected in zip(roots, [notes.F1] * 6 + [notes.Fs1] * 2):
            self.assertAlmostEqual(root, expected, delta=0.01)


if __name__ == "__main__":
    unittest.main()
