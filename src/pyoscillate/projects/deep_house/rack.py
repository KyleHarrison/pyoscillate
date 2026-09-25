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

PATCH_DEFS: dict[str, tuple[PatchDef, ...]] = {
    "kicks": (
        PatchDef(kick.KickRound()),
        PatchDef(kick.KickPunch()),
        PatchDef(kick.KickSoft()),
    ),
    "bass": (
        PatchDef(
            bass.BassRolling(),
            # a kick ducking the bass on every hit is a standard deep-house
            # sidechain move - see drums/kick/CLAUDE.md's "Sidechaining" reference
            sidechain=SidechainSource("kick_round", depth=0.6, release=0.15),
        ),
        PatchDef(bass.BassDub()),
        PatchDef(bass.BassMuted()),
    ),
    "chords": (
        PatchDef(chord.ChordVelvet()),
        PatchDef(chord.ChordOrgan()),
        PatchDef(chord.ChordShimmer()),
    ),
    "hats": (
        PatchDef(hat.GrooveCrisp()),
        PatchDef(hat.GrooveOpen()),
        PatchDef(hat.GrooveShuffle()),
    ),
    "percussion": (
        PatchDef(percussion.PercussionRim()),
        PatchDef(percussion.PercussionConga()),
    ),
    "claps": (PatchDef(clap.Clap()),),
    "drums": (
        PatchDef(snare.Snare()),
        PatchDef(tom.Tom()),
        PatchDef(cymbal.CymbalRide()),
        PatchDef(cymbal.CymbalCrash()),
    ),
}

GROUP_TITLES: dict[str, str] = {
    "kicks": "Kicks",
    "bass": "Bass",
    "chords": "Chord Stabs",
    "hats": "Hi-hats",
    "percussion": "Percussion",
    "claps": "Claps",
    "drums": "Drums",
}

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef(key, GROUP_TITLES[key], defs) for key, defs in PATCH_DEFS.items()
]
