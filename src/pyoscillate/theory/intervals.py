"""Named semitone-interval lookups shared by every pitched patch.

Each enum member's `.value` is a tuple of semitones above a root, so a patch
names the musical idea (`Chord.MINOR_7`) instead of carrying a raw list.
Members must keep distinct values: Enum folds equal values into aliases.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Self

from pyoscillate.clock import NoteDivision


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

    @property
    def index(self) -> int:
        """This member's position in the dropdown, the index `by_index`
        takes."""
        return tuple(type(self).__members__.values()).index(self)


class Pattern(Choice):
    """Base for the step patterns every gated patch selects from, so a pattern
    is written once here and any patch can play it. A member's value is
    `(division, cycle, entries, label)`: `division` is the grid a step lasts,
    `cycle` the steps one pass spans, `entries` one tuple per step that
    sounds (an absent step is a rest) and `label` the dropdown text. What an
    entry carries beyond its step depends on the family: a velocity for a
    `Rhythm`, a semitone offset for a `Melody`, a chord-tone index for
    `ChordTones`. A patch holds the chosen member's index in a `Param` (see
    `choice_param`) and reads its steps through `step_pattern`.
    """

    @property
    def division(self) -> NoteDivision:
        """The grid one step lasts."""
        return self.value[0]

    @property
    def cycle(self) -> int:
        """The number of steps one pass of this pattern spans."""
        return self.value[1]

    @classmethod
    def labels(cls) -> tuple[str, ...]:
        return tuple(member.value[3] for member in cls.__members__.values())


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


class Walk(Choice):
    """Ordered interval sequences an arpeggio or drone steps through,
    semitones from its root; the order is the melody. A patch selects one
    from a dropdown, so a member's dropdown index is its position here."""

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


