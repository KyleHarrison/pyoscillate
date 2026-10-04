"""The master rack's control tree stays small and cheap to diff.

Flet diffs the whole control tree on its single event-loop thread after every
`page.update()`, so the control count and the whole-tree diff time are what
decide how laggy the UI feels (see docs/todos/ui-perf-00-audit-context.md).
This builds the real master rack headless, serialises it the way Flet's
transport does (which also takes the snapshots a diff compares against) and
checks both after UI changes. The limits are generous: they catch a return to
mounting every panel up front (about 18,000 controls, 87 ms), not noise.
"""

import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import msgpack
from flet.controls.base_control import BaseControl
from flet.controls.object_patch import ObjectPatch
from flet.messaging.protocol import configure_encode_object_for_msgpack

import flet as ft
from pyoscillate.projects.master_rack.rack import MasterRack
from src.flet.base import PatchRackApp


class MasterRackUpdateScopeTests(unittest.TestCase):
    MAX_CONTROLS = 2000
    MAX_DIFF_SECONDS = 0.05

    @classmethod
    def setUpClass(cls) -> None:
        page = MagicMock()
        with TemporaryDirectory() as catalog_dir:
            PatchRackApp(
                page,
                "Master Rack",
                "test",
                MasterRack(),
                catalog_dir=Path(catalog_dir),
            )
        cls.root: ft.Control = page.add.call_args.args[0]
        encode = configure_encode_object_for_msgpack(BaseControl)
        cls.packed = msgpack.packb(cls.root, default=encode, use_bin_type=True)

    @classmethod
    def count_controls(cls, node: object) -> int:
        if isinstance(node, dict):
            own = 1 if "_c" in node else 0
            return own + sum(cls.count_controls(v) for v in node.values())
        if isinstance(node, list):
            return sum(cls.count_controls(v) for v in node)
        return 0

    def test_the_first_paint_holds_few_controls(self) -> None:
        tree = msgpack.unpackb(self.packed, raw=False, strict_map_key=False)
        count = self.count_controls(tree)
        self.assertGreater(count, 0)
        self.assertLess(count, self.MAX_CONTROLS)

    def test_an_unchanged_tree_diffs_quickly_and_to_nothing(self) -> None:
        started = time.perf_counter()
        _, added, removed =ObjectPatch.from_diff(
            self.root, self.root, control_cls=BaseControl, parent=None, path=[]
        )
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, self.MAX_DIFF_SECONDS)
        self.assertEqual((added, removed), ([], []))


if __name__ == "__main__":
    unittest.main()
