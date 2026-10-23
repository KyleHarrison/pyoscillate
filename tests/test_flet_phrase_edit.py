import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest import mock

import flet.canvas as cv

import flet as ft
from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, start_server
from pyoscillate.patches.drums.kick.kick import KickLofi
from pyoscillate.tempo import Tempo
from src.flet.timeline import EvolveTimeline


class PhraseEditTests(unittest.TestCase):
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
        self.kick = KickLofi()
        self.kick.build(BuildContext(Tempo(bpm=120), self.clock, Harmony()))
        self.evolution = self.kick.phrase_evolution
        # canvases are not on a page here, so a repaint is a no-op
        patcher = mock.patch.object(cv.Canvas, "update")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.timeline = EvolveTimeline(self.evolution)
        self.timeline.width = 400.0
        self.timeline.redraw()

    def tap(self, x: float) -> None:
        self.timeline._handle_tap(
            ft.TapEvent(
                name="tap_down",
                control=self.timeline.control,
                local_position=ft.Offset(x, 30),
            )
        )

    def steps(self) -> set[int]:
        return {step.at for step in self.kick.selected_phrase.steps}

    def test_tap_adds_then_removes_a_step(self) -> None:
        before = self.steps()
        phrase = self.kick.selected_phrase
        cell = self.timeline._block_width / (self.timeline._span * phrase.division)
        free = next(i for i in range(phrase.cycle) if i not in before)
        self.tap((free + 0.5) * cell)
        self.assertEqual(self.steps(), before | {free})
        self.assertIs(self.evolution.current, self.kick.selected_phrase)
        self.tap((free + 0.5) * cell)
        self.assertEqual(self.steps(), before)

    def test_hover_draws_guides_on_the_cell_and_leaving_clears_them(self) -> None:
        phrase = self.kick.selected_phrase
        cell = self.timeline._block_width / (self.timeline._span * phrase.division)
        self.timeline._handle_hover(
            SimpleNamespace(local_position=ft.Offset(cell * 2.4, 30))  # type: ignore[arg-type]
        )
        vertical, horizontal, marker = self.timeline.guide.shapes
        self.assertAlmostEqual(vertical.x1, cell * 2)
        self.assertEqual(horizontal.x2, self.timeline._edit_width(phrase))
        self.assertIsInstance(marker, cv.Circle)
        self.timeline._clear_guide()
        self.assertEqual(self.timeline.guide.shapes, [])

    def test_editing_a_patch_not_built_yet_waits_for_the_build(self) -> None:
        unbuilt = KickLofi()
        timeline = EvolveTimeline(unbuilt.phrase_evolution)
        timeline.width = 400.0
        timeline.redraw()
        phrase = unbuilt.selected_phrase
        unbuilt.edit_phrase(replace(phrase, steps=phrase.steps[:1]))
        self.assertEqual(len(unbuilt.selected_phrase.steps), 1)
        unbuilt.build(BuildContext(Tempo(bpm=120), self.clock, Harmony()))
        self.assertEqual(len(unbuilt.selected_phrase.steps), 1)

    def test_only_the_first_cycle_takes_taps(self) -> None:
        phrase = self.kick.selected_phrase
        edit_width = self.timeline._edit_width(phrase)
        self.assertLessEqual(edit_width, self.timeline._block_width)
        if edit_width < self.timeline._block_width:
            self.tap(edit_width + 1)
            self.assertIsNone(self.kick.edited_phrase)

    def test_picking_another_phrase_drops_the_edit(self) -> None:
        self.tap(1)
        self.assertIsNotNone(self.kick.edited_phrase)
        self.kick.phrase = self.evolution.options[1]
        self.assertIsNone(self.kick.edited_phrase)


if __name__ == "__main__":
    unittest.main()