class Rhythm(Pattern):
    """Hit patterns for any percussive or chord-striking patch, as
    `((step, velocity), ...)`; a third `True` marks a hat hit as open rather
    than closed. A patch reads `hits` (step -> velocity) into its
    `step_pattern`; where a voice maps velocity to brightness (see `Keys`),
    the accents shape the timbre as well as the level. Members are only ever
    appended, so a saved dropdown index keeps meaning the same pattern."""

    # beat one, then the "and" of two
    CHARLESTON = (
        NoteDivision.SIXTEENTH,
        16,
        ((0, 1.0), (6, 0.55)),
        "Charleston: beat 1 and the 'and' of 2",
    )
    # a stab on every beat, the downbeats strongest
    FOUR_ON_THE_FLOOR = (
        NoteDivision.SIXTEENTH,
        16,
        ((0, 1.0), (4, 0.7), (8, 0.85), (12, 0.7)),
        "Four on the floor: every beat",
    )
    # the "and" of every beat, the house offbeat
    OFFBEAT_HOUSE = (
        NoteDivision.SIXTEENTH,
        16,
        ((2, 0.9), (6, 0.8), (10, 0.9), (14, 0.8)),
        "Offbeat house: every 'and'",
    )
    # one chord a bar, left to ring
    WHOLE_BAR = (NoteDivision.SIXTEENTH, 16, ((0, 1.0),), "Whole bar: one hit a bar")
    # pushes ahead of beats two and four
    SYNCOPATED_PUSH = (
        NoteDivision.SIXTEENTH,
        16,
        ((0, 1.0), (5, 0.6), (8, 0.8), (11, 0.55)),
        "Syncopated push: ahead of the beat",
    )
    # one full-level hit per beat: the classic kick pulse
    QUARTER_PULSE = (
        NoteDivision.QUARTER,
        1,
        ((0, 1.0),),
        "Quarter pulse: a hit on every beat",
    )
    # one hit per half-beat: a steady ticking hat
    EIGHTH_PULSE = (
        NoteDivision.EIGHTH,
        1,
        ((0, 1.0),),
        "Eighth pulse: a hit on every half-beat",
    )
    # beats two and four, the backbeat a clap or snare accents
    BACKBEAT = (
        NoteDivision.SIXTEENTH,
        16,
        ((4, 1.0), (12, 1.0)),
        "Backbeat: beats 2 and 4",
    )
    # the backbeat with a quiet ghost note on the last 16th of the bar
    BACKBEAT_GHOST = (
        NoteDivision.SIXTEENTH,
        16,
        ((4, 1.0), (12, 1.0), (15, 0.3)),
        "Backbeat with a ghost: beats 2 and 4, a soft pickup",
    )
    # the last 16th of every beat, a tight woody rim-click figure
    RIM_OFFBEATS = (
        NoteDivision.SIXTEENTH,
        16,
        ((3, 1.0), (7, 1.0), (11, 1.0), (15, 1.0)),
        "Rim offbeats: the last 16th of every beat",
    )
    # a loose, syncopated conga figure
    CONGA_SYNCOPATED = (
        NoteDivision.SIXTEENTH,
        16,
        ((3, 1.0), (6, 1.0), (9, 1.0), (11, 1.0), (14, 1.0)),
        "Conga syncopation: five loose hits a bar",
    )
    # a quarter-note ride, the downbeat and beat three strongest
    RIDE_QUARTERS = (
        NoteDivision.SIXTEENTH,
        16,
        ((0, 1.0), (4, 0.8), (8, 0.9), (12, 0.8)),
        "Ride quarters: a hit on every beat",
    )
    # one crash at the start of an eight-bar phrase
    CRASH_PHRASE = (
        NoteDivision.SIXTEENTH,
        128,
        ((0, 1.0),),
        "Crash phrase: one hit every eight bars",
    )
    # hats: closed 16ths on the "and" of every beat
    HAT_CRISP = (
        NoteDivision.SIXTEENTH,
        16,
        ((2, 1.0), (6, 1.0), (10, 1.0), (14, 1.0)),
        "Crisp hats: closed on every 'and'",
    )
    # open offbeats choked by a closed ghost on the last 16th
    HAT_OPEN = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (2, 1.0, True),
            (6, 1.0, True),
            (10, 1.0, True),
            (14, 1.0, True),
            (15, 0.66),
        ),
        "Open hats: ringing offbeats choked on the last 16th",
    )
    # loosely shuffled, syncopated hats ending on an open hit
    HAT_SHUFFLE = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (2, 1.0),
            (5, 0.66),
            (6, 1.0),
            (10, 1.0),
            (13, 0.66),
            (14, 1.0, True),
        ),
        "Shuffle hats: syncopated, ending open",
    )
    # quiet open offbeats choked by softer closed ghosts, a background shimmer
    HAT_FOREST = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (2, 0.6, True),
            (3, 0.25),
            (6, 0.6, True),
            (7, 0.25),
            (10, 0.6, True),
            (11, 0.25),
            (14, 0.7, True),
            (15, 0.3),
        ),
        "Forest hats: quiet open offbeats choked by ghosts",
    )
    # 32nd-note steps (8 per beat). Each beat keeps its downbeat and "and"
    # on the grid but delays the weak "e"/"a" 16ths by one 32nd (to 3 and 7)
    # for an MPC-style swing, each a quiet ghost hit; the bar's last "a"
    # opens to breathe before the loop restarts
    HAT_LOFI = (
        NoteDivision.THIRTYSECOND,
        32,
        (
            (0, 1.0),
            (3, 0.4),
            (4, 0.75),
            (7, 0.4),
            (8, 0.85),
            (11, 0.4),
            (12, 0.75),
            (15, 0.4),
            (16, 1.0),
            (19, 0.4),
            (20, 0.75),
            (23, 0.4),
            (24, 0.85),
            (27, 0.4),
            (28, 0.55, True),
        ),
        "Lofi hats: swung 16ths with ghost notes",
    )
    # the lofi hats with the straight 16ths filled in as faint ghosts
    HAT_LOFI_FULL = (
        NoteDivision.THIRTYSECOND,
        32,
        (
            (0, 1.0),
            (2, 0.25),
            (3, 0.4),
            (4, 0.75),
            (6, 0.3),
            (7, 0.4),
            (8, 0.85),
            (10, 0.25),
            (11, 0.4),
            (12, 0.75),
            (14, 0.3),
            (15, 0.4),
            (16, 1.0),
            (18, 0.25),
            (19, 0.4),
            (20, 0.75),
            (22, 0.3),
            (23, 0.4),
            (24, 0.85),
            (26, 0.25),
            (27, 0.4),
            (28, 0.55, True),
        ),
        "Lofi hats, full: swung 16ths with every ghost filled in",
    )
    # 32nd-note steps. Beat one's downbeat is full; the syncopated "and" of
    # beat two lands on step 13 instead of the straight 12, one 32nd late (a
    # 5:3 swing ratio), and a quiet ghost flicks in a 32nd behind beat 4's
    # "a" - both just behind the grid for a laid-back boom-bap pocket
    KICK_LOFI = (
        NoteDivision.THIRTYSECOND,
        32,
        ((0, 1.0), (13, 0.85), (31, 0.3)),
        "Lofi kick: boom-bap with a swung 'and' and a ghost",
    )
    # the lofi kick with two softer fills
    KICK_LOFI_FULL = (
        NoteDivision.THIRTYSECOND,
        32,
        ((0, 1.0), (8, 0.45), (13, 0.85), (24, 0.55), (31, 0.3)),
        "Lofi kick, full: boom-bap with extra soft hits",
    )
    # 32nd-note steps. The backbeat on beats 2 and 4 (straight would be 8 and
    # 24) lands one 32nd late, at 9 and 25, for a behind-the-beat pocket; a
    # soft pickup ghost sits before beat 2 and a quieter one swings into the
    # loop before beat 1
    SNARE_LOFI = (
        NoteDivision.THIRTYSECOND,
        32,
        ((6, 0.25), (9, 1.0), (25, 1.0), (30, 0.3)),
        "Lofi snare: a late backbeat with ghost notes",
    )
    # one hit at the top of every bar: a whole-bar re-articulation
    BAR_PULSE = (
        NoteDivision.WHOLE,
        1,
        ((0, 1.0),),
        "Bar pulse: a hit at the top of every bar",
    )

    @property
    def hits(self) -> dict[int, float]:
        """Step -> velocity, the form `step_pattern` reads."""
        return {entry[0]: entry[1] for entry in self.value[2]}

    @property
    def open_steps(self) -> frozenset[int]:
        """The steps a hat plays open rather than closed."""
        return frozenset(entry[0] for entry in self.value[2] if len(entry) > 2)


