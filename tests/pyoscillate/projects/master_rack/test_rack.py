import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from pyoscillate.projects.master_rack.rack import (
    MasterRack,
    discover_directories,
    discover_patches,
)
from src.flet.base import PatchRackApp


def _group(rack: MasterRack, title: str):
    """The group called `title` anywhere in the rack."""
    return next(
        group for top in rack.groups for group in top.walk() if group.title == title
    )


class MasterRackTests(unittest.TestCase):
    def test_top_level_groups_are_the_patch_directories(self) -> None:
        rack = MasterRack()

        titles = [group.title for group in rack.groups]
        self.assertEqual(titles, sorted(titles))
        self.assertIn("Drums", titles)
        self.assertIn("Tonal", titles)

    def test_groups_nest_the_way_the_directories_do(self) -> None:
        rack = MasterRack()

        tonal = _group(rack, "Tonal")
        self.assertEqual(
            [child.title for child in tonal.children],
            ["Bass", "Drone", "Keys", "Lead", "Pluck", "Strings"],
        )
        bass = _group(rack, "Bass")
        self.assertEqual([child.title for child in bass.children], ["FM", "Funk"])
        self.assertIn(bass, tonal.children)

    def test_a_group_offers_only_the_patches_directly_in_its_directory(self) -> None:
        rack = MasterRack()

        tonal = _group(rack, "Tonal")
        bass = _group(rack, "Bass")
        fm = _group(rack, "FM")
        self.assertEqual(tonal.own_patches, ())
        self.assertTrue(set(fm.own_patches).isdisjoint(bass.own_patches))
        self.assertTrue(set(fm.patches) <= set(bass.patches))
        self.assertTrue(set(bass.patches) <= set(tonal.patches))

    def test_a_group_is_selectable_when_it_has_patches_of_its_own(self) -> None:
        rack = MasterRack()

        for top in rack.groups:
            for group in top.walk():
                with self.subTest(group=group.title):
                    self.assertEqual(group.selectable, bool(group.own_patches))

    def test_the_top_group_holds_every_patch_below_it(self) -> None:
        rack = MasterRack()

        for category, classes in discover_patches().items():
            group = next(
                g for g in rack.groups if g.title == category.replace("_", " ").title()
            )
            with self.subTest(category=category):
                self.assertEqual({type(p) for p in group.patches}, set(classes))

    def test_the_hat_group_offers_every_hat_patch(self) -> None:
        rack = MasterRack()

        hats = _group(rack, "Hat")
        offered = {type(patch) for patch in hats.own_patches}
        self.assertEqual(offered, set(discover_directories()[("drums", "hat")]))
        self.assertGreater(len(offered), 3)

    def test_every_patch_is_offered_once(self) -> None:
        rack = MasterRack()

        offered = [
            patch
            for top in rack.groups
            for group in top.walk()
            for patch in group.own_patches
        ]
        self.assertEqual(len(offered), len(set(offered)))
        self.assertEqual(
            len(offered), sum(len(c) for c in discover_directories().values())
        )

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
        self.drums = next(
            g
            for top in self.app.groups
            for g in top.walk()
            if g.group_def.title == "Hat"
        )

    def test_nothing_is_added_at_first(self) -> None:
        self.assertEqual(self.drums.added, set())
        self.assertFalse(any(box.visible for box in self.drums._boxes.values()))

    def test_adding_shows_the_panel_without_switching_it_on(self) -> None:
        panel = self.drums.panels[0]

        self.drums.set_added({panel})

        self.assertTrue(self.drums._boxes[panel].visible)
        self.assertFalse(panel.enabled)

    def test_adds_fill_the_full_width(self) -> None:
        box = self.drums._boxes[self.drums.panels[0]]

        self.assertEqual(box.col, 12)

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

    def test_nothing_is_built_until_a_patch_is_added(self) -> None:
        panel = self.drums.panels[0]

        self.assertFalse(any(p.built for p in self.app.panels.values()))
        self.assertIsNone(self.drums._boxes[panel].content)
        self.assertFalse(panel.mounted)

    def test_adding_mounts_the_panel_and_removing_takes_it_out(self) -> None:
        panel = self.drums.panels[0]

        self.drums.set_added({panel})
        self.assertIs(self.drums._boxes[panel].content, panel.region)
        self.assertTrue(panel.mounted)

        self.drums.set_added(set())
        self.assertIsNone(self.drums._boxes[panel].content)
        self.assertFalse(panel.mounted)

    def test_a_panel_is_built_the_first_time_it_opens(self) -> None:
        panel = self.drums.panels[0]
        self.drums.set_added({panel})
        self.assertFalse(panel.built)
        self.assertEqual(panel.body.controls, [])

        panel.set_expanded(True)

        self.assertTrue(panel.built)
        self.assertTrue(panel.body.controls)

    def test_the_page_starts_with_few_controls(self) -> None:
        def count(control: object) -> int:
            children = list(getattr(control, "controls", None) or [])
            for name in ("content", "leading", "title", "subtitle"):
                child = getattr(control, name, None)
                if child is not None and not isinstance(child, str):
                    children.append(child)
            return 1 + sum(count(child) for child in children)

        total = sum(count(group.control) for group in self.app.groups)

        # a group costs its tile and menu, and a patch one menu row: the sliders
        # of a patch (dozens each) are not made until its tile opens
        self.assertLess(total, 1000)

    def test_a_panel_never_shown_still_takes_a_preset(self) -> None:
        panel = self.drums.panels[0]
        saved = panel.to_preset()
        param = next(p for p in panel.patch.params if not p.spec.options)
        saved[param.name] = param.spec.maximum

        panel.apply_preset(saved)

        self.assertEqual(param.read(panel.patch), param.spec.maximum)
        self.assertFalse(panel.built)
        self.assertEqual(panel.sync_sliders(), [])

    def test_values_set_while_unbuilt_show_when_the_body_is_made(self) -> None:
        panel = self.drums.panels[0]
        param = next(p for p in panel.patch.params if not p.spec.options)
        param.write(panel.patch, param.spec.maximum)

        panel.set_expanded(True)

        self.assertEqual(
            panel._sliders[param].value, param.spec.to_position(param.spec.maximum)
        )

    def test_a_removed_panel_is_not_repainted_by_a_group_push(self) -> None:
        panel = self.drums.panels[0]
        self.drums.set_added({panel})
        panel.set_expanded(True)
        self.drums.set_added(set())

        self.assertEqual(panel.sync_sliders(), [])
        self.assertFalse(panel.refresh_analysis())

    def test_the_added_set_survives_a_preset_round_trip(self) -> None:
        panel = self.drums.panels[1]
        self.drums.set_added({panel})
        self.app.preset_name_field.value = "round"
        self.app._save_preset(MagicMock())
        self.drums.set_added(set())

        self.app.preset_dropdown.value = "round"
        self.app._load_preset(MagicMock())

        self.assertEqual(self.drums.added, {panel})
        self.assertIs(self.drums._boxes[panel].content, panel.region)


if __name__ == "__main__":
    unittest.main()
