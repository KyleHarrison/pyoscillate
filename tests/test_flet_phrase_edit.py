"""Editing a phrase or a progression on the `EvolveTimeline`: taps and drags
change the first cycle of a block, per choice, and the patch plays the edit."""

import unittest
from types import SimpleNamespace
from unittest import mock

from flet.controls.base_control import BaseControl

import flet as ft
from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, start_server
from pyoscillate.patches.tonal.bass.fm.fm import FmBassBark
from pyoscillate.tempo import Tempo
from pyoscillate.theory.progression import Progressions
from src.flet.timeline import EvolveTimeline


class TimelineEditTests(unittest.TestCase):
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
        # nothing is on a page here, so a repaint is a no-op
        patcher = mock.patch.object(BaseControl, "update")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.bass = FmBassBark()
        self.bass.build(BuildContext(Tempo(bpm=120), self.clock, Harmony()))
        self.phrases = self.bass.phrase_evolution
        # one with rests to put notes in
        self.bass.phrase = next(
            member
            for member in self.phrases.options
            if len(member.steps) < member.cycle // 2
        )
        self.chords = self.bass.progression_evolution

    def timeline(self, evolution, width: float = 400.0) -> EvolveTimeline:
        timeline = EvolveTimeline(evolution)
        timeline.width = width
        timeline.redraw()
        return timeline

    @staticmethod
    def at(x: float, y: float = 30) -> SimpleNamespace:
        return SimpleNamespace(local_position=ft.Offset(x, y))

    def test_tap_adds_then_removes_a_step(self) -> None:
        timeline = self.timeline(self.phrases)
        phrase = self.bass.selected_phrase
        before = {step.at for step in phrase.steps}
        cell = timeline._block_width / (timeline._span * phrase.division)
        free = next(i for i in range(phrase.cycle) if i not in before)
        timeline._handle_tap(self.at((free + 0.5) * cell))
        self.assertEqual(
            {s.at for s in self.bass.selected_phrase.steps}, before | {free}
        )
        self.assertIs(self.phrases.current, self.bass.selected_phrase)
        timeline._handle_tap(self.at((free + 0.5) * cell))
        self.assertEqual({s.at for s in self.bass.selected_phrase.steps}, before)

    def test_only_the_first_cycle_takes_taps(self) -> None:
        timeline = self.timeline(self.phrases)
        phrase = self.bass.selected_phrase
        edit_width = timeline._edit_width(phrase)
        if edit_width < timeline._block_width:
            timeline._handle_tap(self.at(edit_width + 1))
            self.assertIs(self.bass.selected_phrase, self.phrases.current_member)

    def test_hover_draws_guides_and_leaving_clears_them(self) -> None:
        timeline = self.timeline(self.phrases)
        phrase = self.bass.selected_phrase
        cell = timeline._block_width / (timeline._span * phrase.division)
        timeline._handle_hover(self.at(cell * 2.4))
        vertical, horizontal, *_ = timeline.guide.shapes
        self.assertAlmostEqual(vertical.x1, cell * 2)
        self.assertEqual(horizontal.x2, timeline._edit_width(phrase))
        timeline._clear_guide()
        self.assertEqual(timeline.guide.shapes, [])

    def test_an_edit_belongs_to_its_choice_and_survives_picking_another(self) -> None:
        first = self.phrases.current_member
        timeline = self.timeline(self.phrases)
        phrase = self.bass.selected_phrase
        cell = timeline._block_width / (timeline._span * phrase.division)
        free = next(
            i for i in range(phrase.cycle) if i not in {s.at for s in phrase.steps}
        )
        timeline._handle_tap(self.at((free + 0.5) * cell))
        other = next(member for member in self.phrases.options if member is not first)
        self.bass.phrase = other
        self.assertIs(self.bass.selected_phrase, other)
        self.bass.phrase = first
        self.assertIn(free, {s.at for s in self.bass.selected_phrase.steps})

    def test_every_evolved_block_edits_its_own_choice(self) -> None:
        sparse = [
            member
            for member in self.phrases.options
            if len(member.steps) < member.cycle // 2
        ]
        a, b, c = sparse[:3]
        self.phrases.choices = (a, b, c)
        self.phrases.enabled = True
        self.bass.phrase = a
        timeline = self.timeline(self.phrases)
        pitch = timeline._block_width + timeline.BLOCK_GAP
        second = timeline._choices[1]
        cell = timeline._block_width / (timeline._span * second.division)
        free = next(
            i for i in range(second.cycle) if i not in {s.at for s in second.steps}
        )
        timeline._handle_tap(self.at(pitch + (free + 0.5) * cell))
        self.assertIn(free, {s.at for s in self.phrases.resolve(b).steps})
        self.assertEqual(self.phrases.resolve(a), a)
        self.assertIs(self.bass.selected_phrase, a)

    def test_more_blocks_than_fit_scroll(self) -> None:
        self.phrases.choices = tuple(self.phrases.options[:8])
        self.phrases.enabled = True
        timeline = self.timeline(self.phrases, width=800.0)
        self.assertEqual(len(timeline._choices), 8)
        self.assertGreater(timeline._total, timeline.width)
        self.assertEqual(timeline.blocks.width, timeline._total)

    def test_the_line_holds_still_and_the_playhead_moves_on_when_it_evolves(
        self,
    ) -> None:
        a, b, c = self.phrases.options[:3]
        self.phrases.choices = (a, b, c)
        self.phrases.enabled = True
        self.bass.phrase = a
        timeline = self.timeline(self.phrases)
        before = [choice.id for choice in timeline._choices]
        self.assertEqual(timeline._now, 0)
        self.phrases.advance()
        timeline.redraw()
        self.assertEqual([choice.id for choice in timeline._choices], before)
        self.assertEqual(timeline._now, 1)
        # the playhead runs through the second block now
        with (
            mock.patch.object(
                type(self.phrases), "ticking", new_callable=mock.PropertyMock
            ) as ticking,
            mock.patch.object(
                type(self.phrases), "progress", new_callable=mock.PropertyMock
            ) as progress,
        ):
            ticking.return_value = True
            progress.return_value = 0.5
            timeline.refresh()
        pitch = timeline._block_width + timeline.BLOCK_GAP
        self.assertAlmostEqual(
            timeline.playhead.shapes[0].x1, pitch + 0.5 * timeline._block_width
        )

    def test_dragging_a_chord_bar_changes_its_root(self) -> None:
        self.bass.progression = Progressions.FOUR_CHORD
        timeline = self.timeline(self.chords)
        per_bar = timeline._block_width / timeline._span
        # the second chord, dragged to the top of the block
        timeline._handle_drag(self.at(per_bar * 1.5, timeline.BODY_TOP))
        roots = self.bass.selected_progression.roots
        self.assertEqual(roots[0], 0)
        self.assertEqual(roots[1], 11)
        self.assertIs(self.chords.current, self.bass.selected_progression)
        self.assertEqual(Progressions.FOUR_CHORD.roots, (0, 7, 9, 5))

    def test_an_unbuilt_patch_keeps_the_edit_for_its_build(self) -> None:
        unbuilt = FmBassBark()
        timeline = self.timeline(unbuilt.phrase_evolution)
        phrase = unbuilt.selected_phrase
        timeline._handle_tap(
            self.at(0.5 * timeline._block_width / (timeline._span * phrase.division))
        )
        edited = unbuilt.selected_phrase
        unbuilt.build(BuildContext(Tempo(bpm=120), self.clock, Harmony()))
        self.assertIs(unbuilt.selected_phrase, edited)


if __name__ == "__main__":
    unittest.main()
