"""Named musical intervals, as semitone counts."""

from __future__ import annotations

from enum import IntEnum


class Interval(IntEnum):
    """A musical interval as its width in semitones. An `IntEnum`, so a
    member is usable anywhere a semitone offset is (`Note.transpose(freq,
    Interval.PERFECT_FIFTH)`), and `-Interval.PERFECT_FIFTH` is the fifth
    below. Use it where an offset names an interval; a scale degree or a
    pool index stays a plain int."""

    UNISON = 0
    MINOR_SECOND = 1
    MAJOR_SECOND = 2
    MINOR_THIRD = 3
    MAJOR_THIRD = 4
    PERFECT_FOURTH = 5
    TRITONE = 6
    PERFECT_FIFTH = 7
    MINOR_SIXTH = 8
    MAJOR_SIXTH = 9
    MINOR_SEVENTH = 10
    MAJOR_SEVENTH = 11
    OCTAVE = 12
    MINOR_NINTH = 13
    MAJOR_NINTH = 14
