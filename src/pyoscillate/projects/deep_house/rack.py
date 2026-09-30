"""Patch definitions for the clock-locked deep-house rack."""

from pyoscillate.controller import GroupController, SidechainSource, Slot
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
from pyoscillate.projects.base import Rack


class DeepHouseRack(Rack):
    """The clock-locked deep-house rack."""

    # this project's own tempo and clock timing resolution - other projects set
    # their own values instead of sharing a static default from `pyoscillate.clock`
    bpm = 132
    ticks_per_bar = 512
    # the rack's shared key and progression: every harmonic patch (bass,
    # chords, tom) re-roots on the same chord on the same bar. i-iv-bVII-v as
    # parallel minor sevenths - the deep-house "chord memory" sound - one chord
    # per bar, so the four-bar loop turns twice inside each eight-bar crash phrase
    harmony = Harmony(key=A, progression=(0, 5, 10, 7), bars_per_chord=1)

    kicks_group = GroupController(
        "Kicks",
        (Slot(kick.KickRound), Slot(kick.KickPunch), Slot(kick.KickSoft)),
    )
    bass_group = GroupController(
        "Bass",
        (
            # a kick ducking the bass on every hit is a standard deep-house
            # sidechain move - see drums/kick/AGENTS.md's "Sidechaining" reference.
            # Ducks off the kicks group's playing style, not a fixed instance,
            # so switching kick styles doesn't silently un-wire the duck.
            Slot(
                bass.BassRolling,
                sidechains=(SidechainSource(kicks_group, depth=0.6, release=0.15),),
            ),
            Slot(bass.BassDub),
            Slot(bass.BassMuted),
        ),
    )
    chords_group = GroupController(
        "Chord Stabs",
        (Slot(chord.ChordVelvet), Slot(chord.ChordOrgan), Slot(chord.ChordShimmer)),
    )
    hats_group = GroupController(
        "Hi-hats",
        (Slot(hat.GrooveCrisp), Slot(hat.GrooveOpen), Slot(hat.GrooveShuffle)),
    )
    percussion_group = GroupController(
        "Percussion",
        (Slot(percussion.PercussionRim), Slot(percussion.PercussionConga)),
    )
    claps_group = GroupController("Claps", (Slot(clap.Clap),))
    drums_group = GroupController(
        "Drums",
        (
            Slot(snare.Snare),
            Slot(tom.Tom),
            Slot(cymbal.CymbalRide),
            Slot(cymbal.CymbalCrash),
        ),
    )
