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
    PatchDef(kick.KickRound()),
    PatchDef(kick.KickPunch()),
    PatchDef(kick.KickSoft()),
    PatchDef(
        FunctionVoice.from_module(
            bass, style="rolling", volume_default=bass.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
        name="bass_rolling",
        title="Bass - Rolling",
        summary="Constantly moving, rolling low-end groove.",
        # a kick ducking the bass on every hit is a standard deep-house
        # sidechain move - see drums/kick/CLAUDE.md's "Sidechaining" reference
        sidechain=SidechainSource("kick_round", depth=0.6, release=0.15),
    ),
    PatchDef(
        FunctionVoice.from_module(
            bass, style="dub", volume_default=bass.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
        name="bass_dub",
        title="Bass - Dub",
        summary="Sparser, more resonant dub-style bass hits.",
    ),
    PatchDef(
        FunctionVoice.from_module(
            bass, style="muted", volume_default=bass.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
        name="bass_muted",
        title="Bass - Muted",
        summary="Short, muted bass stabs that stay soft and out of the way.",
    ),
    PatchDef(
        FunctionVoice.from_module(
            chord, style="velvet", volume_default=chord.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
        name="chord_velvet",
        title="Chord Stab - Velvet",
        summary="Warm, rounded minor-seventh chord stabs.",
    ),
    PatchDef(
        FunctionVoice.from_module(
            chord, style="organ", volume_default=chord.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
        name="chord_organ",
        title="Chord Stab - Organ",
        summary="Sustained, organ-like harmonic bed.",
    ),
    PatchDef(
        FunctionVoice.from_module(
            chord, style="shimmer", volume_default=chord.VOLUME_DEFAULT, **PITCHED_FLAGS
        ),
        name="chord_shimmer",
        title="Chord Stab - Shimmer",
        summary="Bright, shimmering chord stabs with more edge.",
    ),
    PatchDef(hat.GrooveCrisp()),
    PatchDef(hat.GrooveOpen()),
    PatchDef(hat.GrooveShuffle()),
    PatchDef(clap.Clap()),
    PatchDef(percussion.PercussionRim()),
    PatchDef(percussion.PercussionConga()),
    PatchDef(snare.Snare()),
    PatchDef(tom.Tom()),
    PatchDef(cymbal.CymbalRide()),
    PatchDef(cymbal.CymbalCrash()),
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
