import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from pyoscillate.projects.psyambient.rack import PATCH_GROUPS
from src.flet.base import PatchDef, PatchGroup, PatchGroupDef, PatchPanel


class PatchGroupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patch = MagicMock()
        self.build = MagicMock(return_value=self.patch)
        self.rack = MagicMock()
        self.rack.get.return_value = None
        patch_def = PatchDef("test_patch", "Test Patch", "Test voice.", self.build, ())
        self.panel = PatchPanel(self.rack, patch_def)
        self.group = PatchGroup(PatchGroupDef("test", "Test Group", (patch_def,)), [self.panel])
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
        self.rack.start.assert_called_once_with("test_patch", self.patch)
        self.patch.set.assert_called_once_with("volume", self.panel.volume)
        self.assertFalse(self.panel.switch.disabled)

    def test_psyambient_declares_conceptual_groups(self) -> None:
        self.assertEqual(
            [group.name for group in PATCH_GROUPS],
            ["soundscapes", "mid", "bass"],
        )
        self.assertEqual([len(group.patch_defs) for group in PATCH_GROUPS], [3, 3, 3])


if __name__ == "__main__":
    unittest.main()
