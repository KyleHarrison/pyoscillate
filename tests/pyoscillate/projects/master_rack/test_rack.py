import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from pyoscillate.projects.master_rack.rack import MasterRack, discover_patches
from src.flet.base import PatchRackApp


class MasterRackTests(unittest.TestCase):
    def test_one_selectable_group_per_patch_category(self) -> None:
        rack = MasterRack()

        titles = [group.title for group in rack.groups]
        self.assertEqual(titles, sorted(titles))
        self.assertIn("Drums", titles)
        self.assertIn("Tonal", titles)
        self.assertTrue(all(group.selectable for group in rack.groups))

    def test_the_drums_group_offers_every_drum_patch(self) -> None:
        rack = MasterRack()

        drums = next(group for group in rack.groups if group.title == "Drums")
        offered = {type(patch) for patch in drums.own_patches}
        self.assertEqual(offered, set(discover_patches()["drums"]))
        self.assertGreater(len(offered), 5)

    def test_shared_style_bases_are_not_offered(self) -> None:
        offered = {cls.__name__ for cls in discover_patches()["drums"]}

        self.assertIn("KickRound", offered)
        self.assertNotIn("Kick", offered)


class MasterRackAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        page = MagicMock()
        self.app = PatchRackApp(page, "t", "t", MasterRack(), Path(self.directory.name))
        self.drums = next(g for g in self.app.groups if g.group_def.title == "Drums")

    def test_nothing_is_added_at_first(self) -> None:
        self.assertEqual(self.drums.added, set())
        self.assertFalse(any(box.visible for box in self.drums._boxes.values()))

    def test_adding_shows_the_panel_without_switching_it_on(self) -> None:
        panel = self.drums.panels[0]

        self.drums.set_added({panel})

        self.assertTrue(self.drums._boxes[panel].visible)
        self.assertFalse(panel.enabled)

    def test_adds_lay_out_two_to_a_row(self) -> None:
        box = self.drums._boxes[self.drums.panels[0]]

        self.assertEqual(box.col, {"xs": 12, "md": 6})

    def test_removing_hides_and_switches_the_panel_off(self) -> None:
        panel = self.drums.panels[0]
        self.drums.set_added({panel})
        panel.apply_enabled(True)

        self.drums.set_added(set())

        self.assertFalse(self.drums._boxes[panel].visible)
        self.assertFalse(panel.enabled)

    def test_a_loaded_enabled_panel_is_revealed(self) -> None:
        panel = self.drums.panels[1]
        panel.enabled = True

        self.drums.reveal_enabled()

        self.assertIn(panel, self.drums.added)


if __name__ == "__main__":
    unittest.main()
