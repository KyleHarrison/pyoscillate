"""Interval walks."""

from __future__ import annotations

from pyoscillate.clock import NoteDivision
from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, PhraseRole, Step


class Walks(Catalog):
    """Ordered interval sequences an arpeggio or drone steps through, as semitones from its root; the order is the melody. The division is nominal: a patch steps a walk at its own pace."""

    # minor-7th chord tones up to the octave and back
    MINOR_7_ARCH = Phrase(
        division=NoteDivision.QUARTER,
        cycle=8,
        mode=PhraseMode.SEMITONES,
        category="Walk",
        roles=(PhraseRole.DRONE,),
        steps=(
            Step(0, Interval.UNISON),
            Step(1, Interval.MINOR_THIRD),
            Step(2, Interval.PERFECT_FIFTH),
            Step(3, Interval.MINOR_SEVENTH),
            Step(4, Interval.OCTAVE),
            Step(5, Interval.MINOR_SEVENTH),
            Step(6, Interval.PERFECT_FIFTH),
            Step(7, Interval.MINOR_THIRD),
        ),
    )
    # slow wandering line around the root, dipping below it
    DRONE_WANDER = Phrase(
        division=NoteDivision.QUARTER,
        cycle=8,
        mode=PhraseMode.SEMITONES,
        category="Walk",
        roles=(PhraseRole.DRONE,),
        steps=(
            Step(0, Interval.UNISON),
            Step(1, -Interval.PERFECT_FOURTH),
            Step(2, -Interval.MINOR_THIRD),
            Step(3, Interval.MAJOR_SECOND),
            Step(4, Interval.UNISON),
            Step(5, -Interval.PERFECT_FIFTH),
            Step(6, -Interval.PERFECT_FOURTH),
            Step(7, Interval.MINOR_THIRD),
        ),
    )
