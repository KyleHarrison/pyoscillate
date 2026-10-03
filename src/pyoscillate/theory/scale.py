"""Scales as semitone offsets above the key."""

from __future__ import annotations

import math
from dataclasses import dataclass

from pyoscillate.theory.catalog import Catalog, CatalogItem
from pyoscillate.theory.chord import Chord, ChordUnit


@dataclass(frozen=True, eq=False, kw_only=True)
class Scale(CatalogItem):
    """A scale as semitone offsets above the key, for `Harmony.scale` and for
    patches that draw a random scale tone."""

    offsets: tuple[int, ...]

    def voice(self, chord: Chord, root_degree: int = 0) -> tuple[int, ...]:
        """`chord` as semitones above the chord root. A `DEGREES` chord is
        stepped through this scale, so one voicing is minor in a minor scale
        and major in a major one; `root_degree` shifts the whole shape up that
        many scale degrees first, as Strudel's `chrd` does, and degrees past
        the scale's last tone wrap into the next octave. A `SEMITONES` chord
        is already in semitones and comes back as written."""
        if chord.unit is ChordUnit.SEMITONES:
            return tuple(int(offset) for offset in chord.offsets)
        semitones = []
        for degree in chord.offsets:
            octave, step = divmod(degree + root_degree, len(self.offsets))
            semitones.append(self.offsets[step] + 12 * octave)
        return tuple(semitones)

    def degree(self, offset: int) -> int:
        """Index of the scale tone nearest `offset` semitones above the key
        (a chord root's scale degree); equidistant tones resolve downward."""
        return min(
            range(len(self.offsets)),
            key=lambda i: (abs(self.offsets[i] - offset % 12), i),
        )

    def snap(self, note: float, key: int) -> float:
        """MIDI `note` moved to the nearest tone of this scale in `key`
        (a pitch class); equidistant tones resolve downward."""
        octave = math.floor((note - key) / 12)
        candidates = (
            key + 12 * o + degree
            for o in (octave - 1, octave, octave + 1)
            for degree in self.offsets
        )
        return min(candidates, key=lambda c: (abs(c - note), c))


class Scales(Catalog):
    """The scales a rack or patch can be set to."""

    MAJOR = Scale(offsets=(0, 2, 4, 5, 7, 9, 11), category="Diatonic")
    MINOR = Scale(offsets=(0, 2, 3, 5, 7, 8, 10), category="Diatonic")
    MAJOR_PENTATONIC = Scale(offsets=(0, 2, 4, 7, 9), category="Pentatonic")
    MINOR_PENTATONIC = Scale(offsets=(0, 3, 5, 7, 10), category="Pentatonic")
    # major pentatonic closed at the octave, for random-draw melodies
    MAJOR_PENTATONIC_OCTAVE = Scale(offsets=(0, 2, 4, 7, 9, 12), category="Pentatonic")
