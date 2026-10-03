"""Lead lines."""

from __future__ import annotations

from pyoscillate.clock import NoteDivision
from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, Step


class Leads(Catalog):
    """Note lines for a pitched lead, as semitones above the current chord root."""

    # root up the major triad to the octave and back; step 6 rests so the
    # phrase has somewhere for its release tail to be heard
    LEAD_ARCH = Phrase(
        division=NoteDivision.EIGHTH,
        cycle=8,
        label="Arch: root up the triad to the octave and back",
        mode=PhraseMode.SEMITONES,
        category="Motif",
        steps=(
            Step(0, Interval.UNISON),
            Step(1, Interval.MAJOR_THIRD),
            Step(2, Interval.PERFECT_FIFTH),
            Step(3, Interval.OCTAVE),
            Step(4, Interval.PERFECT_FIFTH),
            Step(5, Interval.MAJOR_THIRD),
            Step(7, Interval.UNISON),
        ),
    )
    # a minor-pentatonic-ish phrase (root, minor 3rd, 5th, minor 7th) that
    # leaves space after each two- or three-note idea
    MUTED_KEYS = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Muted motif: a sparse minor-pentatonic phrase",
        mode=PhraseMode.SEMITONES,
        category="Motif",
        steps=(
            Step(0, Interval.UNISON),
            Step(3, Interval.MINOR_THIRD),
            Step(6, Interval.PERFECT_FIFTH),
            Step(8, Interval.MINOR_SEVENTH),
            Step(11, Interval.PERFECT_FIFTH),
            Step(13, Interval.MINOR_THIRD),
        ),
    )
    # sparse, floating long notes for a hollow reed
    WIND_DRIFT = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=32,
        label="Wind drift: sparse, floating long notes",
        mode=PhraseMode.SEMITONES,
        category="Wind",
        steps=(
            Step(0, Interval.PERFECT_FIFTH),
            Step(5, Interval.MINOR_SIXTH),
            Step(8, Interval.PERFECT_FIFTH),
            Step(12, Interval.PERFECT_FOURTH),
            Step(16, Interval.MINOR_THIRD),
            Step(21, Interval.PERFECT_FOURTH),
            Step(24, Interval.PERFECT_FIFTH),
            Step(28, Interval.MINOR_SECOND),
        ),
    )
    # the wind line turned over, starting from the octave
    WIND_DRIFT_B = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=32,
        label="Wind drift B: the same drift falling from the octave",
        mode=PhraseMode.SEMITONES,
        category="Wind",
        steps=(
            Step(0, Interval.OCTAVE),
            Step(6, Interval.MINOR_SEVENTH),
            Step(10, Interval.MINOR_SIXTH),
            Step(14, Interval.PERFECT_FIFTH),
            Step(16, Interval.PERFECT_FOURTH),
            Step(22, Interval.MINOR_THIRD),
            Step(26, Interval.MINOR_SECOND),
            Step(30, Interval.UNISON),
        ),
    )
    # a short, syncopated, sliding 16th-note groove
    SWIRL_GROOVE = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=32,
        label="Swirl groove: syncopated 16ths sliding through the minor scale",
        mode=PhraseMode.SEMITONES,
        category="Groove",
        steps=(
            Step(0, Interval.PERFECT_FIFTH),
            Step(3, Interval.PERFECT_FIFTH),
            Step(6, Interval.MINOR_SIXTH),
            Step(8, Interval.PERFECT_FIFTH),
            Step(10, Interval.PERFECT_FOURTH),
            Step(12, Interval.MINOR_THIRD),
            Step(14, Interval.PERFECT_FOURTH),
            Step(16, Interval.PERFECT_FIFTH),
            Step(19, Interval.MINOR_SEVENTH),
            Step(22, Interval.MINOR_SIXTH),
            Step(24, Interval.PERFECT_FIFTH),
            Step(27, Interval.PERFECT_FOURTH),
            Step(30, Interval.MINOR_SECOND),
        ),
    )
    # the swirl groove answered by a falling line from the octave
    SWIRL_GROOVE_B = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=32,
        label="Swirl groove B: the same groove falling from the octave",
        mode=PhraseMode.SEMITONES,
        category="Groove",
        steps=(
            Step(0, Interval.OCTAVE),
            Step(2, Interval.MINOR_SEVENTH),
            Step(3, Interval.MINOR_SIXTH),
            Step(6, Interval.PERFECT_FIFTH),
            Step(8, Interval.MINOR_SIXTH),
            Step(11, Interval.PERFECT_FIFTH),
            Step(14, Interval.PERFECT_FOURTH),
            Step(16, Interval.MINOR_THIRD),
            Step(18, Interval.PERFECT_FOURTH),
            Step(19, Interval.PERFECT_FIFTH),
            Step(22, Interval.PERFECT_FOURTH),
            Step(24, Interval.MINOR_THIRD),
            Step(27, Interval.MINOR_SECOND),
            Step(28, Interval.UNISON),
            Step(30, Interval.MINOR_SECOND),
        ),
    )
