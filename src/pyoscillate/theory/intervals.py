"""Named semitone-interval lookups shared by every pitched patch.

Each enum member's `.value` is a tuple of semitones above a root, so a patch
names the musical idea (`Chord.MINOR_7`) instead of carrying a raw list.
Members must keep distinct values: Enum folds equal values into aliases.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import NamedTuple, Self


class Choice(Enum):
    """Base for the lookups a patch parameter selects by index. A `Param`
    stores the index; `by_index` clamps it to the members, and `labels` are
    the matching dropdown texts. Both walk `__members__`, so an alias (equal
    values fold into the first name) keeps its own index and label - never
    index `list(cls)`, which drops aliases."""

    @classmethod
    def by_index(cls, index: int) -> Self:
        """The member numbered `index`, clamped to the available range."""
        members = tuple(cls.__members__.values())
        return members[max(0, min(index, len(members) - 1))]

    @classmethod
    def labels(cls) -> tuple[str, ...]:
        """Display text for each index, in index order."""
        return tuple(name.replace("_", " ").capitalize() for name in cls.__members__)


class Phrase(NamedTuple):
    """A melodic phrase: `steps` maps a step to its semitone offset above the
    current chord root, and an absent step is a rest. `cycle` is the number of
    steps one pass spans."""

    cycle: int
    steps: dict[int, int]


class Scale(Enum):
    """Scales as semitone offsets above the key, for `Harmony.scale` and for
    patches that draw a random scale tone."""

    MAJOR = (0, 2, 4, 5, 7, 9, 11)
    MINOR = (0, 2, 3, 5, 7, 8, 10)
    MAJOR_PENTATONIC = (0, 2, 4, 7, 9)
    MINOR_PENTATONIC = (0, 3, 5, 7, 10)
    # major pentatonic closed at the octave, for random-draw melodies
    MAJOR_PENTATONIC_OCTAVE = (0, 2, 4, 7, 9, 12)

    def voice(self, shape: Voicing, root_degree: int = 0) -> tuple[int, ...]:
        """`shape`'s scale degrees as semitones above the chord root, stepped
        through this scale, so one voicing is minor in a minor scale and major
        in a major one. `root_degree` shifts the whole shape up that many
        scale degrees first, as Strudel's `chrd` does. Degrees past the
        scale's last tone wrap into the next octave."""
        semitones = []
        for degree in shape.value:
            octave, step = divmod(degree + root_degree, len(self.value))
            semitones.append(self.value[step] + 12 * octave)
        return tuple(semitones)

    def degree(self, offset: int) -> int:
        """Index of the scale tone nearest `offset` semitones above the key
        (a chord root's scale degree); equidistant tones resolve downward."""
        return min(
            range(len(self.value)),
            key=lambda i: (abs(self.value[i] - offset % 12), i),
        )

    def snap(self, note: float, key: int) -> float:
        """MIDI `note` moved to the nearest tone of this scale in `key`
        (a pitch class); equidistant tones resolve downward."""
        octave = math.floor((note - key) / 12)
        candidates = (
            key + 12 * o + degree
            for o in (octave - 1, octave, octave + 1)
            for degree in self.value
        )
        return min(candidates, key=lambda c: (abs(c - note), c))


class ChordShape(Enum):
    """Chord shapes as semitones above the chord root, lowest voice first."""

    # open fifth topped with the octave, a hollow bed that fits any mode
    OPEN_FIFTH = (0, 7, 12)


class Walk(Enum):
    """Ordered interval sequences an arpeggio or drone steps through,
    semitones from its root; the order is the melody."""

    # minor-7th chord tones up to the octave and back
    MINOR_7_ARCH = (0, 3, 7, 10, 12, 10, 7, 3)
    # slow wandering line around the root, dipping below it
    DRONE_WANDER = (0, -5, -3, 2, 0, -7, -5, 3)


