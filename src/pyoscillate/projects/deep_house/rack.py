"""Patch definitions for the clock-locked deep-house rack."""

from pyoscillate.controller import GroupController
from pyoscillate.harmony import A, Harmony
from pyoscillate.patches.base import SidechainSource
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
    needs_clock = True
    # the rack's shared key and progression: every `needs_harmony` patch (bass,
    # chords, tom) re-roots on the same chord on the same bar. i-iv-bVII-v as
    # parallel minor sevenths - the deep-house "chord memory" sound - one chord
    # per bar, so the four-bar loop turns twice inside each eight-bar crash phrase
    harmony = Harmony(key=A, progression=(0, 5, 10, 7), bars_per_chord=1)

    def build_groups(self) -> tuple[GroupController, ...]:
        return (
            GroupController(
                "kicks",
                "Kicks",
                (kick.KickRound(), kick.KickPunch(), kick.KickSoft()),
            ),
            GroupController(
                "bass",
                "Bass",
                (
                    # a kick ducking the bass on every hit is a standard deep-house
                    # sidechain move - see drums/kick/CLAUDE.md's "Sidechaining" reference.
                    # Ducks off the "kicks" group's currently active style, not a fixed
                    # instance, so switching kick styles doesn't silently un-wire the duck.
                    bass.BassRolling(
                        sidechain=SidechainSource("kicks", depth=0.6, release=0.15)
                    ),
                    bass.BassDub(),
                    bass.BassMuted(),
                ),
            ),
            GroupController(
                "chords",
                "Chord Stabs",
                (chord.ChordVelvet(), chord.ChordOrgan(), chord.ChordShimmer()),
            ),
            GroupController(
                "hats",
                "Hi-hats",
                (hat.GrooveCrisp(), hat.GrooveOpen(), hat.GrooveShuffle()),
            ),
            GroupController(
                "percussion",
                "Percussion",
                (percussion.PercussionRim(), percussion.PercussionConga()),
            ),
            GroupController("claps", "Claps", (clap.Clap(),)),
            GroupController(
                "drums",
                "Drums",
                (snare.Snare(), tom.Tom(), cymbal.CymbalRide(), cymbal.CymbalCrash()),
            ),
        )
