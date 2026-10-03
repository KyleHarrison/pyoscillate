"""Chord progressions as one root per bar."""

from __future__ import annotations

from dataclasses import dataclass

from pyoscillate.theory.catalog import Catalog, CatalogItem


@dataclass(frozen=True, eq=False, kw_only=True)
class Progression(CatalogItem):
    """Chord changes as roots, one per bar, in semitones above the key of a
    major scale. Give one to `Harmony.progression` and every pitched patch that
    reads the rack's harmony follows the same changes; the chord quality
    (minor, major, dominant) comes from the scale degree each root sits on,
    not from this table. `numerals` is the roman-numeral spelling (lowercase
    for a minor chord), shown in the label."""

    roots: tuple[int, ...]
    numerals: str


class Progressions(Catalog):
    """The named progressions, each known by what it is called."""

    FOUR_CHORD = Progression(
        roots=(0, 7, 9, 5),
        numerals="I-V-vi-IV",
        label="Four chords (I-V-vi-IV)",
        category="Pop",
    )
    DOO_WOP = Progression(
        roots=(0, 9, 5, 7),
        numerals="I-vi-IV-V",
        label="Doo-wop (I-vi-IV-V)",
        category="Pop",
    )
    MINOR_POP = Progression(
        roots=(9, 5, 0, 7),
        numerals="vi-IV-I-V",
        label="Minor pop (vi-IV-I-V)",
        category="Pop",
    )
    JAZZ_TURNAROUND = Progression(
        roots=(2, 7, 0, 9),
        numerals="ii-V-I-vi",
        label="Jazz turnaround (ii-V-I-vi)",
        category="Jazz",
    )
    JAZZ_II_V_I_IV = Progression(
        roots=(2, 7, 0, 5),
        numerals="ii-V-I-IV",
        label="Jazz ii-V-I-IV",
        category="Jazz",
    )
    CIRCLE_OF_FIFTHS = Progression(
        roots=(0, 4, 9, 2),
        numerals="I-iii-vi-ii",
        label="Circle of fifths (I-iii-vi-ii)",
        category="Circle",
    )
    CIRCLE_RUN = Progression(
        roots=(4, 9, 2, 7),
        numerals="iii-vi-ii-V",
        label="Circle run (iii-vi-ii-V)",
        category="Circle",
    )
