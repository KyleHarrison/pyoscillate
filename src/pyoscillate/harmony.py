from __future__ import annotations

import math
from dataclasses import dataclass

NOTE_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
# pitch class of C, for a rack whose vamp is easiest to name off a major-key
# centre (e.g. roman-numeral chords built from scale degrees)
C = 0
# pitch class of F, for the dark psytrance racks
F = 5
# pitch class of A, the default key for racks that don't choose one
A = 9


@dataclass(eq=False)
class Harmony:
    """Rack-level key and chord progression that every pitched patch reads
    from, so the bass, chords and pitched percussion change chord together.

    The current chord is looked up from a bar number - pass
    `clock.bar_index` - never from a patch's own step counter. A patch's
    step count depends on its rate slider and on when it was started, so
    two patches counting their own steps drift apart; the clock's bar count
    is the same for everyone.

    Patches pull from this object at trigger time rather than being pushed
    to, so changing `key` takes effect on every patch's next note, and a
    rebuilt patch is correct on its first note with nothing to re-apply.

    Plain Python data only - no Pyo objects - so it has no graph-ownership
    duties and can live as a module-level value in a project's rack.
    """

    # pitch class of the tonic, 0 = C ... 11 = B
    key: int = A
    # chord roots, as semitones above the key
    progression: tuple[int, ...] = (0,)
    bars_per_chord: int = 1

    def chord_offset(self, bar: int) -> int:
        """Semitones above the key of the chord root sounding in `bar`."""
        index = (bar // self.bars_per_chord) % len(self.progression)
        return self.progression[index]

    def key_freq(self, centre: float) -> float:
        """The tonic nearest `centre` Hz."""
        return _nearest(self.key, centre)

    def chord_freq(self, centre: float, bar: int) -> float:
        """The root of `bar`'s chord, in the octave nearest `centre` Hz.

        Snapping to the nearest octave, instead of adding the progression's
        offsets on top of a fixed root, keeps each voice in its own register
        whatever the key: every root lands within a tritone of `centre`, so
        a progression like A-D-G-E never climbs out of the part's range.
        """
        return _nearest(self.key + self.chord_offset(bar), centre)


def _nearest(pitch_class: int, centre: float) -> float:
    """Frequency of `pitch_class` in the octave nearest `centre` Hz, with a
    tritone tie resolved downward."""
    centre_note = 69 + 12 * math.log2(centre / 440)
    note = pitch_class % 12 + 12 * math.ceil((centre_note - 6 - pitch_class % 12) / 12)
    return 440 * 2 ** ((note - 69) / 12)
