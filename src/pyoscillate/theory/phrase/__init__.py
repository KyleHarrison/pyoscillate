"""Phrases, the step patterns patches play, grouped by the role they fill."""

from __future__ import annotations

from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, Step
from pyoscillate.theory.phrase.bass import BassLines
from pyoscillate.theory.phrase.fill import Fills
from pyoscillate.theory.phrase.hook import Hooks
from pyoscillate.theory.phrase.lead import Leads
from pyoscillate.theory.phrase.rhythm import Rhythms

__all__ = [
    "BassLines",
    "Fills",
    "Hooks",
    "Leads",
    "Melodies",
    "Phrase",
    "PhraseMode",
    "Phrases",
    "Rhythms",
    "Step",
]


class Phrases(Catalog):
    """Every phrase a clocked patch can play, one list over all roles.
    `ArpOrders` and `Walks` are not in it: they need a note pool or a pace of
    their own, so their patches name them directly."""

    sources = (Rhythms, BassLines, Leads, Fills, Hooks)


class Melodies(Catalog):
    """The pitched lines a melodic voice (a bass, a lead, a tom, a bell) can
    play, whose offsets are semitones above the chord root."""

    sources = (Leads, BassLines, Fills)