class Melody(Pattern):
    """Note lines for any pitched gated patch, as `((step, semitones), ...)`,
    optionally `((step, semitones, accent, length), ...)`: `steps` maps a step
    to its semitone offset above the current chord root, an absent step is a
    rest, and `accents`/`lengths` give each step's level and hold time (1.0
    when an entry carries none).
    Members are only ever appended, so a saved dropdown index keeps meaning
    the same line."""

    # root up the major triad to the octave and back; step 6 rests so the
    # phrase has somewhere for its release tail to be heard
    LEAD_ARCH = (
        NoteDivision.EIGHTH,
        8,
        ((0, 0), (1, 4), (2, 7), (3, 12), (4, 7), (5, 4), (7, 0)),
        "Arch: root up the triad to the octave and back",
    )
    # a minor-pentatonic-ish phrase (root, minor 3rd, 5th, minor 7th) that
    # leaves space after each two- or three-note idea
    MUTED_KEYS = (
        NoteDivision.SIXTEENTH,
        16,
        ((0, 0), (3, 3), (6, 7), (8, 10), (11, 7), (13, 3)),
        "Muted motif: a sparse minor-pentatonic phrase",
    )
    # fifth, fifth, minor third, root: a two-bar fill walking down the minor
    # pentatonic, all four tones of the rack's minor-seventh chords
    TOM_FILL = (
        NoteDivision.SIXTEENTH,
        32,
        ((10, 7), (26, 7), (29, 3), (31, 0)),
        "Descending fill: fifth, fifth, third, root over two bars",
    )
    # sparse, floating long notes for a hollow reed
    WIND_DRIFT = (
        NoteDivision.SIXTEENTH,
        32,
        ((0, 7), (5, 8), (8, 7), (12, 5), (16, 3), (21, 5), (24, 7), (28, 1)),
        "Wind drift: sparse, floating long notes",
    )
    # the wind line turned over, starting from the octave
    WIND_DRIFT_B = (
        NoteDivision.SIXTEENTH,
        32,
        ((0, 12), (6, 10), (10, 8), (14, 7), (16, 5), (22, 3), (26, 1), (30, 0)),
        "Wind drift B: the same drift falling from the octave",
    )
    # a short, syncopated, sliding 16th-note groove
    SWIRL_GROOVE = (
        NoteDivision.SIXTEENTH,
        32,
        (
            (0, 7),
            (3, 7),
            (6, 8),
            (8, 7),
            (10, 5),
            (12, 3),
            (14, 5),
            (16, 7),
            (19, 10),
            (22, 8),
            (24, 7),
            (27, 5),
            (30, 1),
        ),
        "Swirl groove: syncopated 16ths sliding through the minor scale",
    )
    # the swirl groove answered by a falling line from the octave
    SWIRL_GROOVE_B = (
        NoteDivision.SIXTEENTH,
        32,
        (
            (0, 12),
            (2, 10),
            (3, 8),
            (6, 7),
            (8, 8),
            (11, 7),
            (14, 5),
            (16, 3),
            (18, 5),
            (19, 7),
            (22, 5),
            (24, 3),
            (27, 1),
            (28, 0),
            (30, 1),
        ),
        "Swirl groove B: the same groove falling from the octave",
    )
    # bass lines: 16th steps, each carrying its semitone offset and accent
    BASS_TECHNO = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (0, 0, 1.0),
            (1, 0, 0.6),
            (2, 0, 0.6),
            (3, 0, 0.6),
            (4, 0, 0.9),
            (5, 0, 0.6),
            (6, 12, 0.6),
            (7, 0, 0.6),
            (8, 0, 1.0),
            (9, 0, 0.6),
            (10, 7, 0.6),
            (11, 0, 0.6),
            (12, 0, 0.9),
            (13, 0, 0.6),
            (14, 0, 0.6),
            (15, 0, 0.7),
        ),
        "Techno bass: steady 16ths with an octave and a fifth leaning in",
    )
    BASS_ROLLING = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (0, 0, 1.0),
            (1, 0, 0.72),
            (2, 7, 0.72),
            (3, 0, 0.72),
            (4, 0, 1.0),
            (5, 12, 0.72),
            (6, 7, 0.72),
            (7, 0, 0.72),
            (8, 0, 1.0),
            (9, 0, 0.72),
            (10, 3, 0.72),
            (11, 7, 0.72),
            (12, 0, 1.0),
            (13, 10, 0.72),
            (14, 7, 0.72),
            (15, 0, 0.72),
        ),
        "Rolling bass: constant 16ths moving through fifth, octave and minor third",
    )
    BASS_DUB = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (0, 0, 1.0),
            (1, 0, 0.72),
            (2, 0, 0.72),
            (3, 7, 0.72),
            (4, 0, 1.0),
            (5, 0, 0.72),
            (6, 10, 0.72),
            (7, 0, 0.72),
            (8, 0, 1.0),
            (9, 7, 0.72),
            (10, 0, 0.72),
            (11, 0, 0.72),
            (12, 3, 1.0),
            (13, 0, 0.72),
            (14, 7, 0.72),
            (15, 0, 0.72),
        ),
        "Dub bass: sparser, fifth and minor seventh answering the root",
    )
    BASS_MUTED = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (0, 0, 1.0),
            (1, 0, 0.72),
            (2, 0, 0.72),
            (3, 0, 0.72),
            (4, 7, 1.0),
            (5, 0, 0.72),
            (6, 0, 0.72),
            (7, 0, 0.72),
            (8, 0, 1.0),
            (9, 0, 0.72),
            (10, 3, 0.72),
            (11, 0, 0.72),
            (12, 0, 1.0),
            (13, 7, 0.72),
            (14, 0, 0.72),
            (15, 10, 0.72),
        ),
        "Muted bass: short stabs, fifth, minor third and minor seventh",
    )
    BASS_MUTED_B = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (0, 0, 1.0),
            (1, 0, 0.72),
            (2, 7, 0.72),
            (3, 0, 0.72),
            (4, 0, 1.0),
            (5, 0, 0.72),
            (6, 10, 0.72),
            (7, 0, 0.72),
            (8, 0, 1.0),
            (9, 3, 0.72),
            (10, 0, 0.72),
            (11, 0, 0.72),
            (12, 7, 1.0),
            (13, 0, 0.72),
            (14, 0, 0.72),
            (15, 10, 0.72),
        ),
        "Muted bass B: the same stabs landing on different steps",
    )
    BASS_FOREST = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (1, 0, 0.8),
            (2, 0, 0.95),
            (3, 12, 0.7),
            (5, 0, 0.8),
            (6, 0, 0.95),
            (7, 12, 0.7),
            (9, 0, 0.8),
            (10, 0, 0.95),
            (11, 12, 0.7),
            (13, 0, 0.8),
            (14, 0, 0.95),
            (15, 1, 0.7),
        ),
        "Forest bass: rests on each beat, rolls the 16ths between kicks",
    )
    BASS_CONVERSATION = (
        NoteDivision.SIXTEENTH,
        64,
        (
            (0, 0, 0.75),
            (8, 0, 0.75),
            (16, 0, 0.75),
            (32, 0, 0.75),
            (40, 7, 0.75),
            (48, 0, 0.75),
            (61, 0, 0.9),
        ),
        "Conversation bass: sparse held notes over four bars",
    )
    BASS_CONVERSATION_B = (
        NoteDivision.SIXTEENTH,
        64,
        (
            (0, 0, 0.75),
            (8, 0, 0.75),
            (16, 0, 0.75),
            (32, 7, 0.75),
            (40, 7, 0.75),
            (45, 10, 0.9),
            (48, 0, 0.75),
            (56, 0, 0.75),
        ),
        "Conversation bass B: the third bar leans on the fifth",
    )
    BASS_HOVER = (
        NoteDivision.SIXTEENTH,
        64,
        (
            (0, 0, 0.95),
            (2, 0, 0.8),
            (4, 0, 0.8),
            (6, 0, 0.8),
            (8, 0, 0.8),
            (10, 0, 0.8),
            (12, 0, 0.8),
            (14, 0, 0.8),
            (16, 1, 0.95),
            (18, 1, 0.8),
            (20, 1, 0.8),
            (22, 1, 0.8),
            (24, 1, 0.8),
            (26, 1, 0.8),
            (28, 1, 0.8),
            (30, 1, 0.8),
            (32, 3, 0.95),
            (34, 3, 0.8),
            (36, 3, 0.8),
            (38, 3, 0.8),
            (40, 3, 0.8),
            (42, 3, 0.8),
            (44, 3, 0.8),
            (46, 3, 0.8),
            (48, 5, 0.95),
            (50, 5, 0.8),
            (52, 5, 0.8),
            (54, 5, 0.8),
            (56, 5, 0.8),
            (58, 5, 0.8),
            (60, 5, 0.8),
            (62, 5, 0.8),
        ),
        "Hover bass: steady eighths, stepping up a bar at a time",
    )

    # one funk bar of 16ths, each entry (step, semitones, accent, length in
    # 16ths): root on the One, held; octave pops; minor 7th, 5th and minor
    # 3rd fills; dead-note ghosts between them. Every pitch is a tone of the
    # rack's minor-seventh chords, and the minor 7th on the last 16th glides
    # down into the next bar's root
    BASS_FUNK = (
        NoteDivision.SIXTEENTH,
        16,
        (
            (0, 0, 1.0, 1.8),
            (3, 0, 0.55, 0.4),
            (4, 12, 0.9, 0.6),
            (6, 10, 0.75, 0.9),
            (7, 0, 0.55, 0.4),
            (9, 7, 0.8, 0.6),
            (10, 0, 0.55, 0.4),
            (11, 3, 0.8, 0.9),
            (13, 7, 0.7, 0.5),
            (14, 12, 0.9, 0.5),
            (15, 10, 0.6, 0.5),
        ),
        "Funk bass: a syncopated bar of held notes, pops and ghosts",
    )
    # a two-bar minor-pentatonic figure, one ring per phrase (for the bell,
    # measured from its Register rather than the chord root)
    BELL_FIGURE = (
        NoteDivision.SIXTEENTH,
        32,
        ((0, 12), (6, 7), (12, 10), (16, 3), (22, 5), (28, 0)),
        "Bell figure: a two-bar minor-pentatonic ring",
    )

    @property
    def steps(self) -> dict[int, int]:
        """Step -> semitones above the chord root, the form `step_pattern`
        reads."""
        return {entry[0]: entry[1] for entry in self.value[2]}

    @property
    def accents(self) -> dict[int, float]:
        """Step -> level, 1.0 for a step whose entry carries none."""
        return {
            entry[0]: entry[2] if len(entry) > 2 else 1.0 for entry in self.value[2]
        }

    @property
    def lengths(self) -> dict[int, float]:
        """Step -> how many steps the note is held, 1.0 for a step whose
        entry carries none."""
        return {
            entry[0]: entry[3] if len(entry) > 3 else 1.0 for entry in self.value[2]
        }


class ChordTones(Pattern):
    """Hook figures as `((step, tone), ...)`, where `tone` indexes the
    current chord's triad (0 root, 1 third, 2 fifth) instead of a fixed
    interval, so the figure takes the chord's own major or minor colour."""

    # a root, third, fifth, third climb that leaves the off-steps empty
    SPARSE_HOOK = (
        NoteDivision.EIGHTH,
        8,
        ((0, 0), (2, 1), (4, 2), (6, 1)),
        "Sparse hook: root, third, fifth, third",
    )
    # every eighth filled, the triad rocked back and forth
    FULL_HOOK = (
        NoteDivision.EIGHTH,
        8,
        ((0, 0), (1, 1), (2, 2), (3, 1), (4, 0), (5, 2), (6, 1), (7, 2)),
        "Full hook: the triad rocked through every eighth",
    )

    @property
    def steps(self) -> dict[int, int]:
        """Step -> chord-tone index, the form `step_pattern` reads."""
        return {entry[0]: entry[1] for entry in self.value[2]}
