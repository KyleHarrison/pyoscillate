"""Patch definitions for the clock-locked lofi beats-to-study-to rack."""

from functools import partial

from pyoscillate.controller import GroupController
from pyoscillate.harmony import C, Harmony
from pyoscillate.patches.base import SidechainSource
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.drums.snare import snare
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.pitched_percussion.bell import bell
from pyoscillate.patches.texture.noise import noise
from pyoscillate.patches.tonal.bass import groove as bass_module
from pyoscillate.patches.tonal.keys import keys
from pyoscillate.patches.tonal.lead import lead as lead_module
from pyoscillate.patches.tonal.strings import strings as strings_module
from pyoscillate.patches.utility.notes import notes
from pyoscillate.projects.base import (
    MacroControl,
    MacroSpec,
    MacroTarget,
    Rack,
)


class LofiRack(Rack):
    """The clock-locked lofi beats-to-study-to rack."""

    # this project's own tempo and clock timing resolution - other projects set
    # their own values instead of sharing a static default from `pyoscillate.clock`
    bpm = 80
    # matches deep_house's convention: fine enough for the swung 32nd-note
    # patterns (drums/kick, drums/snare, drums/hat's `lofi` styles) to land exactly
    ticks_per_bar = 512
    needs_clock = True
    # the rack's shared key and vamp: Dm9-G13-Cmaj9-Am9, one chord per bar, four
    # bars per loop - a static, jazz-influenced ii9-V13-Imaj9-vi9 in the key of C
    # major (D=ii, G=V, C=I, A=vi), rather than a developing song form. Every
    # `needs_harmony` patch (bass, strings, lead) re-roots on this on the same
    # bar from the shared clock, so they change chord together regardless of
    # their own Rate sliders; `keys.Keys` isn't `needs_harmony` and instead
    # writes out the same progression by hand as fixed voicings (see keys.py)
    harmony = Harmony(key=C, progression=(2, 7, 0, 9), bars_per_chord=1)
    lead = GroupController(
        "lead",
        "Lead Melody",
        (lead_module.LeadMutedKeys, keys.Keys),
        bars=32,
    )
    strings = GroupController(
        "strings",
        "Strings",
        (partial(strings_module.Strings, sidechain=SidechainSource("kick", depth=0.15, release=0.25)),),
        bars=16,
    )
    bass = GroupController(
        "bass",
        "Bass",
        (
            partial(bass_module.BassConversation, sidechain=SidechainSource("kick", depth=0.25, release=0.2)),
            partial(bass_module.BassMuted, sidechain=SidechainSource("kick", depth=0.25, release=0.2)),
        ),
        bars=8,
    )
    high = GroupController(
        "high",
        "High Response",
        (partial(bell.BellFm, root_freq=notes.A5, strike=0.3, ring=1.1, rate=-1),),
    )
    noise = GroupController("noise", "Vinyl Dust", (noise.NoiseDust,))
    kick = GroupController("kick", "Kick", (kick.KickLofi,))
    snare = GroupController("snare", "Snare", (snare.SnareLofi,))
    hat = GroupController("hat", "Hi-hat", (hat.GrooveLofi,))

    macro = MacroSpec(
        SliderSpec(
            "energy", 0.0, 1.0, 0.05, 0.5, "Energy",
            "Lifts brightness and drive together across bass, strings, and lead; low relaxes the whole rack, high pushes it brighter and more driven.",
        ),
        (
            MacroTarget(
                bass,
                (MacroControl(
                    "cutoff",
                    bass_module.GrooveBass.cutoff.spec.minimum,
                    bass_module.GrooveBass.cutoff.spec.maximum,
                ),),
            ),
            MacroTarget(
                strings,
                (
                    MacroControl(
                        "brightness",
                        strings_module.Strings.brightness.spec.minimum,
                        strings_module.Strings.brightness.spec.maximum,
                    ),
                    MacroControl(
                        "shimmer",
                        strings_module.Strings.shimmer.spec.minimum,
                        strings_module.Strings.shimmer.spec.maximum,
                    ),
                ),
            ),
            MacroTarget(
                lead,
                (
                    MacroControl(
                        "brightness",
                        lead_module.Lead.brightness.spec.minimum,
                        lead_module.Lead.brightness.spec.maximum,
                    ),
                    MacroControl(
                        "drive",
                        lead_module.Lead.drive.spec.minimum,
                        lead_module.Lead.drive.spec.maximum,
                    ),
                    MacroControl("bark", keys.Keys.bark.spec.minimum, keys.Keys.bark.spec.maximum),
                    MacroControl("bite", keys.Keys.bite.spec.minimum, keys.Keys.bite.spec.maximum),
                ),
            ),
        ),
    )
