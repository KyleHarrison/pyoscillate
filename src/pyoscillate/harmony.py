from __future__ import annotations

import math
from dataclasses import dataclass

from pyoscillate.theory.chord import Chord
from pyoscillate.theory.phrase.base import Phrase
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.scale import Scale, Scales


@dataclass(eq=False)
class Harmony:
    """A rack's key and scale, which its pitched patches read so the bass,
    chords and pitched percussion play in one key.

    Each `Rack` owns one (a fresh copy per rack instance, since the Flet key
    control mutates it) and hands it to every patch through
    `BuildContext.harmony`; a patch that has no use for harmony ignores it.

    The chord changes are not here: each chord-following patch holds its own
    progression (a `Phrase`, see `Progressive`) and passes it to the lookups
    below, so a patch can evolve through progressions on its own timer. Racks
    seed every such patch with the same one to keep them on the same chord.
    The current chord is looked up from a bar number - pass
    `clock.bar_index` - never from a patch's own step counter. A patch's
    step count depends on its rate slider and on when it was started, so
    two patches counting their own steps drift apart; the clock's bar count
    is the same for everyone.

    Patches pull from this object at trigger time rather than being pushed
    to, so changing `key` takes effect on every patch's next note, and a
    rebuilt patch is correct on its first note with nothing to re-apply.

    Plain Python data only - no Pyo objects - so it has no graph-ownership
    duties.
    """

    # pitch class of the tonic, 0 = C ... 11 = B
    key: int = Note.KEY_A
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
        return Note.midi_to_freq(self.scale.snap(Note.freq_to_midi(freq), self.key))

    def voice(
        self, shape: Chord, root_degree: int = 0, scale: Scale | None = None
    ) -> tuple[int, ...]:
        """`shape` resolved through `scale` - the one passed in, else the
        rack's, else major - as semitones above the chord root."""
        return (scale or self.scale or Scales.MAJOR).voice(shape, root_degree)

    @staticmethod
    def chord_offset(bar: int, progression: Phrase) -> int:
        """Semitones above the key of the chord root `progression` has
        sounding in `bar`."""
        return progression.chord_root(bar)

    def chord_tones(
        self, bar: int, shape: Chord, progression: Phrase
    ) -> tuple[int, ...]:
        """`shape` stacked on the chord `progression` has sounding in `bar`, as
        semitones above the key. The stack is read from the scale (the rack's,
        else major) at the chord root's degree, so the same shape comes out
        minor on a ii and major on a I without the progression naming chord
        qualities."""
        scale = self.scale or Scales.MAJOR
        return scale.voice(shape, scale.degree(self.chord_offset(bar, progression)))

    def key_freq(self, centre: float) -> float:
        """The tonic nearest `centre` Hz."""
        return self.nearest(self.key, centre)

    def chord_freq(self, centre: float, bar: int, progression: Phrase) -> float:
        """The root of `progression`'s chord in `bar`, in the octave nearest
        `centre` Hz.

        Snapping to the nearest octave, instead of adding the progression's
        offsets on top of a fixed root, keeps each voice in its own register
        whatever the key: every root lands within a tritone of `centre`, so
        a progression like A-D-G-E never climbs out of the part's range.
        """
        return self.nearest(self.key + self.chord_offset(bar, progression), centre)

    @staticmethod
    def nearest(pitch_class: int, centre: float) -> float:
        """Frequency of `pitch_class` in the octave nearest `centre` Hz, with a
        tritone tie resolved downward."""
        centre_note = Note.freq_to_midi(centre)
        note = pitch_class % 12 + 12 * math.ceil(
            (centre_note - 6 - pitch_class % 12) / 12
        )
        return Note.midi_to_freq(note)
