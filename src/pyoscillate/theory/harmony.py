from __future__ import annotations

import math
from dataclasses import dataclass

from pyoscillate.theory.intervals import Progression, Scale, Voicing
from pyoscillate.theory.notes import freq_to_midi, midi_to_freq

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
    # the chord changes: a named `Progression`, or chord roots (semitones
    # above the key, one per bar) for changes the table doesn't name. Read
    # the roots through `roots`.
    progression: Progression | tuple[int, ...] = (0,)
    bars_per_chord: int = 1
    # the scale `quantise` snaps to and `voice` reads by default; None means
    # no scale is set and `quantise` leaves pitches alone
    scale: Scale | None = None

    def quantise(self, freq: float) -> float:
        """`freq` snapped to the nearest note of the rack's `scale` in `key`.

        A pitch stream that is not itself drawn from the key (a free-running
        melody, an arp on a hand-set register) goes through this to stay in
        key. Equidistant notes resolve downward. Returns `freq` unchanged
        when no `scale` is set, so an unconfigured rack sounds as before.
        """
        if not self.scale:
            return freq
        return midi_to_freq(self.scale.snap(freq_to_midi(freq), self.key))

    def voice(
        self, shape: Voicing, root_degree: int = 0, scale: Scale | None = None
    ) -> tuple[int, ...]:
        """`shape` resolved through `scale` - the one passed in, else the
        rack's, else major - as semitones above the chord root."""
        return (scale or self.scale or Scale.MAJOR).voice(shape, root_degree)

    @property
    def roots(self) -> tuple[int, ...]:
        """The progression's chord roots, semitones above the key, one per
        bar."""
        if isinstance(self.progression, Progression):
            return self.progression.roots
        return self.progression

    def chord_offset(self, bar: int) -> int:
        """Semitones above the key of the chord root sounding in `bar`."""
        index = (bar // self.bars_per_chord) % len(self.roots)
        return self.roots[index]

    def chord_tones(self, bar: int, shape: Voicing) -> tuple[int, ...]:
        """`shape` stacked on the chord sounding in `bar`, as semitones above
        the key. The stack is read from the scale (the rack's, else major) at
        the chord root's degree, so the same shape comes out minor on a ii and
        major on a I without the progression naming chord qualities."""
        scale = self.scale or Scale.MAJOR
        return scale.voice(shape, scale.degree(self.chord_offset(bar)))

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
    centre_note = freq_to_midi(centre)
    note = pitch_class % 12 + 12 * math.ceil((centre_note - 6 - pitch_class % 12) / 12)
    return midi_to_freq(note)
