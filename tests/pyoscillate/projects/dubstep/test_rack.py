import unittest
from typing import ClassVar

from pyoscillate.patches.drums.hat.groove import GrooveHalfTime
from pyoscillate.patches.drums.kick.kick import KickDubstep
from pyoscillate.patches.drums.snare.snare import SnareHalfTime
from pyoscillate.patches.tonal.bass.reese.reese import ReeseHeave, ReeseWobble
from pyoscillate.patches.tonal.keys.string_keys import Piano
from pyoscillate.patches.tonal.strings.strings import Strings
from pyoscillate.patches.tonal.vocal.solo import VocalFemale
from pyoscillate.patches.transition.riser.riser import RiserNoise, RiserPitch
from pyoscillate.projects.dubstep.rack import DubstepRack
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase import BassLines, Leads, Rhythms
from pyoscillate.theory.pitch import Note


class DubstepRackTests(unittest.TestCase):
    def test_declares_the_groups_in_display_order(self) -> None:
        rack = DubstepRack()

        self.assertEqual(
            [group.title for group in rack.groups],
            ["Drums", "Bass", "Melody", "Build"],
        )
        self.assertEqual(
            [[type(patch) for patch in group.patches] for group in rack.groups],
            [
                [KickDubstep, SnareHalfTime, GrooveHalfTime],
                [ReeseWobble, ReeseHeave],
                [Piano, Strings, VocalFemale],
                [RiserNoise, RiserPitch],
            ],
        )

    def test_runs_at_140_bpm(self) -> None:
        self.assertEqual(DubstepRack.bpm, 140)

    def test_bass_and_melody_duck_off_the_kick_group(self) -> None:
        rack = DubstepRack()

        for slot in (
            rack.bass_wobble_slot,
            rack.bass_heave_slot,
        ):
            (sidechain,) = slot.sidechains
            self.assertIs(sidechain.group, rack.kick_group)
        piano, strings = rack.melody_group.patches[:2]
        for patch in (piano, strings):
            (sidechain,) = patch.sidechains
            self.assertIs(sidechain.group, rack.kick_group)

    def test_wobble_bass_alternates_its_line_every_8_bars(self) -> None:
        rack = DubstepRack()

        evolution = rack.bass_wobble_slot.phrase_evolution
        self.assertTrue(evolution.enabled)
        self.assertEqual(evolution.bars, 8)
        self.assertEqual(
            [phrase.id for phrase in evolution.choices],
            [BassLines.BASS_DROP.id, BassLines.BASS_DROP_B.id],
        )

    def test_chords_follow_the_epic_minor_cycle_in_f(self) -> None:
        rack = DubstepRack()
        bass = rack.bass_wobble_slot

        roots = [
            rack.harmony.chord_freq(Note.F1, bar, bass.selected_progression)
            for bar in range(8)
        ]

        expected = [
            Note.F1,
            Note.F1,
            Note.Cs1,
            Note.Cs1,
            Note.Gs1,
            Note.Gs1,
            Note.Ds1,
            Note.Ds1,
        ]
        for root, note in zip(roots, expected):
            self.assertAlmostEqual(root, note, delta=0.01)

    def test_sung_line_starts_on_the_anthem_phrase(self) -> None:
        rack = DubstepRack()

        vocal = rack.melody_group.patches[2]
        self.assertEqual(vocal.selected_phrase.id, Leads.ANTHEM.id)


class DubstepPhraseTests(unittest.TestCase):
    CHORD_NEUTRAL: ClassVar[set[Interval]] = {
        Interval.UNISON,
        Interval.PERFECT_FOURTH,
        Interval.PERFECT_FIFTH,
        Interval.OCTAVE,
        Interval.MAJOR_NINTH,
    }

    def test_snare_only_lands_on_beat_three(self) -> None:
        loud = [
            at for at, accent in Rhythms.SNARE_HALF_TIME.accents.items() if accent > 0.5
        ]

        self.assertEqual(loud, [8, 24])

    def test_kick_plays_beat_one_of_each_bar_and_never_the_snare(self) -> None:
        steps = Rhythms.KICK_HALF_TIME.accents

        self.assertIn(0, steps)
        self.assertIn(16, steps)
        self.assertNotIn(8, steps)
        self.assertNotIn(24, steps)

    def test_bass_never_strikes_a_note_on_the_snare(self) -> None:
        for line in (BassLines.BASS_DROP, BassLines.BASS_DROP_B, BassLines.BASS_HEAVE):
            with self.subTest(line=line.id):
                self.assertFalse({8, 24} & set(line.values))

    def test_bass_and_topline_intervals_suit_minor_and_major_chords(self) -> None:
        for line in (
            BassLines.BASS_DROP,
            BassLines.BASS_DROP_B,
            BassLines.BASS_HEAVE,
            Leads.ANTHEM,
        ):
            with self.subTest(line=line.id):
                self.assertLessEqual(
                    {Interval(step.offset) for step in line.steps}, self.CHORD_NEUTRAL
                )

    def test_notes_end_inside_their_cycle(self) -> None:
        for line in (
            BassLines.BASS_DROP,
            BassLines.BASS_DROP_B,
            BassLines.BASS_HEAVE,
            Leads.ANTHEM,
        ):
            with self.subTest(line=line.id):
                for step in line.steps:
                    self.assertLessEqual(step.at + step.length, line.cycle)


if __name__ == "__main__":
    unittest.main()
