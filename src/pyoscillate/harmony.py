from __future__ import annotations

import math
from dataclasses import dataclass

from pyoscillate.intervals import Scale, Voicing

NOTE_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
# pitch class of C, for a rack whose vamp is easiest to name off a major-key
# centre (e.g. roman-numeral chords built from scale degrees)
C = 0
# pitch class of F, for the dark psytrance racks
F = 5
# pitch class of A, the default key for racks that don't choose one
A = 9


# scales as semitone offsets above the key, for `Harmony.scale`


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
    # scale degrees as semitones above the key that `quantise` snaps to;
    # None means no scale is set and `quantise` leaves pitches alone
    scale: tuple[int, ...] | None = None

    def quantise(self, freq: float) -> float:
        """`freq` snapped to the nearest note of the rack's `scale` in `key`.

        A pitch stream that is not itself drawn from the key (a free-running
        melody, an arp on a hand-set register) goes through this to stay in
        key. Equidistant notes resolve downward. Returns `freq` unchanged
        when no `scale` is set, so an unconfigured rack sounds as before.
        """
        if not self.scale:
            return freq
        note = 69 + 12 * math.log2(freq / 440)
        octave = math.floor((note - self.key) / 12)
        candidates = (
            self.key + 12 * o + degree
            for o in (octave - 1, octave, octave + 1)
            for degree in self.scale
        )
        nearest = min(candidates, key=lambda c: (abs(c - note), c))
        return 440 * 2 ** ((nearest - 69) / 12)

    def voice(
        self, shape: Voicing, root_degree: int = 0, scale: Scale | None = None
    ) -> tuple[int, ...]:
        """`shape`'s scale degrees as semitones above the chord root, stepped
        through `scale` - the one passed in, else the rack's, else major - so
        one voicing is minor in a minor scale and major in a major one.
        `root_degree` shifts the whole
        shape up that many scale degrees first, as Strudel's `chrd` does.
        Degrees past the scale's last tone wrap into the next octave.
        """
        tones_in = (scale.value if scale else self.scale) or Scale.MAJOR.value
        tones = len(tones_in)
        semitones = []
        for degree in shape.value:
            octave, step = divmod(degree + root_degree, tones)
            semitones.append(tones_in[step] + 12 * octave)
        return tuple(semitones)

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
