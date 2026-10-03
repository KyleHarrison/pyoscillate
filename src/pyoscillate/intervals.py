"""Named semitone-interval lookups shared by every pitched patch.

Each enum member's `.value` is a tuple of semitones above a root, so a patch
names the musical idea (`Chord.MINOR_7`) instead of carrying a raw list.
Members must keep distinct values: Enum folds equal values into aliases.
"""

from __future__ import annotations

from enum import Enum


class Scale(Enum):
    """Scales as semitone offsets above the key, for `Harmony.scale` and for
    patches that draw a random scale tone."""

    MAJOR = (0, 2, 4, 5, 7, 9, 11)
    MINOR = (0, 2, 3, 5, 7, 8, 10)
    MAJOR_PENTATONIC = (0, 2, 4, 7, 9)
    MINOR_PENTATONIC = (0, 3, 5, 7, 10)
    # major pentatonic closed at the octave, for random-draw melodies
    MAJOR_PENTATONIC_OCTAVE = (0, 2, 4, 7, 9, 12)


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


class Voicing(Enum):
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

    @classmethod
    def by_index(cls, index: int) -> Voicing:
        """The shape numbered `index` in the Strudel library, clamped to its
        last entry as Strudel does."""
        shapes = list(cls.__members__.values())
        return shapes[max(0, min(index, len(shapes) - 1))]


class ArpOrder(Enum):
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

    @classmethod
    def by_index(cls, index: int) -> ArpOrder:
        """The order numbered `index`, clamped to the available range."""
        orders = list(cls)
        return orders[max(0, min(index, len(orders) - 1))]

    def intervals(self, pool: tuple[int, ...]) -> tuple[int, ...]:
        """This order's semitone offset at each step, drawn from `pool`."""
        return tuple(pool[index % len(pool)] for index in self.value)


class KeysProgression(Enum):
    """Four-bar electric-piano vamps for `Keys`, in the key of C.

    A member's value is `(roots, voicing_sets)`. `roots` are the chord roots
    as semitones above the key, one per bar: pass them as
    `Harmony(key=C, progression=KeysProgression.X.roots)` so the bass and
    chords follow the same changes, because `Keys` writes its voicings out by
    hand and never reads the rack's harmony. Each entry of `voicing_sets` is
    one full four-bar set of close, rootless four-note voicings, as semitones
    above `Keys`' Register (A): set 0 is the home voicing and set 1 lifts each
    chord's lowest note an octave, so `on_evolve` can change the inversion
    while the chords stay put. Voicings keep the top voices moving by step.
    """

    # Dm9 - G13 - Cmaj9 - Am9, the boom-bap rack's vamp
    II_V_I_VI = (
        (2, 7, 0, 9),
        (
            ((-4, 0, 3, 7), (-4, 0, 2, 7), (-5, -2, 2, 5), (3, 7, 10, 14)),
            ((0, 3, 7, 8), (0, 2, 7, 8), (-2, 2, 5, 7), (7, 10, 14, 15)),
        ),
    )
    # Cmaj9 - Am9 - Fmaj9 - G13
    I_VI_IV_V = (
        (0, 9, 5, 7),
        (
            ((-5, -2, 2, 5), (-5, -2, 2, 3), (-5, -2, 0, 3), (-5, -4, 0, 2)),
            ((-2, 2, 5, 7), (-2, 2, 3, 7), (-2, 0, 3, 7), (-4, 0, 2, 7)),
        ),
    )
    # Am9 - Fmaj9 - Cmaj9 - G13
    VI_IV_I_V = (
        (9, 5, 0, 7),
        (
            ((-2, 2, 3, 7), (-2, 0, 3, 7), (-2, 2, 5, 7), (0, 2, 7, 8)),
            ((2, 3, 7, 10), (0, 3, 7, 10), (2, 5, 7, 10), (2, 7, 8, 12)),
        ),
    )
    # Dm9 - G13 - Cmaj9 - Fmaj9
    II_V_I_IV = (
        (2, 7, 0, 5),
        (
            ((-4, 0, 3, 7), (-4, 0, 2, 7), (-5, -2, 2, 5), (-5, -2, 0, 3)),
            ((0, 3, 7, 8), (0, 2, 7, 8), (-2, 2, 5, 7), (-2, 0, 3, 7)),
        ),
    )
    # Cmaj9 - Em9 - Am9 - Dm9
    I_III_VI_II = (
        (0, 4, 9, 2),
        (
            ((-5, -2, 2, 5), (-3, -2, 2, 5), (-5, -2, 2, 3), (-5, -4, 0, 3)),
            ((-2, 2, 5, 7), (-2, 2, 5, 9), (-2, 2, 3, 7), (-4, 0, 3, 7)),
        ),
    )
    # Em9 - Am9 - Dm9 - G13
    III_VI_II_V = (
        (4, 9, 2, 7),
        (
            ((-3, -2, 2, 5), (-5, -2, 2, 3), (-5, -4, 0, 3), (-5, -4, 0, 2)),
            ((-2, 2, 5, 9), (-2, 2, 3, 7), (-4, 0, 3, 7), (-4, 0, 2, 7)),
        ),
    )

    @classmethod
    def by_index(cls, index: int) -> KeysProgression:
        """The vamp numbered `index`, clamped to the available range."""
        vamps = list(cls)
        return vamps[max(0, min(index, len(vamps) - 1))]

    @property
    def roots(self) -> tuple[int, ...]:
        """Chord roots, semitones above the key, one per bar."""
        return self.value[0]

    @property
    def voicing_sets(self) -> tuple[tuple[tuple[int, ...], ...], ...]:
        """Alternative four-bar voicing sets for these chords."""
        return self.value[1]
