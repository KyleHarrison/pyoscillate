"""Patch definitions for the clock-locked deep-house rack."""

from pyoscillate.harmony import A, Harmony
from pyoscillate.patches.base import FunctionVoice
from pyoscillate.patches.drums.clap import clap
from pyoscillate.patches.drums.cymbal import cymbal
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.drums.percussion import percussion
from pyoscillate.patches.drums.snare import snare
from pyoscillate.patches.drums.tom import tom
from pyoscillate.patches.musical.chord import chord
from pyoscillate.patches.tonal.bass import groove as bass
from src.flet.base import PatchDef, PatchGroupDef, SidechainSource

# this project's own tempo and clock timing resolution - other projects set
# their own values instead of sharing a static default from `pyoscillate.clock`
BPM = 132
TICKS_PER_BAR = 512
# the rack's shared key and progression: every `needs_harmony` patch (bass,
# chords, tom) re-roots on the same chord on the same bar. i-iv-bVII-v as
# parallel minor sevenths - the deep-house "chord memory" sound - one chord
# per bar, so the four-bar loop turns twice inside each eight-bar crash phrase
HARMONY = Harmony(key=A, progression=(0, 5, 10, 7), bars_per_chord=1)

PITCHED_FLAGS = {"needs_tempo": True, "needs_clock": True, "needs_harmony": True}

PATCH_DEFS: list[PatchDef] = [
    PatchDef(
        "kick_round",
        "Kick - Round",
        "Deep, rounded low-end thump anchoring the groove.",
        kick.KickRound(),
    ),
    PatchDef(
        "kick_punch",
        "Kick - Punch",
        "Tighter, punchier kick with more transient snap.",
        kick.KickPunch(),
    ),
    PatchDef(
        "kick_soft",
        "Kick - Soft",
        "Soft, cushioned kick that sits back in the mix.",
        kick.KickSoft(),
    ),
    PatchDef(
        "bass_rolling",
        "Bass - Rolling",
        "Constantly moving, rolling low-end groove.",
        FunctionVoice.from_module(
            bass, style="rolling", volume_default=bass.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
        # a kick ducking the bass on every hit is a standard deep-house
        # sidechain move - see drums/kick/CLAUDE.md's "Sidechaining" reference
        sidechain=SidechainSource("kick_round", depth=0.6, release=0.15),
    ),
    PatchDef(
        "bass_dub",
        "Bass - Dub",
        "Sparser, more resonant dub-style bass hits.",
        FunctionVoice.from_module(
            bass, style="dub", volume_default=bass.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
    ),
    PatchDef(
        "bass_muted",
        "Bass - Muted",
        "Short, muted bass stabs that stay soft and out of the way.",
        FunctionVoice.from_module(
            bass, style="muted", volume_default=bass.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
    ),
    PatchDef(
        "chord_velvet",
        "Chord Stab - Velvet",
        "Warm, rounded minor-seventh chord stabs.",
        FunctionVoice.from_module(
            chord, style="velvet", volume_default=chord.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
    ),
    PatchDef(
        "chord_organ",
        "Chord Stab - Organ",
        "Sustained, organ-like harmonic bed.",
        FunctionVoice.from_module(
            chord, style="organ", volume_default=chord.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
    ),
    PatchDef(
        "chord_shimmer",
        "Chord Stab - Shimmer",
        "Bright, shimmering chord stabs with more edge.",
        FunctionVoice.from_module(
            chord, style="shimmer", volume_default=chord.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
    ),
    PatchDef(
        "hat_crisp",
        "Hat - Crisp",
        "Tight, crisp top-end pulse.",
        hat.GrooveCrisp(),
    ),
    PatchDef(
        "hat_open",
        "Hat - Open",
        "Airier, more open top-end texture with longer tails.",
        hat.GrooveOpen(),
    ),
    PatchDef(
        "hat_shuffle",
        "Hat - Shuffle",
        "Loosely shuffled, syncopated top-end groove.",
        hat.GrooveShuffle(),
    ),
    PatchDef(
        "clap",
        "Clap",
        "Sharp, bright clap accent.",
        clap.Clap(),
    ),
    PatchDef(
        "percussion_rim",
        "Percussion - Rim",
        "Tight, woody rim-click accent.",
        percussion.PercussionRim(),
    ),
    PatchDef(
        "percussion_conga",
        "Percussion - Conga",
        "Warm, resonant conga-like rhythmic color.",
        percussion.PercussionConga(),
    ),
    PatchDef(
        "snare",
        "Snare",
        "Tone-and-rattle backbeat snare with a swung ghost note, layered under the clap.",
        snare.Snare(),
    ),
    PatchDef(
        "tom",
        "Tom",
        "Sparse two-bar tom fill on the current chord's minor pentatonic.",
        tom.Tom(),
    ),
    PatchDef(
        "cymbal_ride",
        "Cymbal - Ride",
        "Quarter-note ride with slowly drifting metallic colour.",
        cymbal.CymbalRide(),
    ),
    PatchDef(
        "cymbal_crash",
        "Cymbal - Crash",
        "Long crash wash marking the start of every eight-bar phrase.",
        cymbal.CymbalCrash(),
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
