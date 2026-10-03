"""The shared phrase catalogs in `theory/phrase/` and the dropdowns that
select from them. No audio server is needed."""

import importlib
import pkgutil
import unittest

from pyoscillate import patches
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import Phrased
from pyoscillate.patches.drums.kick.kick import Kick
from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.chord import Chords, ChordUnit
from pyoscillate.theory.phrase import (
    BassLines,
    Fills,
    Hooks,
    Leads,
    Melodies,
    Phrase,
    PhraseMode,
    Phrases,
    Rhythms,
)
from pyoscillate.theory.phrase.arp import ArpOrders
from pyoscillate.theory.phrase.walk import Walks
from pyoscillate.theory.progression import Progressions
from pyoscillate.theory.scale import Scales


class CatalogTests(unittest.TestCase):
    CATALOGS = (
        Rhythms,
        BassLines,
        Leads,
        Fills,
        Hooks,
        Phrases,
        Melodies,
        ArpOrders,
        Walks,
        Chords,
        Scales,
        Progressions,
    )
    PHRASE_CATALOGS = (Rhythms, BassLines, Leads, Fills, Hooks, ArpOrders, Walks)

    def test_every_step_sits_inside_its_cycle(self) -> None:
        for catalog in self.PHRASE_CATALOGS:
            for phrase in catalog.members():
                with self.subTest(phrase=phrase.id):
                    self.assertTrue(phrase.steps)
                    for step in phrase.steps:
                        self.assertTrue(0 <= step.at < phrase.cycle)

    def test_every_member_has_its_own_id_and_label(self) -> None:
        for catalog in self.CATALOGS:
            with self.subTest(catalog=catalog.__name__):
                self.assertEqual(len(set(catalog.ids())), len(catalog.members()))
                self.assertEqual(len(set(catalog.labels())), len(catalog.members()))

    def test_ids_are_the_lowercase_attribute_names(self) -> None:
        self.assertEqual(Rhythms.QUARTER_PULSE.id, "quarter_pulse")
        self.assertIs(Rhythms.by_id("quarter_pulse"), Rhythms.QUARTER_PULSE)
        with self.assertRaises(KeyError):
            Rhythms.by_id("no_such_phrase")

    def test_every_member_has_a_category_and_the_groups_cover_them(self) -> None:
        for catalog in self.CATALOGS:
            with self.subTest(catalog=catalog.__name__):
                members = catalog.members()
                self.assertTrue(all(member.category for member in members))
                grouped = catalog.grouped()
                self.assertEqual(
                    sum(len(items) for items in grouped.values()), len(members)
                )

    def test_a_rhythm_accent_is_a_level(self) -> None:
        for rhythm in Rhythms.members():
            with self.subTest(rhythm=rhythm.id):
                self.assertIs(rhythm.mode, PhraseMode.NONE)
                self.assertEqual(rhythm.values, rhythm.accents)
                self.assertTrue(all(0 < a <= 1 for a in rhythm.accents.values()))

    def test_open_hat_steps_are_hits(self) -> None:
        for rhythm in Rhythms.members():
            with self.subTest(rhythm=rhythm.id):
                self.assertLessEqual(rhythm.open_steps, set(rhythm.accents))

    def test_a_pitched_phrase_values_are_offsets_with_levels_alongside(self) -> None:
        for phrase in (*BassLines.members(), *Leads.members(), *Fills.members()):
            with self.subTest(phrase=phrase.id):
                self.assertIs(phrase.mode, PhraseMode.SEMITONES)
                self.assertEqual(set(phrase.values), set(phrase.accents))
                self.assertEqual(set(phrase.lengths), set(phrase.values))
                self.assertTrue(all(0 < a <= 1 for a in phrase.accents.values()))

    def test_a_hook_indexes_the_chord_triad(self) -> None:
        for hook in Hooks.members():
            with self.subTest(hook=hook.id):
                self.assertIs(hook.mode, PhraseMode.CHORD_TONE)
                self.assertTrue(all(0 <= tone <= 2 for tone in hook.values.values()))

    def test_a_pool_phrase_resolves_through_a_pool_and_wraps(self) -> None:
        order = ArpOrders.UP_DOWN_FOURS
        self.assertIs(order.mode, PhraseMode.POOL_INDEX)
        resolved = order.resolve((0, 4, 7))
        self.assertEqual(set(resolved), set(range(order.cycle)))
        self.assertTrue(set(resolved.values()) <= {0, 4, 7})

    def test_a_walk_is_its_offsets_in_step_order(self) -> None:
        self.assertEqual(Walks.MINOR_7_ARCH.offsets, (0, 3, 7, 10, 12, 10, 7, 3))

    def test_a_chord_in_semitones_ignores_the_scale(self) -> None:
        self.assertIs(Chords.OPEN_FIFTH.unit, ChordUnit.SEMITONES)
        self.assertEqual(Scales.MINOR.voice(Chords.OPEN_FIFTH), (0, 7, 12))
        self.assertEqual(Scales.MAJOR.voice(Chords.TRIAD), (0, 4, 7))
        self.assertEqual(Scales.MINOR.voice(Chords.TRIAD), (0, 3, 7))

    def test_index_round_trips_through_by_index(self) -> None:
        for catalog in self.CATALOGS:
            for member in catalog.members():
                self.assertIs(catalog.by_index(catalog.index_of(member)), member)

    def test_by_index_clamps(self) -> None:
        self.assertIs(Rhythms.by_index(-1), Rhythms.members()[0])
        self.assertIs(Rhythms.by_index(10_000), Rhythms.members()[-1])

    def test_a_gathering_catalog_lists_its_sources_in_order(self) -> None:
        self.assertEqual(
            Phrases.members(),
            (
                *Rhythms.members(),
                *BassLines.members(),
                *Leads.members(),
                *Fills.members(),
                *Hooks.members(),
            ),
        )

    def test_two_catalogs_cannot_gather_clashing_ids(self) -> None:
        with self.assertRaises(ValueError):

            class Clash(Catalog):
                sources = (Rhythms, Rhythms)

        self.assertTrue(all(isinstance(p, Phrase) for p in Phrases.members()))