class Voicing(Choice):
    """Chord shapes as **scale degrees** above the chord root (not
    semitones), lowest voice first: `(0, 2, 4)` is a triad in whatever scale
    it is resolved against. Resolve with `Harmony.voice`.

    Ported from Switch Angel's strudel-scripts `chordshapes`; `by_index`
    keeps her numbering so a Strudel variation number selects the same
    shape. Equal shapes become aliases of the first name, so look up by
    index through `by_index`, never `list(Voicing)`.
    """

    POWER_CHORD = (0, 4)
    TRIAD = (0, 2, 4)
    SPREAD_TRIAD = (-7, 0, 2, 4, 7)
    SPREAD_SUS4_TRIAD = (-7, 0, 2, 3, 7)
    SEVENTH_CHORD = (0, 2, 4, 6)
    MINOR_7TH_CLUSTER = (0, 2, 3, 6)
    OPEN_TRIAD = (0, 4, 7, 9)
    OPEN_SUSPENDED_TRIAD = (0, 4, 7, 8)
    OPEN_7TH = (0, 4, 6, 9)
    JAZZ_TENTH = (0, 2, 6, 9)
    ELEVENTH_CHORD = (0, 2, 6, 10)
    NINTH_CHORD = (0, 2, 4, 6, 8)
    WIDE_13TH = (-7, 0, 2, 6, 9)
    SIX_NINE_EXTENDED = (0, 4, 7, 9, 13)
    HIGH_TENSION_EXTENSION = (0, 4, 8, 9, 13)
    HIGH_CLUSTER_A = (0, 2, 7, 8, 11)
    HIGH_CLUSTER_B = (0, 2, 8, 9, 11)
    # same notes as SPREAD_SUS4_TRIAD, kept as its own name at Strudel index 17
    WIDE_SUSPENDED_SPREAD = SPREAD_SUS4_TRIAD

    # EDM / Melodic House / Future Bass
    SUS2_STACK = (0, 3, 4)
    SUS4_STACK = (0, 1, 4)
    DENSE_TRIAD_CLUSTER = (0, 2, 3, 4)
    ADD9_TRIAD = (0, 2, 4, 8)
    ADD9_6 = (0, 2, 4, 9)
    SOFT_MAJOR_9 = (0, 4, 6, 8)
    DREAMY_SPREAD = (0, 2, 5, 9)
    AMBIENT_OPEN_STACK = (0, 4, 7, 11)
    FIFTH_UPPER_CLUSTER = (0, 7, 9, 11)
    WIDE_ADD9 = (0, 2, 7, 11)
    WIDE_POWER_CHORD = (-7, 0, 4, 7)
    BASS_7TH = (-7, 0, 4, 6)
    DEEP_HOUSE_VOICING = (-7, 0, 2, 9)
    FESTIVAL_HOUSE = (-7, 0, 4, 9)
    PROGRESSIVE_STACK = (-7, 0, 2, 4, 9)
    FULL_EXTENDED_HOUSE = (-7, 0, 2, 4, 6, 9)
    CINEMATIC_MINOR_FEEL = (-7, 0, 2, 4, 8)
    SUSPENDED_BASS_SPREAD = (-7, 0, 3, 7, 10)

    # Future Bass / Porter / Illenium style
    FUTURE_BASS_MAJOR = (0, 2, 4, 8, 11)
    FUTURE_BASS_11TH = (0, 2, 4, 6, 11)
    BRIGHT_EMOTIONAL_STACK = (0, 2, 4, 9, 11)
    LUSH_EXTENDED = (0, 2, 6, 9, 11)
    WIDE_EMOTIONAL_CLUSTER = (0, 4, 6, 8, 11)
    HYBRID_CLUSTER = (0, 2, 3, 7, 11)
    TENSION_PAD = (0, 1, 4, 8, 11)
    MASSIVE_CLUSTER = (0, 1, 2, 4, 11)
    ORGANIC_PAD_CHORD = (0, 2, 4, 5, 9)
    SHIMMER_STACK = (0, 4, 5, 9, 11)

    # Techno / Minimal / Darker voicings
    DARK_CLUSTER = (0, 1, 4, 7)
    MINOR_CLUSTER = (0, 1, 3, 7)
    TIGHT_OPEN_CHORD = (0, 4, 5, 7)
    QUARTAL_STACK = (0, 5, 7)
    QUARTAL_7TH = (0, 5, 7, 10)
    HOLLOW_FIFTH_STACK = (0, 5, 10)
    WIDE_QUARTAL = (-7, 0, 5, 7)
    DARK_BASS_CLUSTER = (-7, 0, 1, 5)
    INDUSTRIAL_SPREAD = (-7, -3, 0, 5)
    ACID_TENSION = (0, 1, 5, 8)
    SUSPENDED_DARK_CHORD = (0, 3, 5, 8)

    # Trance / Uplifting / Big room
    BIG_ROOM_ADD9 = (0, 2, 4, 7)
    EPIC_TRANCE_STACK = (0, 4, 7, 11, 14)
    HUGE_SPREAD_STACK = (-7, 0, 2, 4, 7, 11)
    FULL_ATMOSPHERIC = (0, 2, 4, 6, 9, 11)
    ANTHEM_LEAD_STACK = (0, 7, 11, 14)
    EMOTIONAL_SUPERSAW = (0, 2, 9, 11, 14)
    CINEMATIC_WIDE_CHORD = (-12, 0, 4, 7, 11)
    MASSIVE_OCTAVE_SPREAD = (-12, -7, 0, 4, 7)

    # Experimental / modern electronic
    CHROMATIC_CLUSTER = (0, 1, 2)
    DENSE_MODERN_CLUSTER = (0, 1, 2, 4)
    FLOATING_AMBIENCE = (0, 2, 3, 5, 8)
    UNRESOLVED_TEXTURE = (0, 4, 5, 8, 9)
    QUARTAL_HYBRID = (0, 2, 5, 7, 11)
    CINEMATIC_MINOR_9 = (0, 3, 7, 10, 14)
    FULL_LYDIAN_STACK = (0, 2, 4, 7, 9, 11)
    TENSION_WASH = (0, 1, 4, 6, 11)
    POLY_CLUSTER = (0, 2, 6, 7, 11)
    BRIGHT_MODERN_EXTENSION = (0, 4, 8, 11, 14)

    # Comping
    # third, fifth, seventh and ninth with the root left to the bass: a close
    # four-note stack, minor 9th on a ii and major 9th on a I in a major key
    ROOTLESS_NINTH = (2, 4, 6, 8)
    # third, seventh, ninth and thirteenth: the fuller colour a dominant
    # chord takes in place of the plain ninth
    ROOTLESS_THIRTEENTH = (2, 6, 8, 12)


