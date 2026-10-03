import unittest

from pyoscillate.patches.drums.kick.kick import Kick
from pyoscillate.patches.musical.stab.stab import Stab
from pyoscillate.patches.tonal.bass.groove import GrooveBass
from pyoscillate.projects.deep_house.rack import DeepHouseRack


class DeepHouseRackTests(unittest.TestCase):
    def test_declares_rhythm_and_harmony_sections(self) -> None:
        rack = DeepHouseRack()

        self.assertEqual([group.title for group in rack.groups], ["Rhythm", "Harmony"])
        self.assertEqual(
            [
                group.title
                for group in rack.group_for(DeepHouseRack.rhythm_group).children
            ],
            ["Kicks", "Claps", "Hi-hats", "Percussion", "Drums"],
        )

    def test_every_bass_and_chord_style_ducks_off_the_kicks(self) -> None:
        rack = DeepHouseRack()

        for group in (DeepHouseRack.bass_group, DeepHouseRack.chords_group):
            for slot in group.slots:
                (sidechain,) = rack.patch_for(slot).sidechains
                self.assertIs(sidechain.group, rack.kicks_group)

    def test_outer_controls_move_the_inner_ones(self) -> None:
        rack = DeepHouseRack()

        rack.harmony_group.apply(DeepHouseRack.harmony_warmth, 1.0)
        rack.rhythm_group.apply(DeepHouseRack.rhythm_drive, 1.0)

        for slot in DeepHouseRack.bass_group.slots:
            self.assertEqual(rack.patch_for(slot).cutoff, 1800)
        for slot in DeepHouseRack.chords_group.slots:
            self.assertEqual(rack.patch_for(slot).brightness, 5000)
        for slot in DeepHouseRack.kicks_group.slots:
            self.assertAlmostEqual(rack.patch_for(slot).punch, 1.6)

    def test_slider_starts_match_the_patch_defaults(self) -> None:
        rack = DeepHouseRack()

        for slot in DeepHouseRack.bass_group.slots:
            self.assertEqual(
                rack.patch_for(slot).cutoff, GrooveBass.cutoff.spec.default
            )
        for slot in DeepHouseRack.chords_group.slots:
            self.assertEqual(
                rack.patch_for(slot).brightness, Stab.brightness.spec.default
            )
        for slot in DeepHouseRack.kicks_group.slots:
            self.assertEqual(rack.patch_for(slot).punch, Kick.punch.spec.default)


if __name__ == "__main__":
    unittest.main()
