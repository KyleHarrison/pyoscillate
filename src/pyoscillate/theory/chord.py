"""Chord shapes: stacks of intervals above a chord root."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pyoscillate.theory.catalog import Catalog, CatalogItem
from pyoscillate.theory.interval import Interval


class ChordUnit(Enum):
    """What a `Chord`'s offsets count."""

    # scale degrees above the root, resolved through a scale so the shape
    # takes that scale's major or minor colour
    DEGREES = "degrees"
    # fixed semitones above the root, the same in every scale
    SEMITONES = "semitones"


@dataclass(frozen=True, eq=False, kw_only=True)
class Chord(CatalogItem):
    """A chord shape, lowest voice first. With the default `DEGREES` unit
    `(0, 2, 4)` is a triad in whatever scale it is resolved against; resolve
    it with `Harmony.voice`. Ported from Switch Angel's strudel-scripts
    `chordshapes`."""

    offsets: tuple[int, ...]
    unit: ChordUnit = ChordUnit.DEGREES


class Chords(Catalog):
    """Every chord shape a patch can be set to, grouped by the idiom it
    comes from."""

    POWER_CHORD = Chord(offsets=(0, 4), category="Basic")
    TRIAD = Chord(offsets=(0, 2, 4), category="Basic")
    SPREAD_TRIAD = Chord(offsets=(-7, 0, 2, 4, 7), category="Spread")
    SPREAD_SUS4_TRIAD = Chord(offsets=(-7, 0, 2, 3, 7), category="Spread")
    SEVENTH_CHORD = Chord(offsets=(0, 2, 4, 6), category="Basic")
    MINOR_7TH_CLUSTER = Chord(offsets=(0, 2, 3, 6), category="Cluster")
    OPEN_TRIAD = Chord(offsets=(0, 4, 7, 9), category="Open")
    OPEN_SUSPENDED_TRIAD = Chord(offsets=(0, 4, 7, 8), category="Open")
    OPEN_7TH = Chord(offsets=(0, 4, 6, 9), category="Open")
    JAZZ_TENTH = Chord(offsets=(0, 2, 6, 9), category="Basic")
    ELEVENTH_CHORD = Chord(offsets=(0, 2, 6, 10), category="Basic")
    NINTH_CHORD = Chord(offsets=(0, 2, 4, 6, 8), category="Basic")
    WIDE_13TH = Chord(offsets=(-7, 0, 2, 6, 9), category="Spread")
    SIX_NINE_EXTENDED = Chord(offsets=(0, 4, 7, 9, 13), category="Basic")
    HIGH_TENSION_EXTENSION = Chord(offsets=(0, 4, 8, 9, 13), category="Basic")
    HIGH_CLUSTER_A = Chord(offsets=(0, 2, 7, 8, 11), category="Cluster")
    HIGH_CLUSTER_B = Chord(offsets=(0, 2, 8, 9, 11), category="Cluster")
    SUS2_STACK = Chord(offsets=(0, 3, 4), category="House")
    SUS4_STACK = Chord(offsets=(0, 1, 4), category="House")
    DENSE_TRIAD_CLUSTER = Chord(offsets=(0, 2, 3, 4), category="Cluster")
    ADD9_TRIAD = Chord(offsets=(0, 2, 4, 8), category="House")
    ADD9_6 = Chord(offsets=(0, 2, 4, 9), category="House")
    SOFT_MAJOR_9 = Chord(offsets=(0, 4, 6, 8), category="House")
    DREAMY_SPREAD = Chord(offsets=(0, 2, 5, 9), category="House")
    AMBIENT_OPEN_STACK = Chord(offsets=(0, 4, 7, 11), category="House")
    FIFTH_UPPER_CLUSTER = Chord(offsets=(0, 7, 9, 11), category="Cluster")
    WIDE_ADD9 = Chord(offsets=(0, 2, 7, 11), category="Spread")
    WIDE_POWER_CHORD = Chord(offsets=(-7, 0, 4, 7), category="Spread")
    BASS_7TH = Chord(offsets=(-7, 0, 4, 6), category="Spread")
    DEEP_HOUSE_VOICING = Chord(offsets=(-7, 0, 2, 9), category="House")
    FESTIVAL_HOUSE = Chord(offsets=(-7, 0, 4, 9), category="House")
    PROGRESSIVE_STACK = Chord(offsets=(-7, 0, 2, 4, 9), category="House")
    FULL_EXTENDED_HOUSE = Chord(offsets=(-7, 0, 2, 4, 6, 9), category="House")
    CINEMATIC_MINOR_FEEL = Chord(offsets=(-7, 0, 2, 4, 8), category="House")
    SUSPENDED_BASS_SPREAD = Chord(offsets=(-7, 0, 3, 7, 10), category="Spread")
    FUTURE_BASS_MAJOR = Chord(offsets=(0, 2, 4, 8, 11), category="Future bass")
    FUTURE_BASS_11TH = Chord(offsets=(0, 2, 4, 6, 11), category="Future bass")
    BRIGHT_EMOTIONAL_STACK = Chord(offsets=(0, 2, 4, 9, 11), category="Future bass")
    LUSH_EXTENDED = Chord(offsets=(0, 2, 6, 9, 11), category="Future bass")
    WIDE_EMOTIONAL_CLUSTER = Chord(offsets=(0, 4, 6, 8, 11), category="Cluster")
    HYBRID_CLUSTER = Chord(offsets=(0, 2, 3, 7, 11), category="Cluster")
    TENSION_PAD = Chord(offsets=(0, 1, 4, 8, 11), category="Future bass")
    MASSIVE_CLUSTER = Chord(offsets=(0, 1, 2, 4, 11), category="Cluster")
    ORGANIC_PAD_CHORD = Chord(offsets=(0, 2, 4, 5, 9), category="Future bass")
    SHIMMER_STACK = Chord(offsets=(0, 4, 5, 9, 11), category="Future bass")
    DARK_CLUSTER = Chord(offsets=(0, 1, 4, 7), category="Cluster")
    MINOR_CLUSTER = Chord(offsets=(0, 1, 3, 7), category="Cluster")
    TIGHT_OPEN_CHORD = Chord(offsets=(0, 4, 5, 7), category="Dark")
    QUARTAL_STACK = Chord(offsets=(0, 5, 7), category="Quartal")
    QUARTAL_7TH = Chord(offsets=(0, 5, 7, 10), category="Quartal")
    HOLLOW_FIFTH_STACK = Chord(offsets=(0, 5, 10), category="Dark")
    WIDE_QUARTAL = Chord(offsets=(-7, 0, 5, 7), category="Quartal")
    DARK_BASS_CLUSTER = Chord(offsets=(-7, 0, 1, 5), category="Cluster")
    INDUSTRIAL_SPREAD = Chord(offsets=(-7, -3, 0, 5), category="Dark")
    ACID_TENSION = Chord(offsets=(0, 1, 5, 8), category="Dark")
    SUSPENDED_DARK_CHORD = Chord(offsets=(0, 3, 5, 8), category="Dark")
    BIG_ROOM_ADD9 = Chord(offsets=(0, 2, 4, 7), category="Trance")
    EPIC_TRANCE_STACK = Chord(offsets=(0, 4, 7, 11, 14), category="Trance")
    HUGE_SPREAD_STACK = Chord(offsets=(-7, 0, 2, 4, 7, 11), category="Trance")
    FULL_ATMOSPHERIC = Chord(offsets=(0, 2, 4, 6, 9, 11), category="Trance")
    ANTHEM_LEAD_STACK = Chord(offsets=(0, 7, 11, 14), category="Trance")
    EMOTIONAL_SUPERSAW = Chord(offsets=(0, 2, 9, 11, 14), category="Trance")
    CINEMATIC_WIDE_CHORD = Chord(offsets=(-12, 0, 4, 7, 11), category="Trance")
    MASSIVE_OCTAVE_SPREAD = Chord(offsets=(-12, -7, 0, 4, 7), category="Trance")
    CHROMATIC_CLUSTER = Chord(offsets=(0, 1, 2), category="Cluster")
    DENSE_MODERN_CLUSTER = Chord(offsets=(0, 1, 2, 4), category="Cluster")
    FLOATING_AMBIENCE = Chord(offsets=(0, 2, 3, 5, 8), category="Experimental")
    UNRESOLVED_TEXTURE = Chord(offsets=(0, 4, 5, 8, 9), category="Experimental")
    QUARTAL_HYBRID = Chord(offsets=(0, 2, 5, 7, 11), category="Quartal")
    CINEMATIC_MINOR_9 = Chord(offsets=(0, 3, 7, 10, 14), category="Experimental")
    FULL_LYDIAN_STACK = Chord(offsets=(0, 2, 4, 7, 9, 11), category="Experimental")
    TENSION_WASH = Chord(offsets=(0, 1, 4, 6, 11), category="Experimental")
    POLY_CLUSTER = Chord(offsets=(0, 2, 6, 7, 11), category="Cluster")
    BRIGHT_MODERN_EXTENSION = Chord(offsets=(0, 4, 8, 11, 14), category="Experimental")
    # third, fifth, seventh and ninth with the root left to the bass: a close
    # four-note stack, minor 9th on a ii and major 9th on a I in a major key
    ROOTLESS_NINTH = Chord(offsets=(2, 4, 6, 8), category="Comping")
    # third, seventh, ninth and thirteenth: the fuller colour a dominant
    # chord takes in place of the plain ninth
    ROOTLESS_THIRTEENTH = Chord(offsets=(2, 6, 8, 12), category="Comping")

    # open fifth topped with the octave, a hollow bed that fits any mode
    OPEN_FIFTH = Chord(
        offsets=(Interval.UNISON, Interval.PERFECT_FIFTH, Interval.OCTAVE),
        unit=ChordUnit.SEMITONES,
        category="Open",
    )
