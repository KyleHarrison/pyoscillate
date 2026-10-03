"""Arpeggio orders."""

from __future__ import annotations

from pyoscillate.clock import NoteDivision
from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, PhraseRole, Step


class ArpOrders(Catalog):
    """The order an arpeggio visits its note pool, as one pool index per step. An index selects `pool[index % len(pool)]` (see `Phrase.resolve`), so an order longer than the pool just cycles it and the same order works on a triad or a scale. Ported from Switch Angel's `trancearp` restart presets: `F` counts up from 0 and `B` counts down from 15, and each preset restarts them at different points across a 16-step bar. The division is nominal: a patch plays an order on its own grid."""

    # climb the pool and back down, one cycle of the pool's length x 2 - 2
    ARCH = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=10,
        mode=PhraseMode.POOL_INDEX,
        category="Order",
        roles=(PhraseRole.ARP,),
        steps=(
            Step(0, 0),
            Step(1, 1),
            Step(2, 2),
            Step(3, 3),
            Step(4, 4),
            Step(5, 5),
            Step(6, 4),
            Step(7, 3),
            Step(8, 2),
            Step(9, 1),
        ),
    )
    # F: rising all bar
    FORWARD = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        mode=PhraseMode.POOL_INDEX,
        category="Order",
        roles=(PhraseRole.ARP,),
        steps=(
            Step(0, 0),
            Step(1, 1),
            Step(2, 2),
            Step(3, 3),
            Step(4, 4),
            Step(5, 5),
            Step(6, 6),
            Step(7, 7),
            Step(8, 8),
            Step(9, 9),
            Step(10, 10),
            Step(11, 11),
            Step(12, 12),
            Step(13, 13),
            Step(14, 14),
            Step(15, 15),
        ),
    )
    # B: falling all bar
    BACKWARD = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        mode=PhraseMode.POOL_INDEX,
        category="Order",
        roles=(PhraseRole.ARP,),
        steps=(
            Step(0, 15),
            Step(1, 14),
            Step(2, 13),
            Step(3, 12),
            Step(4, 11),
            Step(5, 10),
            Step(6, 9),
            Step(7, 8),
            Step(8, 7),
            Step(9, 6),
            Step(10, 5),
            Step(11, 4),
            Step(12, 3),
            Step(13, 2),
            Step(14, 1),
            Step(15, 0),
        ),
    )
    # F restarted every three steps, then every two: a short repeating climb
    CLIMB_THREES = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        mode=PhraseMode.POOL_INDEX,
        category="Order",
        roles=(PhraseRole.ARP,),
        steps=(
            Step(0, 0),
            Step(1, 1),
            Step(2, 2),
            Step(3, 0),
            Step(4, 1),
            Step(5, 2),
            Step(6, 0),
            Step(7, 1),
            Step(8, 2),
            Step(9, 0),
            Step(10, 1),
            Step(11, 2),
            Step(12, 0),
            Step(13, 1),
            Step(14, 0),
            Step(15, 1),
        ),
    )
    # F B F B: four up, four down, repeated
    UP_DOWN_FOURS = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        mode=PhraseMode.POOL_INDEX,
        category="Order",
        roles=(PhraseRole.ARP,),
        steps=(
            Step(0, 0),
            Step(1, 1),
            Step(2, 2),
            Step(3, 3),
            Step(4, 15),
            Step(5, 14),
            Step(6, 13),
            Step(7, 12),
            Step(8, 0),
            Step(9, 1),
            Step(10, 2),
            Step(11, 3),
            Step(12, 15),
            Step(13, 14),
            Step(14, 13),
            Step(15, 12),
        ),
    )
    # a long rise, a long fall, then two stuttering restarts
    RISE_FALL_STUTTER = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        mode=PhraseMode.POOL_INDEX,
        category="Order",
        roles=(PhraseRole.ARP,),
        steps=(
            Step(0, 0),
            Step(1, 1),
            Step(2, 2),
            Step(3, 3),
            Step(4, 4),
            Step(5, 5),
            Step(6, 15),
            Step(7, 14),
            Step(8, 13),
            Step(9, 12),
            Step(10, 11),
            Step(11, 10),
            Step(12, 0),
            Step(13, 1),
            Step(14, 0),
            Step(15, 1),
        ),
    )
    # a long rise that resets twice to the root at the end of the bar
    RISE_RESET = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        mode=PhraseMode.POOL_INDEX,
        category="Order",
        roles=(PhraseRole.ARP,),
        steps=(
            Step(0, 0),
            Step(1, 1),
            Step(2, 2),
            Step(3, 3),
            Step(4, 4),
            Step(5, 5),
            Step(6, 6),
            Step(7, 7),
            Step(8, 8),
            Step(9, 9),
            Step(10, 10),
            Step(11, 11),
            Step(12, 0),
            Step(13, 1),
            Step(14, 0),
            Step(15, 1),
        ),
    )
