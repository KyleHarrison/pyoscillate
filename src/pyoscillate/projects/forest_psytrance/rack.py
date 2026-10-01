"""Patch definitions for the clock-locked forest-psytrance rack."""

from pyoscillate.controller import (
    EvolvingGroup,
    GroupControl,
    GroupController,
    ParamControl,
    SidechainSource,
    Slot,
    SlotTarget,
)
from pyoscillate.harmony import F, Harmony
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.tonal.bass import groove as bass
from pyoscillate.patches.tonal.lead import fm
from pyoscillate.patches.utility.notes import notes
from pyoscillate.projects.base import Rack


class ForestPsytranceRack(Rack):
    """Dark, hypnotic 160 BPM rack: a deep rolling bass in the gaps between
    four-on-the-floor kicks, subtle offbeat hats, and windy, psychedelic FM
    leads - see README.md for the brief behind each choice."""

    bpm = 160
    ticks_per_bar = 512
    # F Phrygian: a static F vamp that leans on the b2 (Gb) for the last two
    # bars of every eight-bar cycle
    harmony = Harmony(key=F, progression=(0, 0, 0, 1), bars_per_chord=2)

    kick_punch = Slot(kick.KickPunch, punch=0.9, length=0.8, click=0.6)
    kick_group = GroupController(
        "Kick",
        (kick_punch,),
        "Four-on-the-floor pulse the bass rolls around.",
    )

    bass_forest = Slot(
        bass.BassForest,
        sidechains=(SidechainSource(kick_group, depth=0.5, release=0.1),),
        cutoff=420,
    )
    bass_roll = GroupControl(
        SliderSpec(
            "roll",
            0,
            1,
            0.05,
            0,
            "Roll",
            "Opens the bass filter for a brighter, more forward roll.",
        ),
        (SlotTarget(bass_forest, (ParamControl(bass.GrooveBass.cutoff, 420, 900),)),),
    )
    bass_group = GroupController(
        "Bass",
        (bass_forest,),
        "Deep, rolling offbeat low end between the kicks.",
        controls=(bass_roll,),
    )

    hat_forest = Slot(hat.GrooveForest, volume=0.8)
    hat_group = GroupController(
        "Hi-hats",
        (hat_forest,),
        "Quiet offbeat shimmer behind the groove.",
    )

    lead_wind = Slot(
        fm.LeadFmWind,
        root_freq=notes.F4,
    )
    lead_swirl = Slot(
        fm.LeadFmSwirl,
        root_freq=notes.F4,
    )
    lead_group = EvolvingGroup(
        "Leads",
        (lead_wind, lead_swirl),
        "Windy, psychedelic FM melodies; the phrase changes every 8 bars.",
        bars=8,
    )
    layout = (kick_group, bass_group, hat_group, lead_group)
