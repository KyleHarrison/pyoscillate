# Run: uv run flet run src/flet/deep_house/app.py
"""Patch definitions for the clock-locked deep-house rack."""

from pyoscillate.controller import (
    FanOut,
    GroupControl,
    GroupController,
    ParamControl,
    SidechainSource,
    Slot,
)
from pyoscillate.harmony import Harmony
from pyoscillate.patches.common import PitchBend
from pyoscillate.patches.drums.clap import clap
from pyoscillate.patches.drums.cymbal import cymbal
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.drums.percussion import percussion
from pyoscillate.patches.drums.snare import snare
from pyoscillate.patches.drums.tom import tom
from pyoscillate.patches.musical.stab import stab
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.tonal.bass import groove as bass
from pyoscillate.projects.base import Rack
from pyoscillate.theory.pitch import Note


class DeepHouseRack(Rack):
    """Warm, rolling 132 BPM deep house: a four-on-the-floor kick the bass
    and the chord stabs duck off, offbeat minor-seventh chord memory, shuffled
    hats and accent percussion. Each role offers alternative styles; the
    Rhythm and Harmony sections each carry one slider that moves their parts
    together."""

    # this project's own tempo and clock timing resolution - other projects set
    # their own values instead of sharing a static default from `pyoscillate.clock`
    bpm = 132
    ticks_per_bar = 512
    # the rack's shared key and progression: every harmonic patch (bass,
    # chords, tom) re-roots on the same chord on the same bar. i-iv-bVII-v as
    # parallel minor sevenths - the deep-house "chord memory" sound - one chord
    # per bar, so the four-bar loop turns twice inside each eight-bar crash phrase
    harmony = Harmony(key=Note.KEY_A, progression=(0, 5, 10, 7), bars_per_chord=1)

    # --- rhythm: the kick group comes first so the harmonic layers can duck off it
    kick_punch = GroupControl(
        SliderSpec(
            "punch",
            0,
            1,
            0.05,
            0,
            "Punch",
            "Hits harder and adds drive to whichever kick is playing.",
        ),
        (
            FanOut(
                (
                    ParamControl(kick.Kick.punch, 1.0, 1.6),
                    ParamControl(kick.Kick.drive, 0.12, 0.4),
                )
            ),
        ),
    )
    kicks_group = GroupController(
        "Kicks",
        (Slot(kick.KickRound), Slot(kick.KickPunch), Slot(kick.KickSoft)),
        "Four-on-the-floor pulse; the bass and chords duck off it.",
        controls=(kick_punch,),
        alternatives=True,
    )
    hat_air = GroupControl(
        SliderSpec(
            "air",
            0,
            1,
            0.05,
            0,
            "Air",
            "Opens the hats: brighter and longer.",
        ),
        (
            FanOut(
                (
                    ParamControl(hat.Groove.cutoff, 9000, 14000),
                    ParamControl(hat.Groove.length, 1.0, 1.6),
                )
            ),
        ),
    )
    hats_group = GroupController(
        "Hi-hats",
        (Slot(hat.GrooveCrisp), Slot(hat.GrooveOpen), Slot(hat.GrooveShuffle)),
        "Offbeat and shuffled top-end motion.",
        controls=(hat_air,),
        alternatives=True,
    )
    percussion_group = GroupController(
        "Percussion",
        (Slot(percussion.PercussionRim), Slot(percussion.PercussionConga)),
        "Accent percussion around the groove.",
        alternatives=True,
    )
    claps_group = GroupController("Claps", (Slot(clap.Clap),), "Backbeat clap.")
    drums_group = GroupController(
        "Drums",
        (
            Slot(snare.Snare),
            Slot(tom.Tom),
            Slot(cymbal.CymbalRide),
            Slot(cymbal.CymbalCrash),
        ),
        "Snare, fill tom and cymbals.",
    )
    rhythm_drive = GroupControl(
        SliderSpec(
            "drive",
            0,
            1,
            0.05,
            0,
            "Drive",
            "Pushes the kick harder and opens the hats together.",
        ),
        (kick_punch, hat_air),
    )
    rhythm_group = GroupController(
        "Rhythm",
        (kicks_group, claps_group, hats_group, percussion_group, drums_group),
        "Kick, clap, hats, percussion and drums.",
        controls=(rhythm_drive,),
    )

    # --- harmony: both follow the shared progression and duck off the kicks.
    # The duck targets the kicks *group*, not a fixed kick, so switching kick
    # styles doesn't silently un-wire it (see drums/kick/AGENTS.md's
    # "Sidechaining" reference).
    bass_filter = GroupControl(
        SliderSpec(
            "filter",
            0,
            1,
            0.05,
            0,
            "Filter",
            "Opens the bass filter for a brighter, more forward line.",
        ),
        (FanOut((ParamControl(bass.GrooveBass.cutoff, 720, 1800),)),),
    )
    bass_slide = GroupControl(
        SliderSpec(
            "slide",
            0,
            1,
            0.05,
            0,
            "Slide",
            "Smears each bass note into the next and scoops it up from below; low is stepped and clean, high is a sliding line.",
        ),
        (
            FanOut(
                (
                    ParamControl(bass.GrooveBass.glide, 0, 0.08),
                    ParamControl(PitchBend.bend, 0, -3),
                )
            ),
        ),
    )
    bass_accent = GroupControl(
        SliderSpec(
            "accent",
            0,
            1,
            0.05,
            0,
            "Accent",
            "Makes the strong notes speak: louder, shorter and more squelchy against the soft ones.",
        ),
        (FanOut((ParamControl.sweep(bass.GrooveBass.accent),)),),
    )
    bass_group = GroupController(
        "Bass",
        (
            Slot(
                bass.BassRolling,
                sidechains=(SidechainSource(kicks_group, depth=0.6, release=0.15),),
            ),
            Slot(
                bass.BassDub,
                sidechains=(SidechainSource(kicks_group, depth=0.6, release=0.15),),
            ),
            Slot(
                bass.BassMuted,
                sidechains=(SidechainSource(kicks_group, depth=0.6, release=0.15),),
            ),
        ),
        "Moving low end that re-roots on every chord.",
        controls=(bass_filter, bass_slide, bass_accent),
        alternatives=True,
    )
    chord_brightness = GroupControl(
        SliderSpec(
            "brightness",
            0,
            1,
            0.05,
            0,
            "Brightness",
            "Opens the stabs' filter from velvety to bright.",
        ),
        (FanOut((ParamControl(stab.Stab.brightness, 1500, 5000),)),),
    )
    chord_feel = GroupControl(
        SliderSpec(
            "feel",
            0,
            1,
            0.05,
            0,
            "Feel",
            "Loosens the stabs from a rigid block into a rolled, played-by-hand chord.",
        ),
        (
            FanOut(
                (
                    ParamControl(stab.Stab.strum, 0, 0.4),
                    ParamControl(stab.Stab.feel, 0, 0.5),
                )
            ),
        ),
    )
    chords_group = GroupController(
        "Chord Stabs",
        (
            Slot(
                stab.StabVelvet,
                sidechains=(SidechainSource(kicks_group, depth=0.3, release=0.2),),
            ),
            Slot(
                stab.StabOrgan,
                sidechains=(SidechainSource(kicks_group, depth=0.3, release=0.2),),
            ),
            Slot(
                stab.StabShimmer,
                sidechains=(SidechainSource(kicks_group, depth=0.3, release=0.2),),
            ),
        ),
        "Offbeat minor-seventh chord memory.",
        controls=(chord_brightness, chord_feel),
        alternatives=True,
    )
    harmony_warmth = GroupControl(
        SliderSpec(
            "brightness",
            0,
            1,
            0.05,
            0,
            "Brightness",
            "Opens the bass and chord filters together.",
        ),
        (bass_filter, chord_brightness),
    )
    harmony_group = GroupController(
        "Harmony",
        (bass_group, chords_group),
        "Bass and chords, following the shared key and progression.",
        controls=(harmony_warmth,),
    )