class DropdownTests(unittest.TestCase):
    """Every patch that plays a phrase takes it from a catalog dropdown, and
    none declares a pattern of its own."""

    @staticmethod
    def patch_classes() -> list[type[Patch]]:
        classes: dict[str, type[Patch]] = {}
        for module in pkgutil.walk_packages(patches.__path__, "pyoscillate.patches."):
            for obj in vars(importlib.import_module(module.name)).values():
                if isinstance(obj, type) and issubclass(obj, Patch):
                    classes[f"{obj.__module__}.{obj.__qualname__}"] = obj
        return list(classes.values())

    def test_a_phrase_param_lists_its_whole_catalog(self) -> None:
        for cls in self.patch_classes():
            for param in cls.params:
                if param.catalog is None:
                    continue
                with self.subTest(patch=cls.__name__, param=param.name):
                    spec = param.spec
                    self.assertEqual(spec.options, param.catalog.labels())
                    self.assertEqual(spec.option_ids, param.catalog.ids())
                    self.assertTrue(0 <= spec.default < len(spec.options))
                    self.assertEqual(spec.maximum, len(spec.options) - 1)

    def test_every_phrased_patch_starts_on_a_phrase_of_its_catalog(self) -> None:
        for cls in self.patch_classes():
            if issubclass(cls, Phrased):
                with self.subTest(patch=cls.__name__):
                    catalog = cls.phrase.catalog
                    self.assertIsNotNone(catalog)
                    self.assertIsInstance(
                        catalog.by_index(int(cls.phrase.default)), Phrase
                    )

    def test_no_patch_declares_a_pattern_of_its_own(self) -> None:
        for cls in self.patch_classes():
            with self.subTest(patch=cls.__name__):
                for name in ("pattern", "pattern_cycle", "phrases"):
                    self.assertNotIn(name, vars(cls))

    def test_a_member_can_be_assigned_to_a_choice_param(self) -> None:
        kick = Kick()
        kick.phrase = Rhythms.BACKBEAT
        self.assertEqual(kick.phrase, Rhythms.index_of(Rhythms.BACKBEAT))
        self.assertIs(kick.selected_phrase, Rhythms.BACKBEAT)

    def test_a_param_replaced_with_a_member_default_resolves_it(self) -> None:

        class Voice:
            phrase = Phrased.phrase.replace(catalog=Rhythms, default=Rhythms.BACKBEAT)

        self.assertEqual(Voice.phrase.default, Rhythms.index_of(Rhythms.BACKBEAT))
        self.assertEqual(Voice.phrase.spec.option_ids, Rhythms.ids())


if __name__ == "__main__":
    unittest.main()
