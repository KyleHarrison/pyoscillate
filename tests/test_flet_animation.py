import asyncio
import unittest
from types import SimpleNamespace

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.params import Param
from src.flet.base import PatchPanel, PatchRackApp, SweepRow
from src.flet.timeline import EvolveTimeline


class _Sweep:
    """The parts of a `Sweep` that `SweepRow` reads."""

    def __init__(self) -> None:
        self.param = SimpleNamespace(
            spec=SimpleNamespace(minimum=0.0, maximum=1.0, format=str, divisions=None)
        )
        self.enabled = True
        self.running = True
        self.low, self.high, self.bars = 0.0, 1.0, 4.0
        self.position = 0.0
        self.patch = SimpleNamespace(tempo=SimpleNamespace(bar=2.0))

    def value_at(self, position: float) -> float:
        return position


class _Evolution:
    """The parts of an `Evolution` that `EvolveTimeline` reads."""

    axis = None
    enabled = False
    bars = 8
    choices: tuple = ()
    label = "Evolve"

    def __init__(self) -> None:
        self.ticking = True
        self.progress = 0.0

    def rotation(self, count: int) -> tuple:
        return ()


class SweepRowRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sweep = _Sweep()
        self.row = SweepRow(self.sweep, plain_slider=SimpleNamespace())  # type: ignore[arg-type]
        self.row.width = 240.0
        self.row.refresh()

    def test_a_dot_that_moved_is_the_only_thing_repainted(self) -> None:
        self.sweep.position = 0.5

        changed = self.row.refresh()

        self.assertIn(self.row.dot, changed)

    def test_a_dot_that_has_not_moved_repaints_nothing(self) -> None:
        self.sweep.position = 0.5
        self.row.refresh()

        self.assertEqual(self.row.refresh(), [])

    def test_a_sub_pixel_step_is_held_back_until_it_adds_up(self) -> None:
        self.sweep.position = 0.5
        self.row.refresh()

        self.sweep.position = 0.5 + 0.1 / 200
        self.assertEqual(self.row.refresh(), [])

        self.sweep.position = 0.5 + 1.0 / 200
        self.assertIn(self.row.dot, self.row.refresh())

    def test_a_stopped_sweep_hides_its_markers_once(self) -> None:
        self.sweep.running = False

        self.assertEqual(self.row.refresh(), [self.row.dot, self.row.trail])
        self.assertFalse(self.row.dot.visible)
        self.assertEqual(self.row.refresh(), [])


class TimelinePlayheadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evolution = _Evolution()
        self.timeline = EvolveTimeline(self.evolution)  # type: ignore[arg-type]

    def test_a_playhead_that_moved_a_pixel_is_repainted(self) -> None:
        self.evolution.progress = 0.5

        self.assertEqual(self.timeline.refresh(), [self.timeline.playhead])
        self.assertEqual(len(self.timeline.playhead.shapes), 1)

    def test_a_playhead_that_barely_moved_is_left_alone(self) -> None:
        self.evolution.progress = 0.5
        self.timeline.refresh()

        self.evolution.progress = 0.5 + 0.5 / self.timeline.width

        self.assertEqual(self.timeline.refresh(), [])

    def test_a_playhead_is_removed_when_the_clock_stops(self) -> None:
        self.evolution.progress = 0.5
        self.timeline.refresh()
        self.evolution.ticking = False

        self.assertEqual(self.timeline.refresh(), [self.timeline.playhead])
        self.assertEqual(self.timeline.playhead.shapes, [])
        self.assertEqual(self.timeline.refresh(), [])


class _Voice(Patch):
    name = "voice"
    title = "Voice"
    summary = "Voice."
    level = Param(0.0, 1.0, 0.1, 0.5, "Level", "Level.")

    def build(self, context: BuildContext) -> Patch:
        return self


class OnScreenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.panel = PatchPanel(_Voice())
        self.panel.tile_height = 200.0

    def test_a_tile_with_no_measured_position_counts_as_in_view(self) -> None:
        self.assertTrue(self.panel.on_screen(100.0, 900.0))

    def test_a_tile_far_below_the_page_is_out_of_view(self) -> None:
        self.panel.origin = (0.0, 5000.0)

        self.assertFalse(self.panel.on_screen(100.0, 900.0))

    def test_the_margin_keeps_a_tile_just_out_of_view_live(self) -> None:
        self.panel.origin = (0.0, 1000.0)

        self.assertFalse(self.panel.on_screen(100.0, 900.0))
        self.assertTrue(self.panel.on_screen(100.0, 900.0, margin=800.0))

    def test_scrolling_carries_a_measured_position(self) -> None:
        self.panel.origin = (0.0, 5000.0)
        self.panel.scroll_source = lambda: 4500.0

        self.assertTrue(self.panel.on_screen(100.0, 900.0))

    def test_a_layout_change_forgets_the_position(self) -> None:
        self.panel.origin = (0.0, 5000.0)

        self.panel.forget_origin()

        self.assertTrue(self.panel.on_screen(100.0, 900.0))


class AnimationFrameTests(unittest.TestCase):
    """The loop draws only open tiles that are in view."""

    def setUp(self) -> None:
        self.shown = _Voice()
        self.panels = {
            "open": PatchPanel(_Voice()),
            "folded": PatchPanel(_Voice()),
            "far": PatchPanel(_Voice()),
        }
        self.panels["open"].set_expanded(True)
        self.panels["far"].set_expanded(True)
        self.panels["far"].tile_height = 200.0
        self.panels["far"].origin = (0.0, 90000.0)
        self.calls: list[tuple[str, bool]] = []
        for name, panel in self.panels.items():
            panel.refresh_live = lambda name=name: self.calls.append((name, True)) or []  # type: ignore[method-assign]
            panel.refresh_analysis = lambda on_screen=True, name=name: (  # type: ignore[method-assign]
                self.calls.append((name, on_screen)) or False
            )
        self.app = SimpleNamespace(
            panels=self.panels,
            running=True,
            list_top=100.0,
            viewport_height=800.0,
            pinned_panel=None,
            _progression_value=lambda: None,
            progression_dropdown=SimpleNamespace(value=None),
        )

    def test_only_open_tiles_in_view_are_refreshed(self) -> None:
        asyncio.run(PatchRackApp._animate_frame(self.app))  # type: ignore[arg-type]

        self.assertIn(("open", True), self.calls)
        self.assertNotIn(("folded", True), self.calls)
        self.assertNotIn(("far", True), self.calls)
        # a folded or distant tile releases its scope
        self.assertIn(("folded", False), self.calls)
        self.assertIn(("far", False), self.calls)

    def test_a_frame_reports_how_long_it_took(self) -> None:
        seconds = asyncio.run(PatchRackApp._animate_frame(self.app))  # type: ignore[arg-type]

        self.assertGreaterEqual(seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
