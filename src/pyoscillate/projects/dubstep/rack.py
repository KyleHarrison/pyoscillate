# Run: uv run flet run src/flet/dubstep/app.py
"""Patch definitions for the clock-locked melodic-dubstep rack."""

from pyoscillate.controller import (
    FanOut,
    GroupControl,
    GroupController,
    ParamControl,
    SidechainSource,
    Slot,
)
from pyoscillate.harmony import Harmony
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.drums.snare import snare
from pyoscillate.patches.evolve import Evolve
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.tonal.bass.reese import reese
from pyoscillate.patches.tonal.keys import string_keys
from pyoscillate.patches.tonal.strings import strings
from pyoscillate.patches.tonal.vocal import singer, solo
from pyoscillate.patches.transition.riser import riser
from pyoscillate.projects.base import Rack
from pyoscillate.theory.phrase import BassLines, Leads
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.progression import Progressions
from pyoscillate.theory.scale import Scales


class DubstepRack(Rack):
    """Melodic, cinematic 140 BPM dubstep: a half-time kick and snare, a
    tempo-locked wobble bass that ducks off the kick, and an emotional
    minor-key topline of piano, strings and a sung line over a looping 8-bar
    chord cycle - see README.md for the brief behind each choice."""

    bpm = 140
    ticks_per_bar = 128
    # F natural minor, i-bVI-bIII-bVII at two bars a chord: the bass, piano,
    # strings and vocal all change chord on the same bar
    harmony = Harmony(key=Note.KEY_F, scale=Scales.MINOR)
    progression = Progressions.EPIC_MINOR

    # --- drums: the kick group comes first so the bass and chords can duck off it
    kick_punch = GroupControl(
        SliderSpec(
            "punch",
            0,
            1,
            0.05,
            0,
            "Punch",
            "Hits harder and adds drive to the kick.",
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
    kick_group = GroupController(
        "Kick",
        (Slot(kick.KickDubstep),),
        "Half-time pulse on beat 1; the bass and topline duck off it.",
        controls=(kick_punch,),
    )
    snare_tail = GroupControl(
        SliderSpec(
            "tail",
            0,
            1,
            0.05,
            0,
            "Tail",
            "Lets the snare ring longer, from a tight crack to a big room.",
        ),
        (FanOut((ParamControl(snare.Snare.decay, 0.3, 0.5),)),),
    )
    snare_group = GroupController(
        "Snare",
        (Slot(snare.SnareHalfTime),),
        "The one backbeat of the bar, on beat 3.",
        controls=(snare_tail,),
    )
    hats_group = GroupController(
        "Hats",
        (Slot(hat.GrooveHalfTime),),
        "Sparse offbeat ticks behind the pulse.",
    )
    drums_weight = GroupControl(
        SliderSpec(
            "weight",
            0,
            1,
            0.05,
            0,
            "Weight",
            "Hits the kick harder and lets the snare ring longer together.",
        ),
        (kick_punch, snare_tail),
    )
    drums_group = GroupController(
        "Drums",
        (kick_group, snare_group, hats_group),
        "Half-time kick, snare and hats.",
        controls=(drums_weight,),
    )

    # --- bass: duck off the kick group, so switching kick style keeps the pump
    bass_wobble = GroupControl(
        SliderSpec(
            "wobble",
            0,
            1,
            0.05,
            0,
            "Wobble",
            "Opens the wobble wider: from a gentle swell to a wide, vowel-like wub.",
        ),
        (FanOut((ParamControl(reese.Reese.depth, 1.0, 4.5),)),),
    )
    bass_growl = GroupControl(
        SliderSpec(
            "growl",
            0,
            1,
            0.05,
            0,
            "Growl",
            "Adds bite and distortion: from a smooth wobble to a snarling growl.",
        ),
        (
            FanOut(
                (
                    ParamControl(reese.Reese.growl, 0.1, 0.9),
                    ParamControl(reese.Reese.resonance, 0.25, 0.8),
                )
            ),
        ),
    )
    bass_brightness = GroupControl(
        SliderSpec(
            "brightness",
            0,
            1,
            0.05,
            0,
            "Brightness",
            "Raises the filter's resting point: from dark and closed to buzzy and forward.",
        ),
        (FanOut((ParamControl(reese.Reese.cutoff, 120, 600),)),),
    )
    bass_wobble_slot = Slot(
        reese.ReeseWobble,
        sidechains=(SidechainSource(kick_group, depth=0.5, release=0.15),),
        evolve=Evolve(8, (BassLines.BASS_DROP, BassLines.BASS_DROP_B)),
    )
    bass_heave_slot = Slot(
        reese.ReeseHeave,
        sidechains=(SidechainSource(kick_group, depth=0.5, release=0.15),),
    )
    bass_group = GroupController(
        "Bass",
        (bass_wobble_slot, bass_heave_slot),
        "Heavy low end that wobbles in time and re-roots on every chord.",
        controls=(bass_wobble, bass_growl, bass_brightness),
        alternatives=True,
    )

    # --- melody: the emotional layer over the chord cycle
    melody_air = GroupControl(
        SliderSpec(
            "air",
            0,
            1,
            0.05,
            0,
            "Air",
            "Opens the piano, strings and voice: from soft and distant to bright and close.",
        ),
        (
            FanOut(
                (
                    ParamControl(string_keys.Piano.brightness, 2500, 8000),
                    ParamControl(strings.Strings.brightness, 1200, 4500),
                    ParamControl(singer.FormantSinger.brightness, 2500, 7000),
                )
            ),
        ),
    )
    melody_group = GroupController(
        "Melody",
        (
            Slot(
                string_keys.Piano,
                root_freq=Note.F3,
                sidechains=(SidechainSource(kick_group, depth=0.3, release=0.2),),
            ),
            Slot(
                strings.Strings,
                root_freq=Note.F3,
                sidechains=(SidechainSource(kick_group, depth=0.35, release=0.2),),
            ),
            Slot(solo.VocalFemale, root_freq=Note.F4, phrase=Leads.ANTHEM),
        ),
        "Piano figure, string swell and a sung line over the chord cycle.",
        controls=(melody_air,),
    )

    # --- build: lands on the downbeat of every 8-bar phrase
    build_group = GroupController(
        "Build",
        (Slot(riser.RiserNoise), Slot(riser.RiserPitch)),
        "Risers that climb into the downbeat of every 8-bar phrase.",
    )
