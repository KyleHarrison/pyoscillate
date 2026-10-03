"""Fills and figures that sound once per phrase."""

from __future__ import annotations

from pyoscillate.clock import NoteDivision
from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, PhraseRole, Step


class Fills(Catalog):
    """Sparse figures that sound once in a phrase: a tom fill, a bell ring. Offsets are semitones above the chord root (the bell measures from its Register instead)."""

    # fifth, fifth, minor third, root: a two-bar fill walking down the minor
    # pentatonic, all four tones of the rack's minor-seventh chords
    TOM_FILL = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=32,
        label="Descending fill: fifth, fifth, third, root over two bars",
        mode=PhraseMode.SEMITONES,
        category="Fill",
        roles=(PhraseRole.FILL,),
        steps=(
            Step(10, Interval.PERFECT_FIFTH),
            Step(26, Interval.PERFECT_FIFTH),
            Step(29, Interval.MINOR_THIRD),
            Step(31, Interval.UNISON),
        ),
    )
    # a two-bar minor-pentatonic figure, one ring per phrase (for the bell,
    # measured from its Register rather than the chord root)
    BELL_FIGURE = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=32,
        label="Bell figure: a two-bar minor-pentatonic ring",
        mode=PhraseMode.SEMITONES,
        category="Figure",
        roles=(PhraseRole.BELL,),
        steps=(
            Step(0, Interval.OCTAVE),
            Step(6, Interval.PERFECT_FIFTH),
            Step(12, Interval.MINOR_SEVENTH),
            Step(16, Interval.MINOR_THIRD),
            Step(22, Interval.PERFECT_FOURTH),
            Step(28, Interval.UNISON),
        ),
    )
