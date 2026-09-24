"""Patch definitions for the clock-locked deep-house rack."""

from pyoscillate.harmony import A, Harmony
from pyoscillate.patches.drums.clap import clap
from pyoscillate.patches.drums.cymbal import cymbal
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.drums.percussion import percussion
from pyoscillate.patches.drums.snare import snare
from pyoscillate.patches.drums.tom import tom
from pyoscillate.patches.musical.chord import chord
from pyoscillate.patches.tonal.bass import groove as bass
from src.flet.base import PatchDef, PatchGroupDef

# this project's own tempo and clock timing resolution - other projects set
# their own values instead of sharing a static default from `pyoscillate.clock`
BPM = 132
TICKS_PER_BAR = 512
# the rack's shared key and progression: every `needs_harmony` patch (bass,
# chords, tom) re-roots on the same chord on the same bar. i-iv-bVII-v as
# parallel minor sevenths - the deep-house "chord memory" sound - one chord
# per bar, so the four-bar loop turns twice inside each eight-bar crash phrase
HARMONY = Harmony(key=A, progression=(0, 5, 10, 7), bars_per_chord=1)

PATCH_DEFS: list[PatchDef] = [
    PatchDef(
        "kick_round",
        "Kick - Round",
        "Deep, rounded low-end thump anchoring the groove.",
        kick.make_builder("round"),
        kick.PARAMETERS,
        kick.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "kick_punch",
        "Kick - Punch",
        "Tighter, punchier kick with more transient snap.",
        kick.make_builder("punch"),
        kick.PARAMETERS,
        kick.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "kick_soft",
        "Kick - Soft",
        "Soft, cushioned kick that sits back in the mix.",
        kick.make_builder("soft"),
        kick.PARAMETERS,
        kick.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "bass_rolling",
        "Bass - Rolling",
        "Constantly moving, rolling low-end groove.",
        bass.make_builder("rolling"),
        bass.PARAMETERS,
        bass.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
        needs_harmony=True,
    ),
    PatchDef(
        "bass_dub",
        "Bass - Dub",
        "Sparser, more resonant dub-style bass hits.",
        bass.make_builder("dub"),
        bass.PARAMETERS,
        bass.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
        needs_harmony=True,
    ),
    PatchDef(
        "bass_muted",
        "Bass - Muted",
        "Short, muted bass stabs that stay soft and out of the way.",
        bass.make_builder("muted"),
        bass.PARAMETERS,
        bass.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
        needs_harmony=True,
    ),
    PatchDef(
        "chord_velvet",
        "Chord Stab - Velvet",
        "Warm, rounded minor-seventh chord stabs.",
        chord.make_builder("velvet"),
        chord.PARAMETERS,
        chord.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
        needs_harmony=True,
    ),
    PatchDef(
        "chord_organ",
        "Chord Stab - Organ",
        "Sustained, organ-like harmonic bed.",
        chord.make_builder("organ"),
        chord.PARAMETERS,
        chord.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
        needs_harmony=True,
    ),
    PatchDef(
        "chord_shimmer",
        "Chord Stab - Shimmer",
        "Bright, shimmering chord stabs with more edge.",
        chord.make_builder("shimmer"),
        chord.PARAMETERS,
        chord.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
        needs_harmony=True,
    ),
    PatchDef(
        "hat_crisp",
        "Hat - Crisp",
        "Tight, crisp top-end pulse.",
        hat.make_builder("crisp"),
        hat.PARAMETERS,
        hat.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "hat_open",
        "Hat - Open",
        "Airier, more open top-end texture with longer tails.",
        hat.make_builder("open"),
        hat.PARAMETERS,
        hat.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "hat_shuffle",
        "Hat - Shuffle",
        "Loosely shuffled, syncopated top-end groove.",
        hat.make_builder("shuffle"),
        hat.PARAMETERS,
        hat.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "clap",
        "Clap",
        "Sharp, bright clap accent.",
        clap.build,
        clap.PARAMETERS,
        clap.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "percussion_rim",
        "Percussion - Rim",
        "Tight, woody rim-click accent.",
        percussion.make_builder("rim"),
        percussion.PARAMETERS,
        percussion.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "percussion_conga",
        "Percussion - Conga",
        "Warm, resonant conga-like rhythmic color.",
        percussion.make_builder("conga"),
        percussion.PARAMETERS,
        percussion.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "snare",
        "Snare",
        "Tone-and-rattle backbeat snare with a swung ghost note, layered under the clap.",
        snare.build,
        snare.PARAMETERS,
        snare.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "tom",
        "Tom",
        "Sparse two-bar tom fill on the current chord's minor pentatonic.",
        tom.build,
        tom.PARAMETERS,
        tom.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
        needs_harmony=True,
    ),
    PatchDef(
        "cymbal_ride",
        "Cymbal - Ride",
        "Quarter-note ride with slowly drifting metallic colour.",
        cymbal.make_builder("ride"),
        cymbal.PARAMETERS,
        cymbal.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "cymbal_crash",
        "Cymbal - Crash",
        "Long crash wash marking the start of every eight-bar phrase.",
        cymbal.make_builder("crash"),
        cymbal.PARAMETERS,
        cymbal.VOLUME_DEFAULT,
        needs_tempo=True,
        needs_clock=True,
    ),
]

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef("kicks", "Kicks", tuple(PATCH_DEFS[0:3])),
    PatchGroupDef("bass", "Bass", tuple(PATCH_DEFS[3:6])),
    PatchGroupDef("chords", "Chord Stabs", tuple(PATCH_DEFS[6:9])),
    PatchGroupDef("hats", "Hi-hats", tuple(PATCH_DEFS[9:12])),
    PatchGroupDef("percussion", "Percussion", tuple(PATCH_DEFS[13:15])),
    PatchGroupDef("claps", "Claps", (PATCH_DEFS[12],)),
    PatchGroupDef("drums", "Drums", tuple(PATCH_DEFS[15:19])),
]
