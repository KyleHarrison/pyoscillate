"""Chord progressions: which chord root is sounding in each bar."""

from __future__ import annotations

from dataclasses import dataclass

from pyoscillate.theory.catalog import Catalog, CatalogItem


@dataclass(frozen=True, eq=False, kw_only=True)
class ChordChanges(CatalogItem):
    """Chord changes as roots in semitones above the key, each held for
    `bars_per_chord` bars before the next, repeating. A pitched patch holds
    one (see `Progressive`) and reads the root sounding in each bar; the chord
    quality (minor, major, dominant) comes from the scale degree each root sits
    on, not from this table. It is not a `Phrase`: nothing plays it, it only
    says which chord a phrase's relative offsets are measured from."""

    roots: tuple[int, ...]
    bars_per_chord: int = 1

    @property
    def cycle(self) -> int:
        """Bars before the changes repeat."""
        return len(self.roots) * self.bars_per_chord

    def chord_root(self, bar: int) -> int:
        """The root sounding in `bar`, in semitones above the key."""
        return self.roots[bar % self.cycle // self.bars_per_chord]


class Progressions(Catalog):
    """The named chord progressions, each known by what it is called. A
    patch starts on `STATIC` (the tonic held) unless its rack names another."""

    STATIC = ChordChanges(roots=(0,), label="Static (I)", category="Static")
    FOUR_CHORD = ChordChanges(
        roots=(0, 7, 9, 5), label="Four chords (I-V-vi-IV)", category="Pop"
    )
    DOO_WOP = ChordChanges(
        roots=(0, 9, 5, 7), label="Doo-wop (I-vi-IV-V)", category="Pop"
    )
    MINOR_POP = ChordChanges(
        roots=(9, 5, 0, 7), label="Minor pop (vi-IV-I-V)", category="Pop"
    )
    JAZZ_TURNAROUND = ChordChanges(
        roots=(2, 7, 0, 9), label="Jazz turnaround (ii-V-I-vi)", category="Jazz"
    )
    JAZZ_II_V_I_IV = ChordChanges(
        roots=(2, 7, 0, 5), label="Jazz ii-V-I-IV", category="Jazz"
    )
    CIRCLE_OF_FIFTHS = ChordChanges(
        roots=(0, 4, 9, 2), label="Circle of fifths (I-iii-vi-ii)", category="Circle"
    )
    CIRCLE_RUN = ChordChanges(
        roots=(4, 9, 2, 7), label="Circle run (iii-vi-ii-V)", category="Circle"
    )
    DEEP_HOUSE_MINOR = ChordChanges(
        roots=(0, 5, 10, 7), label="Deep house minor (i-iv-bVII-v)", category="House"
    )
    PSY_VAMP = ChordChanges(
        roots=(0, 0, 0, 1),
        bars_per_chord=2,
        label="Psy vamp (i-i-i-bII, two bars each)",
        category="Modal",
    )
