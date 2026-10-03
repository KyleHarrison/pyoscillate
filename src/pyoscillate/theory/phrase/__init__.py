"""Phrases, the step patterns patches play, grouped by the role they fill."""

from __future__ import annotations

from typing import ClassVar

from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, PhraseRole, Step
from pyoscillate.theory.phrase.bass import BassLines
from pyoscillate.theory.phrase.fill import Fills
from pyoscillate.theory.phrase.hook import Hooks
from pyoscillate.theory.phrase.lead import Leads
from pyoscillate.theory.phrase.progression import Progressions
from pyoscillate.theory.phrase.rhythm import Rhythms

__all__ = [
    "BassLines",
    "Fills",
    "Hooks",
    "Leads",
    "Phrase",
    "PhraseMode",
    "PhraseRole",
    "Phrases",
    "Progressions",
    "Rhythms",
    "Step",
]


class Phrases(Catalog):
    """Every phrase a clocked patch can play, one list over all roles.
    `ArpOrders` and `Walks` are not in it: they need a note pool or a pace of
    their own, so their patches name them directly. A patch offers the part of
    it that suits it with `for_roles`."""

    sources = (Rhythms, BassLines, Leads, Fills, Hooks, Progressions)

    _by_roles: ClassVar[dict[frozenset[PhraseRole], type[Catalog]]] = {}

    @classmethod
    def for_roles(cls, *roles: PhraseRole) -> type[Catalog]:
        """The catalog of phrases that suit any of `roles`, in `Phrases`
        order. The same roles give the same catalog."""
        key = frozenset(roles)
        if key not in cls._by_roles:
            cls._by_roles[key] = cls.subset(
                phrase
                for phrase in cls.members()
                if isinstance(phrase, Phrase) and key.intersection(phrase.roles)
            )
        return cls._by_roles[key]
