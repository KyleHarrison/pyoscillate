import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock

import flet as ft
from pyoscillate.controller import GroupRuntime
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.drone.wash import SoundscapeWash
from pyoscillate.projects.deep_house.rack import DeepHouseRack
from pyoscillate.projects.lofi.boom_bap.rack import LofiRack
from pyoscillate.projects.lofi.slowed_reverb.rack import SlowedReverbRack
from pyoscillate.projects.psyambient.rack import PsyambientRack
from src.flet.base import PatchGroup, PatchPanel, PatchRackApp


class _StubPatch(Patch):
    """Minimal concrete `Patch` for exercising `PatchPanel`/`PatchGroup`
    wiring without a real Pyo graph."""

    name = "test_patch"
    title = "Test Patch"
    summary = "Test voice."

    test_value = Param(0.0, 1.0, 0.1, 0.5, "Test value", "Helpful detail")

    def build(self, context: BuildContext) -> Patch:
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
        self.voice = _StubPatch()
        self.voice.build = MagicMock(wraps=self.voice.build)
        self.voice.start = MagicMock()
        self.voice.stop = MagicMock()
        self.context = MagicMock()
        self.panel = PatchPanel(self.voice)
        self.group = PatchGroup(GroupRuntime("Test Group", (self.voice,)), [self.panel])
        self.panel.engine_started(self.context)
        self.group.set_engine_ready(True)
        self.panel.apply_enabled(True)
        self.voice.build.reset_mock()
        self.voice.start.reset_mock()
        self.voice.stop.reset_mock()

    def test_disabling_group_stops_patch_without_clearing_selection(self) -> None:
        event = SimpleNamespace(control=SimpleNamespace(value=False), page=MagicMock())

        self.group._handle_enabled(event)

        self.voice.stop.assert_called_once_with()
        self.assertTrue(self.panel.enabled)
        self.assertTrue(self.panel.switch.value)
        self.assertTrue(self.panel.switch.disabled)

    def test_reenabling_group_starts_selected_patch(self) -> None:
        self.group.enabled = False
        self.panel.set_group_enabled(False)
        self.voice.build.reset_mock()
        self.voice.start.reset_mock()
        event = SimpleNamespace(control=SimpleNamespace(value=True), page=MagicMock())

        self.group._handle_enabled(event)

        self.voice.build.assert_called_once_with(self.context)
        self.voice.start.assert_called_once_with(self.context.tempo)
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
            any(
                isinstance(control, ft.ExpansionTile)
                for control in patch_content.controls
            )
        )

    def test_slider_help_text_is_above_track_and_larger(self) -> None:
        param = _StubPatch.test_value

        row = self.panel._slider_row(param)
        controls = row.content.controls

        self.assertEqual(controls[1].value, param.spec.help_text)
        self.assertEqual(controls[1].size, 12)
        self.assertIs(controls[2], self.panel._sliders[param])

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
            app.master_output_slider,
        ):
            self.assertTrue(self._contains_control(right_column, control))

    def _slowed_reverb_app(self, catalog_dir: str) -> PatchRackApp:
        return PatchRackApp(
            MagicMock(),
            "Slowed Reverb",
            "Test rack",
            SlowedReverbRack(),
            catalog_dir=Path(catalog_dir),
        )

    def test_outer_control_moves_inner_sliders_and_patches(self) -> None:
        with TemporaryDirectory() as catalog_dir:
            app = self._slowed_reverb_app(catalog_dir)
        rack = app.rack
        by_path = {slider.path: slider for slider in app.control_sliders}

        by_path["Arrival/lift"].set_value(1.0)

        for path in ("Arrival/Lead/lift", "Arrival/Pad/lift", "Arrival/Hook/lift"):
            self.assertEqual(by_path[path].slider.value, 1.0)
        self.assertEqual(rack.pad_wash.volume, 0.65)
        self.assertEqual(rack.lead_keys.volume, 1.7)

        by_path["Arrival/Pad/lift"].set_value(0.0)

        self.assertEqual(rack.pad_wash.volume, 0.5)
        self.assertEqual(rack.hook_pluck.volume, 0.55)
        self.assertEqual(by_path["Arrival/lift"].slider.value, 1.0)

    def test_control_values_round_trip_through_a_preset(self) -> None:
        with TemporaryDirectory() as catalog_dir:
            app = self._slowed_reverb_app(catalog_dir)
            by_path = {slider.path: slider for slider in app.control_sliders}
            by_path["Arrival/Hook/lift"].set_value(0.4)
            app.preset_name_field.value = "round_trip"
            app._save_preset(MagicMock())

            fresh = self._slowed_reverb_app(catalog_dir)
            fresh.preset_dropdown.value = "round_trip"
            fresh._load_preset(MagicMock())

        self.assertEqual(fresh.rack.hook_pluck.volume, 0.4 + 0.4 * 0.15)
        self.assertEqual(
            next(
                s for s in fresh.control_sliders if s.path == "Arrival/Hook/lift"
            ).slider.value,
            0.4,
        )

    def test_disabling_outer_group_gates_nested_patches(self) -> None:
        with TemporaryDirectory() as catalog_dir:
            app = self._slowed_reverb_app(catalog_dir)
        arrival = app.groups[0]
        pad = next(g for g in arrival.walk() if g.group_def.title == "Pad")
        panel = pad.panels[0]
        panel.engine_started(MagicMock())
        arrival.set_engine_ready(True)

        arrival._handle_enabled(
            SimpleNamespace(control=SimpleNamespace(value=False), page=MagicMock())
        )

        self.assertTrue(pad.switch.disabled)
        self.assertTrue(panel.switch.disabled)

        arrival._handle_enabled(
            SimpleNamespace(control=SimpleNamespace(value=True), page=MagicMock())
        )

        self.assertFalse(pad.switch.disabled)
        self.assertFalse(panel.switch.disabled)

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
        app.running = True
        enabled_names = list(app.panels)[:2]
        for name in enabled_names:
            app.panels[name].enabled = True
            app.panels[name].switch.value = True
        for panel in app.panels.values():
            panel._apply = MagicMock()

        app.toggle_pause()

        self.assertEqual(app._paused_panels, set(enabled_names))
        self.assertTrue(all(not panel.enabled for panel in app.panels.values()))
        self.assertEqual(app.pause_button.text, "Start")

        app.panels[list(app.panels)[-1]].enabled = True
        app.toggle_pause()

        self.assertEqual(
            {name for name, panel in app.panels.items() if panel.enabled},
            set(enabled_names),
        )
        self.assertEqual(app.pause_button.text, "Pause")

    def test_psyambient_declares_conceptual_groups(self) -> None:
        (atmosphere,) = PsyambientRack().groups
        groups = atmosphere.children
        self.assertEqual(
            [group.title for group in groups],
            ["Soundscapes", "Mid Voices", "Bass"],
        )
        self.assertEqual([len(group.patches) for group in groups], [3, 3, 3])

    def test_slowed_reverb_wash_follows_lead_group(self) -> None:
        rack = SlowedReverbRack()
        self.assertEqual(
            [group.title for group in rack.groups],
            ["Arrival", "Bass", "Texture", "Kick", "Hi-hat"],
        )
        self.assertEqual(
            [group.title for group in rack.groups[0].children],
            ["Lead", "Pad", "Hook"],
        )

        lead = rack.groups[0].children[0]
        self.assertEqual(
            [type(patch).__name__ for patch in lead.patches], ["Strings", "Keys"]
        )

        (sidechain,) = rack.pad_wash.sidechains
        self.assertIs(sidechain.group, rack.kick_group)
        self.assertEqual(SlowedReverbRack.harmony.progression, (2, 7, 0, 9))

    def test_lift_updates_the_visible_output_level(self) -> None:
        rack = SlowedReverbRack()
        with TemporaryDirectory() as catalog_dir:
            app = PatchRackApp(
                MagicMock(),
                "Slowed Reverb",
                "Test rack",
                rack,
                catalog_dir=Path(catalog_dir),
            )

        lift = next(
            slider
            for slider in app.control_sliders
            if slider.control is SlowedReverbRack.arrival_lift
        )
        lift.set_value(0.73)

        panel = app.panels[rack.pad_wash.name]
        expected = 0.5 + 0.73 * 0.15
        self.assertAlmostEqual(rack.pad_wash.volume, expected)
        self.assertAlmostEqual(panel._sliders[SoundscapeWash.volume].value, expected)
        self.assertEqual(panel._value_texts[SoundscapeWash.volume].value, "0.6")

    def test_deep_house_drums_group_holds_snare_tom_and_cymbals(self) -> None:
        rhythm = next(
            group for group in DeepHouseRack().groups if group.title == "Rhythm"
        )
        drums = next(group for group in rhythm.children if group.title == "Drums")

        self.assertEqual(
            [patch.name for patch in drums.patches],
            ["snare", "tom", "cymbal_ride", "cymbal_crash"],
        )


if __name__ == "__main__":
    unittest.main()
