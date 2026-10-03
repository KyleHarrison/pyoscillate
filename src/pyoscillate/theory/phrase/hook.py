"""Chord-tone hook figures."""

from __future__ import annotations

from pyoscillate.clock import NoteDivision
from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, Step


class Hooks(Catalog):
    """Hook figures whose offset indexes the current chord's triad (0 root, 1 third, 2 fifth) instead of a fixed interval, so the figure takes the chord's own major or minor colour."""

    # a root, third, fifth, third climb that leaves the off-steps empty
    SPARSE_HOOK = Phrase(
        division=NoteDivision.EIGHTH,
        cycle=8,
        label="Sparse hook: root, third, fifth, third",
        mode=PhraseMode.CHORD_TONE,
        category="Hook",
        steps=(
            Step(0, 0),
            Step(2, 1),
            Step(4, 2),
            Step(6, 1),
        ),
    )
    # every eighth filled, the triad rocked back and forth
    FULL_HOOK = Phrase(
        division=NoteDivision.EIGHTH,
        cycle=8,
        label="Full hook: the triad rocked through every eighth",
        mode=PhraseMode.CHORD_TONE,
        category="Hook",
        steps=(
            Step(0, 0),
            Step(1, 1),
            Step(2, 2),
            Step(3, 1),
            Step(4, 0),
            Step(5, 2),
            Step(6, 1),
            Step(7, 2),
        ),
    )
