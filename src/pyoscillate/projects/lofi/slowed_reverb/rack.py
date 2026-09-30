"""Patch definitions for the dark, slowed-and-reverbed lofi rack."""

from __future__ import annotations

from functools import partial

from pyoscillate.controller import GroupController
from pyoscillate.harmony import C, Harmony
from pyoscillate.patches.base import SidechainSource
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.texture.noise import noise
from pyoscillate.patches.tonal.bass import hover as bass
from pyoscillate.patches.tonal.drone import wash
from pyoscillate.patches.tonal.keys import keys
from pyoscillate.patches.tonal.pluck import pluck
from pyoscillate.patches.tonal.strings import strings
from pyoscillate.patches.utility.notes import notes
from pyoscillate.projects.base import (
    MacroControl,
    MacroSpec,
    MacroTarget,
    Rack,
)


class SlowedReverbRack(Rack):
    """Dark, slowed, bass-dominant lofi rack: a hovering sine-like bass
    under a long, breathing reverb tail, a dark reverberant pad wash, and a
    quiet, dusty texture bed - see README.md for the reference-track
    grounding behind this brief."""

    # felt tempo from the reference track's half-time drag (see README.md)
    bpm = 61
    needs_clock = True
    # The lofi strings follow this vamp; Keys encodes the same voicings.
    # Its white-note pitch collection also preserves the rack's E-Phrygian
    # colour, while E remains a common tone for the wash underneath it.
    harmony = Harmony(key=C, progression=(2, 7, 0, 9), bars_per_chord=1)
    # The bass hovers on E and the pad holds a static register; neither
    # follows the rack's chord progression (see README.md's shared-harmony note).
    ROOT_NOTE = notes.E1

    lead = GroupController(
        "lead",
        "Lead",
        (
            partial(strings.Strings, root_freq=174.61411571650194, brightness=3900, attack=2.15, release=2.9, spread=0.2, shimmer=0.8, colour=0.9, volume=0.7),
            partial(keys.Keys, root_freq=164.81377845643496, bark=5.0, bite=0.3, decay=3.1, tremolo=0.85, wobble=0.6, volume=1.5),
        ),
        "Choose strings or keys to give the wash harmony and pulse.",
        bars=8,
    )
    bass = GroupController(
        "bass",
        "Bass",
        (partial(bass.BassHover, root_freq=ROOT_NOTE, cutoff=770, reverb_size=0.85, reverb_damp=0.85, reverb_bal=0.85, breath=0.5, rate=-1, volume=1.6),),
    )
    pad = GroupController(
        "pad",
        "Pad",
        (partial(wash.SoundscapeWash, sidechain=SidechainSource("kick", depth=0.15, release=0.3), root_freq=notes.E2, detune=0.45, detune_bal=0.1, pitch_drift=0.8, chorus_depth=2.1, chorus_feedback=0.8, chorus_bal=0.75, reverb_size=0.25, reverb_damp=0.15, reverb_bal=0.75, delay_time=1.0, delay_feedback=0.7, volume=0.5),),
        bars=16,
    )
    hook = GroupController(
        "hook",
        "Hook",
        (partial(pluck.PluckHook, root_freq=notes.E3, rate=-1, volume=0.4),),
        bars=8,
    )
    texture = GroupController(
        "texture",
        "Texture",
        (partial(noise.NoiseDust, brightness=1200, colour=1.7, motion=0.3, depth=0.75, level=0.35, volume=0.3),),
    )
    kick = GroupController(
        "kick",
        "Kick",
        (partial(kick.KickLofi, level=0.4, drive=0.2, punch=0.8, length=0.8, click=0.5, rate=-1, volume=0.3),),
        bars=8,
    )
    hat = GroupController(
        "hat",
        "Hi-hat",
        (partial(hat.GrooveLofi, level=0.06, cutoff=3500, metal=0.1, length=0.75, rate=-1, volume=0.12),),
        bars=8,
    )
    macro = MacroSpec(
        SliderSpec(
            "lift",
            0,
            1,
            0.05,
            0,
            "Lift",
            "Gradually opens the chorus, upper hook and lead presence for a section arrival.",
        ),
        (
            MacroTarget(
                pad,
                (
                    MacroControl(
                        "chorus_depth", 2.1, wash.SoundscapeWash.chorus_depth.spec.maximum
                    ),
                    MacroControl("volume", 0.5, 0.65),
                ),
            ),
            MacroTarget(
                hook,
                (
                    MacroControl(
                        "brightness", 2.4, pluck.PluckHook.brightness.spec.maximum
                    ),
                    MacroControl("volume", 0.4, 0.55),
                ),
            ),
            MacroTarget(
                lead,
                (
                    MacroControl(
                        "brightness", 3900, strings.Strings.brightness.spec.maximum
                    ),
                    MacroControl(
                        "shimmer", 0.8, strings.Strings.shimmer.spec.maximum
                    ),
                    MacroControl("bark", 5.0, keys.Keys.bark.spec.maximum),
                    MacroControl("tremolo", 0.85, keys.Keys.tremolo.spec.maximum),
                ),
            ),
            MacroTarget(lead, (MacroControl("volume", 0.7, 0.9),), frozenset(("strings",))),
            MacroTarget(lead, (MacroControl("volume", 1.5, 1.7),), frozenset(("keys",))),
        ),
    )
