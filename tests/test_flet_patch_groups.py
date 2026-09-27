import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from pyoscillate.patches.base import Patch
from pyoscillate.projects.deep_house.rack import DeepHouseRack
from pyoscillate.projects.psyambient.rack import PsyambientRack
from src.flet.base import PatchGroup, PatchGroupDef, PatchPanel

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
    def setUp(self) -> None:
        self.voice = _StubPatch(name="test_patch", title="Test Patch", summary="Test voice.")
        self.build = MagicMock(wraps=self.voice.build)
        self.voice.build = self.build
        self.rack = MagicMock()
        self.rack.get.return_value = None
        self.panel = PatchPanel(self.rack, self.voice)
        self.group = PatchGroup(
            PatchGroupDef("test", "Test Group", (self.voice,)), [self.panel]
        )
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