class ArpOrder(Choice):
    """The order an arpeggio visits its note pool, as one index per step.

    An index selects `pool[index % len(pool)]`, so an order longer than the
    pool just cycles it, and the same preset works on a triad or a scale.
    Ported from Switch Angel's `trancearp` restart presets: `F` counts up
    from 0 and `B` counts down from 15, and each preset restarts them at
    different points across a 16-step bar. Member order is the Strudel
    preset number after `ARCH`; use `by_index`.
    """

    # climb the pool and back down, one cycle of the pool's length x 2 - 2
    ARCH = (0, 1, 2, 3, 4, 5, 4, 3, 2, 1)
    # F: rising all bar
    FORWARD = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
    # B: falling all bar
    BACKWARD = (15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)
    # F restarted every three steps, then every two: a short repeating climb
    CLIMB_THREES = (0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 0, 1)
    # F B F B: four up, four down, repeated
    UP_DOWN_FOURS = (0, 1, 2, 3, 15, 14, 13, 12, 0, 1, 2, 3, 15, 14, 13, 12)
    # a long rise, a long fall, then two stuttering restarts
    RISE_FALL_STUTTER = (0, 1, 2, 3, 4, 5, 15, 14, 13, 12, 11, 10, 0, 1, 0, 1)
    # a long rise that resets twice to the root at the end of the bar
    RISE_RESET = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 0, 1)

    @property
    def cycle(self) -> int:
        """The number of steps one pass of this order spans."""
        return len(self.value)

    def intervals(self, pool: tuple[int, ...]) -> tuple[int, ...]:
        """This order's semitone offset at each step, drawn from `pool`."""
        return tuple(pool[index % len(pool)] for index in self.value)

    def steps(self, pool: tuple[int, ...]) -> dict[int, int]:
        """`intervals` keyed by step, the form `step_pattern` reads."""
        return dict(enumerate(self.intervals(pool)))


