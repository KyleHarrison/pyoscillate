"""Chord progressions as phrases: one chord root per bar, played by every
pitched patch that follows the rack's chords."""

from __future__ import annotations

from pyoscillate.clock import NoteDivision
from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, PhraseRole, Step


def chord_changes(
    roots: tuple[int, ...],
    *,
    label: str,
    category: str,
    bars_per_chord: int = 1,
) -> Phrase:
    """A progression: each of `roots` (semitones above the key) held for
    `bars_per_chord` bars, so the phrase's cycle is counted in bars. The chord
    quality (minor, major, dominant) comes from the scale degree each root sits
    on, not from this table."""
    return Phrase(
        division=NoteDivision.WHOLE,
        cycle=len(roots) * bars_per_chord,
        label=label,
        category=category,
        mode=PhraseMode.CHORD_ROOT,
        roles=(PhraseRole.PROGRESSION,),
        steps=tuple(
            Step(index * bars_per_chord, root, length=bars_per_chord)
            for index, root in enumerate(roots)
        ),
    )


class Progressions(Catalog):
    """The named chord progressions, each known by what it is called. A
    patch starts on `STATIC` (the tonic held) unless its rack names another."""

    STATIC = chord_changes((0,), label="Static (I)", category="Static")
    FOUR_CHORD = chord_changes(
        (0, 7, 9, 5), label="Four chords (I-V-vi-IV)", category="Pop"
    )
    DOO_WOP = chord_changes((0, 9, 5, 7), label="Doo-wop (I-vi-IV-V)", category="Pop")
    MINOR_POP = chord_changes(
        (9, 5, 0, 7), label="Minor pop (vi-IV-I-V)", category="Pop"
    )
    JAZZ_TURNAROUND = chord_changes(
        (2, 7, 0, 9), label="Jazz turnaround (ii-V-I-vi)", category="Jazz"
    )
    JAZZ_II_V_I_IV = chord_changes(
        (2, 7, 0, 5), label="Jazz ii-V-I-IV", category="Jazz"
    )
    CIRCLE_OF_FIFTHS = chord_changes(
        (0, 4, 9, 2), label="Circle of fifths (I-iii-vi-ii)", category="Circle"
    )
    CIRCLE_RUN = chord_changes(
        (4, 9, 2, 7), label="Circle run (iii-vi-ii-V)", category="Circle"
    )
    DEEP_HOUSE_MINOR = chord_changes(
        (0, 5, 10, 7), label="Deep house minor (i-iv-bVII-v)", category="House"
    )
    PSY_VAMP = chord_changes(
        (0, 0, 0, 1),
        label="Psy vamp (i-i-i-bII, two bars each)",
        category="Modal",
        bars_per_chord=2,
    )
