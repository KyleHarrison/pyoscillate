"""Note and chord names on the `EvolveTimeline`: the hook's dots are the notes
they sound, a chord rhythm's the chord, and the progression's chords carry
their names in the rack's key."""

import re
import unittest
from types import SimpleNamespace
from unittest import mock

import flet.canvas as cv
from flet.controls.base_control import BaseControl

import flet as ft
from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, start_server
from pyoscillate.patches.tonal.bass.groove import BassRolling
from pyoscillate.patches.tonal.keys.string_keys import Harpsichord
from pyoscillate.tempo import Tempo
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.phrase import Hooks, Rhythms
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.progression import Progressions
from src.flet.timeline import EvolveTimeline


class NoteNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server(audio="manual")
        cls.clock = Clock(Tempo(bpm=120))
        cls.clock.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.clock.stop()
        cls.server.stop()
        cls.server.shutdown()

    def setUp(self) -> None:
        patcher = mock.patch.object(BaseControl, "update")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.harmony = Harmony()
        self.harp = Harpsichord()
        self.harp.build(BuildContext(Tempo(bpm=120), self.clock, self.harmony))
        self.harp.progression = Progressions.JAZZ_TURNAROUND

    def texts(self, evolution) -> list[str]:
        timeline = EvolveTimeline(evolution)
        timeline.width = 900.0
        timeline.redraw()
        return [s.value for s in timeline.blocks.shapes if isinstance(s, cv.Text)]

    def test_chord_names_follow_the_key_and_scale(self) -> None:
        jazz = Progressions.JAZZ_TURNAROUND
        names = [self.harmony.chord_name(bar, jazz) for bar in range(4)]
        self.assertEqual(names, ["Bm", "E", "A", "F#m"])
        self.harmony.key = 0
        self.assertEqual(self.harmony.chord_name(0, jazz), "Dm")

    def test_the_progression_lane_names_each_chord(self) -> None:
        texts = self.texts(self.harp.progression_evolution)
        self.assertIn("II  Bm", texts)
        self.assertIn("V  E", texts)

    def test_hook_dots_are_the_notes_they_sound(self) -> None:
        self.harp.phrase = Hooks.SPARSE_HOOK
        texts = self.texts(self.harp.phrase_evolution)
        # Bm on the first bar: root, third, fifth, third, as the patch plays them
        played = [Note.name(self.harp.note_frequency(i, 0)) for i in (0, 1, 2, 1)]
        self.assertEqual(texts[1:5], played)
        self.assertEqual([name[:-1] for name in played], ["B", "D", "F#", "D"])

    def test_a_dense_chord_rhythm_names_the_chord_once_a_bar(self) -> None:
        self.harp.phrase = Rhythms.EIGHTH_PULSE
        texts = self.texts(self.harp.phrase_evolution)
        self.assertIn("Bm", texts)

    def test_a_quarter_pulse_dot_is_the_notes_of_the_chord(self) -> None:
        self.harp.phrase = Rhythms.QUARTER_PULSE
        texts = self.texts(self.harp.phrase_evolution)
        played = [Note.name(f) for f in self.harp.chord_frequencies(0, Chords.TRIAD)]
        self.assertEqual([n[:-1] for n in played], ["B", "D", "F#"])
        # the first hit, lowest note first, and the same chord on every beat
        self.assertEqual(texts[1:4], played)
        self.assertEqual(texts[1:4], texts[4:7])
        # the block's label, three notes for each of the 32 hits, 8 bar numbers
        self.assertEqual(len(texts), 1 + 3 * 32 + 8)

    def test_a_patch_that_is_not_built_yet_is_named_from_the_racks_harmony(
        self,
    ) -> None:
        idle = Harpsichord()
        idle.phrase = Rhythms.QUARTER_PULSE
        idle.progression = Progressions.JAZZ_TURNAROUND
        timeline = EvolveTimeline(idle.phrase_evolution)
        timeline.width = 900.0
        timeline.harmony = self.harmony
        timeline.redraw()
        texts = [s.value for s in timeline.blocks.shapes if isinstance(s, cv.Text)]
        self.assertEqual(texts[1:4], ["B3", "D4", "F#4"])
        chords = EvolveTimeline(idle.progression_evolution)
        chords.width = 900.0
        chords.harmony = self.harmony
        chords.redraw()
        self.assertIn(
            "II  Bm",
            [s.value for s in chords.blocks.shapes if isinstance(s, cv.Text)],
        )

    def test_a_new_key_renames_what_is_drawn(self) -> None:
        timeline = EvolveTimeline(self.harp.progression_evolution)
        timeline.width = 900.0
        timeline.redraw()
        self.harmony.key = 0
        timeline.redraw()
        texts = [s.value for s in timeline.blocks.shapes if isinstance(s, cv.Text)]
        self.assertIn("II  Dm", texts)

    def test_a_new_register_renames_the_notes(self) -> None:
        self.harp.phrase = Hooks.SPARSE_HOOK
        timeline = EvolveTimeline(self.harp.phrase_evolution)
        timeline.width = 900.0
        timeline.redraw()
        before = [s.value for s in timeline.blocks.shapes if isinstance(s, cv.Text)]
        self.harp.root_freq = Note.A4
        timeline.redraw()
        after = [s.value for s in timeline.blocks.shapes if isinstance(s, cv.Text)]
        self.assertNotEqual(before[1:5], after[1:5])

    def test_an_edited_progression_is_still_found_by_its_position(self) -> None:
        chords = EvolveTimeline(self.harp.progression_evolution)
        chords.width = 900.0
        chords.redraw()
        chords._edit_chord(Progressions.JAZZ_TURNAROUND, 5, 30)
        self.assertNotIn(self.harp.selected_progression, Progressions.members())
        self.assertEqual(
            int(self.harp.progression),
            Progressions.index_of(Progressions.JAZZ_TURNAROUND),
        )

    def test_a_new_register_renames_a_struck_chord(self) -> None:
        self.harp.phrase = Rhythms.QUARTER_PULSE
        timeline = EvolveTimeline(self.harp.phrase_evolution)
        timeline.width = 900.0
        timeline.redraw()
        before = [s.value for s in timeline.blocks.shapes if isinstance(s, cv.Text)]
        self.harp.root_freq = Note.A4
        timeline.redraw()
        after = [s.value for s in timeline.blocks.shapes if isinstance(s, cv.Text)]
        self.assertNotEqual(before, after)

    def test_crowded_dots_stay_dots_and_roomy_ones_are_named(self) -> None:
        bass = BassRolling()
        bass.build(BuildContext(Tempo(bpm=120), self.clock, self.harmony))

        def drawn() -> tuple[list[str], int]:
            timeline = EvolveTimeline(bass.phrase_evolution)
            timeline.width = 1200.0
            timeline.redraw()
            shapes = timeline.blocks.shapes
            notes = [
                s.value
                for s in shapes
                if isinstance(s, cv.Text) and re.fullmatch(r"[A-G][b#]?\d", s.value)
            ]
            return notes, sum(isinstance(s, cv.Circle) for s in shapes)

        # a sixteenth-note roll leaves no room between its hits
        notes, dots = drawn()
        self.assertEqual(notes, [])
        self.assertGreater(dots, 0)
        # a sparse line has room for every name
        bass.phrase = next(
            member
            for member in bass.phrase_evolution.options
            if len(member.steps) <= member.cycle // 4
        )
        notes, _ = drawn()
        self.assertTrue(notes)

    def test_hovering_a_step_names_its_note(self) -> None:
        self.harp.phrase = Hooks.SPARSE_HOOK
        timeline = EvolveTimeline(self.harp.phrase_evolution)
        timeline.width = 900.0
        timeline.redraw()
        phrase = self.harp.selected_phrase
        cell = timeline._block_width / (timeline._span * phrase.division)
        timeline._handle_hover(
            SimpleNamespace(local_position=ft.Offset(cell * 2.4, 30))
        )
        labels = [s.value for s in timeline.guide.shapes if isinstance(s, cv.Text)]
        expected = Note.name(self.harp.note_frequency(1, 0))
        self.assertEqual(labels, [expected])