class Progression(Choice):
    """Chord changes as roots, one per bar, in semitones above the key of a
    major scale. Give one to `Harmony.progression` and every pitched patch that
    reads the rack's harmony follows the same changes; the chord
    quality (minor, major, dominant) comes from the scale degree each root
    sits on, not from this table. Members are named for what the progression
    is known as; `labels` add the roman numerals (lowercase for a minor chord).
    """

    FOUR_CHORD = (0, 7, 9, 5)
    DOO_WOP = (0, 9, 5, 7)
    MINOR_POP = (9, 5, 0, 7)
    JAZZ_TURNAROUND = (2, 7, 0, 9)
    JAZZ_II_V_I_IV = (2, 7, 0, 5)
    CIRCLE_OF_FIFTHS = (0, 4, 9, 2)
    CIRCLE_RUN = (4, 9, 2, 7)

    @property
    def roots(self) -> tuple[int, ...]:
        """Chord roots, semitones above the key, one per bar."""
        return self.value

    @classmethod
    def labels(cls) -> tuple[str, ...]:
        """Display names with the roman numerals, in index order."""
        return (
            "Four chords (I-V-vi-IV)",
            "Doo-wop (I-vi-IV-V)",
            "Minor pop (vi-IV-I-V)",
            "Jazz turnaround (ii-V-I-vi)",
            "Jazz ii-V-I-IV",
            "Circle of fifths (I-iii-vi-ii)",
            "Circle run (iii-vi-ii-V)",
        )

    @property
    def index(self) -> int:
        """This preset's position in the dropdown, the index `by_index`
        takes."""
        return tuple(type(self).__members__.values()).index(self)


class Rhythm(Choice):
    """Hit patterns for any gated patch, as `((step, velocity), ...)` on a 16-step
    bar of 16ths. A patch reads `hits` into its `step_pattern`; where a voice
    maps velocity to brightness (see `Keys`), the accents shape the timbre as
    well as the level."""

    # beat one, then the "and" of two
    CHARLESTON = ((0, 1.0), (6, 0.55))
    # a stab on every beat, the downbeats strongest
    FOUR_ON_THE_FLOOR = ((0, 1.0), (4, 0.7), (8, 0.85), (12, 0.7))
    # the "and" of every beat, the house offbeat
    OFFBEAT_HOUSE = ((2, 0.9), (6, 0.8), (10, 0.9), (14, 0.8))
    # one chord a bar, left to ring
    WHOLE_BAR = ((0, 1.0),)
    # pushes ahead of beats two and four
    SYNCOPATED_PUSH = ((0, 1.0), (5, 0.6), (8, 0.8), (11, 0.55))

    @property
    def hits(self) -> dict[int, float]:
        """Step -> velocity, the form `step_pattern` reads."""
        return dict(self.value)

    @classmethod
    def labels(cls) -> tuple[str, ...]:
        return (
            "Charleston: beat 1 and the 'and' of 2",
            "Four on the floor: every beat",
            "Offbeat house: every 'and'",
            "Whole bar: one chord a bar",
            "Syncopated push: ahead of the beat",
        )
