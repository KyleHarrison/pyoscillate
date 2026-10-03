"""The shared pattern catalogs in `theory/intervals.py` and the dropdowns that
select from them. No audio server is needed."""

import importlib
import pkgutil
import unittest

from pyoscillate import patches
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import Figured, Melodic, Rhythmic
from pyoscillate.theory.intervals import ChordTones, Melody, Pattern, Rhythm


class CatalogTests(unittest.TestCase):
    def test_every_step_sits_inside_its_cycle(self) -> None:
        for catalog in (Rhythm, Melody, ChordTones):
            for member in catalog:
                with self.subTest(pattern=member.name):
                    self.assertTrue(member.value[2])
                    for entry in member.value[2]:
                        self.assertTrue(0 <= entry[0] < member.cycle)

    def test_every_pattern_has_its_own_label(self) -> None:
        for catalog in (Rhythm, Melody, ChordTones):
            with self.subTest(catalog=catalog.__name__):
                labels = catalog.labels()
                self.assertEqual(len(labels), len(catalog.__members__))
                self.assertEqual(len(set(labels)), len(labels))

    def test_a_rhythm_velocity_is_a_level(self) -> None:
        for rhythm in Rhythm:
            with self.subTest(rhythm=rhythm.name):
                self.assertTrue(all(0 < v <= 1 for v in rhythm.hits.values()))

    def test_open_hat_steps_are_hits(self) -> None:
        for rhythm in Rhythm:
            with self.subTest(rhythm=rhythm.name):
                self.assertLessEqual(rhythm.open_steps, set(rhythm.hits))

    def test_a_melody_accent_is_a_level(self) -> None:
        for melody in Melody:
            with self.subTest(melody=melody.name):
                self.assertEqual(set(melody.accents), set(melody.steps))
                self.assertTrue(all(0 < a <= 1 for a in melody.accents.values()))

    def test_index_round_trips_through_by_index(self) -> None:
        for catalog in (Rhythm, Melody, ChordTones):
            for member in catalog:
                self.assertIs(catalog.by_index(member.index), member)


class DropdownTests(unittest.TestCase):
    """Every patch that plays a pattern takes it from a catalog dropdown, and
    none declares a pattern of its own."""

    @staticmethod
    def patch_classes() -> list[type[Patch]]:
        classes: dict[str, type[Patch]] = {}
        for module in pkgutil.walk_packages(patches.__path__, "pyoscillate.patches."):
            for obj in vars(importlib.import_module(module.name)).values():
                if isinstance(obj, type) and issubclass(obj, Patch):
                    classes[f"{obj.__module__}.{obj.__qualname__}"] = obj
        return list(classes.values())

    def test_a_pattern_param_lists_its_whole_catalog(self) -> None:
        for cls in self.patch_classes():
            for param, catalog in (
                ("rhythm", Rhythm),
                ("melody", Melody),
                ("figure", ChordTones),
            ):
                if param in cls.__dict__ or any(p.name == param for p in cls.params):
                    spec = next(p for p in cls.params if p.name == param).spec
                    with self.subTest(patch=cls.__name__, param=param):
                        self.assertEqual(spec.options, catalog.labels())
                        self.assertTrue(
                            0 <= spec.default < len(catalog.labels()),
                        )

    def test_no_patch_declares_a_pattern_of_its_own(self) -> None:
        for cls in self.patch_classes():
            with self.subTest(patch=cls.__name__):
                for name in ("pattern", "pattern_cycle", "phrase", "phrases"):
                    self.assertNotIn(name, vars(cls))

    def test_the_mixins_name_a_catalog(self) -> None:
        self.assertEqual(Rhythmic.rhythm.spec.options, Rhythm.labels())
        self.assertEqual(Melodic.melody.spec.options, Melody.labels())
        self.assertEqual(Figured.figure.spec.options, ChordTones.labels())
        self.assertTrue(issubclass(Rhythm, Pattern))


if __name__ == "__main__":
    unittest.main()
