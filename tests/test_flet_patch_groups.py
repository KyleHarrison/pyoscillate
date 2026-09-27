import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import flet as ft
from pyoscillate.controller import GroupController
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.projects.deep_house.rack import DeepHouseRack
from pyoscillate.projects.lofi.boom_bap.rack import LofiRack
from pyoscillate.projects.psyambient.rack import PsyambientRack
from src.flet.base import PatchGroup, PatchPanel, PatchRackApp

DEEP_HOUSE_GROUPS = DeepHouseRack().groups
PATCH_GROUPS = PsyambientRack().groups


class _StubPatch(Patch):
    """Minimal concrete `Patch` for exercising `PatchPanel`/`PatchGroup`
    wiring without a real Pyo graph."""

    parameters = ()

    def build(self, **kwargs: Any) -> Patch:
        self.sequencer = MagicMock()
        self.voice = MagicMock()
        return self


class PatchGroupTests(unittest.TestCase):
    def _contains_control(self, root: ft.Control, target: ft.Control) -> bool:
        if root is target:
            return True
        controls = getattr(root, "controls", None) or []
        content = getattr(root, "content", None)
        return any(self._contains_control(child, target) for child in controls) or (
            content is not None and self._contains_control(content, target)
        )

    def setUp(self) -> None:
        self.voice = _StubPatch(name="test_patch", title="Test Patch", summary="Test voice.")
        self.build = MagicMock(wraps=self.voice.build)
        self.voice.build = self.build
        self.rack = MagicMock()
        self.rack.get.return_value = None
        self.panel = PatchPanel(self.rack, self.voice)
        self.group = PatchGroup(GroupController("test", "Test Group", (self.voice,)), [self.panel])
        self.panel.set_engine_ready(True)
        self.group.set_engine_ready(True)
        self.panel.enabled = True
        self.panel.switch.value = True
        self.rack.reset_mock()

    def test_disabling_group_stops_patch_without_clearing_selection(self) -> None:
        event = SimpleNamespace(control=SimpleNamespace(value=False), page=MagicMock())

        self.group._handle_enabled(event)

        self.rack.stop.assert_called_once_with("test_patch")
        self.assertTrue(self.panel.enabled)
        self.assertTrue(self.panel.switch.value)
        self.assertTrue(self.panel.switch.disabled)

    def test_reenabling_group_starts_selected_patch(self) -> None:
        self.group.enabled = False
        self.panel.set_group_enabled(False)
        self.rack.reset_mock()
        event = SimpleNamespace(control=SimpleNamespace(value=True), page=MagicMock())

        self.group._handle_enabled(event)

        self.build.assert_called_once_with()
        self.rack.start.assert_called_once_with("test_patch", self.voice)
        self.assertEqual(self.voice.volume, self.panel.volume)
        self.assertFalse(self.panel.switch.disabled)

    def test_group_collapses_around_full_width_patch_controls(self) -> None:
        group_tile = self.group.control.content
        self.assertIsInstance(group_tile, ft.ExpansionTile)
        self.assertFalse(group_tile.expanded)

        group_content = group_tile.controls[0].content
        self.assertIsInstance(group_content.controls[-1], ft.ResponsiveRow)
        patch_column = group_content.controls[-1].controls[0]
        self.assertEqual(patch_column.col, {"xs": 12, "md": 12})

        patch_content = self.panel.control.content
        self.assertIsInstance(patch_content, ft.Column)
        self.assertIsInstance(patch_content.controls[-1], ft.ResponsiveRow)
        self.assertFalse(
            any(isinstance(control, ft.ExpansionTile) for control in patch_content.controls)
        )

    def test_slider_help_text_is_above_track_and_larger(self) -> None:
        spec = SliderSpec("test_value", 0.0, 1.0, 0.1, 0.5, "Test value", "Helpful detail")
        self.voice.test_value = spec.default

        row = self.panel._slider_row(spec)
        controls = row.content.controls

        self.assertEqual(controls[1].value, spec.help_text)
        self.assertEqual(controls[1].size, 12)
        self.assertIs(controls[2], self.panel._sliders[spec.name])

    def test_rack_wide_controls_are_in_header_right_column(self) -> None:
        with TemporaryDirectory() as catalog_dir:
            page = MagicMock()
            app = PatchRackApp(
                page,
                "Lofi Rack",
                "Test rack",
                LofiRack(),
                catalog_dir=Path(catalog_dir),
            )

        self.assertFalse(page.window.full_screen)
        self.assertTrue(page.window.maximized)
        root = page.add.call_args.args[0]
        self.assertEqual(len(root.controls), 2)
        header = root.controls[0]
        self.assertIsInstance(header.content, ft.ResponsiveRow)
        right_column = header.content.controls[1]
        for control in (
            app.engine_button,
            app.pause_button,
            app.preset_dropdown,
            app.preset_name_field,
            app.key_dropdown,
            app.macro_slider,
            app.master_output_slider,
        ):
            self.assertTrue(self._contains_control(right_column, control))

    def test_pause_resumes_only_patches_that_were_enabled(self) -> None:
        with TemporaryDirectory() as catalog_dir:
            page = MagicMock()
            app = PatchRackApp(
                page,
                "Lofi Rack",
                "Test rack",
                LofiRack(),
                catalog_dir=Path(catalog_dir),
            )

        app.server = MagicMock()
        enabled_names = list(app.panels)[:2]
        for name in enabled_names:
            app.panels[name].enabled = True
            app.panels[name].switch.value = True
        for panel in app.panels.values():
            panel._apply = MagicMock()

        app._toggle_pause()

        self.assertEqual(app._paused_panels, set(enabled_names))
        self.assertTrue(all(not panel.enabled for panel in app.panels.values()))
        self.assertEqual(app.pause_button.text, "Start")

        app.panels[list(app.panels)[-1]].enabled = True
        app._toggle_pause()

        self.assertEqual(
            {name for name, panel in app.panels.items() if panel.enabled},
            set(enabled_names),
        )
        self.assertEqual(app._paused_panels, None)
        self.assertEqual(app.pause_button.text, "Pause")

    def test_psyambient_declares_conceptual_groups(self) -> None:
        self.assertEqual(
            [group.name for group in PATCH_GROUPS],
            ["soundscapes", "mid", "bass"],
        )
        self.assertEqual([len(group.patches) for group in PATCH_GROUPS], [3, 3, 3])

    def test_deep_house_drums_group_holds_snare_tom_and_cymbals(self) -> None:
        drums = next(group for group in DEEP_HOUSE_GROUPS if group.name == "drums")

        self.assertEqual(drums.title, "Drums")
        self.assertEqual(
            [patch.name for patch in drums.patches],
            ["snare", "tom", "cymbal_ride", "cymbal_crash"],
        )


if __name__ == "__main__":
    unittest.main()
