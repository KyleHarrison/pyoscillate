"""Patch definitions for the clock-locked lofi beats-to-study-to rack."""

from pyoscillate.controller import EvolvingGroup, GroupController, SidechainSource, Slot
from pyoscillate.harmony import C, Harmony
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.drums.snare import snare
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.pitched_percussion.bell import bell
from pyoscillate.patches.texture.noise import noise
from pyoscillate.patches.tonal.bass import groove as bass
from pyoscillate.patches.tonal.keys import keys
from pyoscillate.patches.tonal.lead import lead
from pyoscillate.patches.tonal.strings import strings
from pyoscillate.patches.utility.notes import notes
from pyoscillate.projects.base import Macro, MacroControl, MacroTarget, Rack


class LofiRack(Rack):
    """The clock-locked lofi beats-to-study-to rack."""

    # this project's own tempo and clock timing resolution - other projects set
    # their own values instead of sharing a static default from `pyoscillate.clock`
    bpm = 80
    # matches deep_house's convention: fine enough for the swung 32nd-note
    # patterns (drums/kick, drums/snare, drums/hat's `lofi` styles) to land exactly
    ticks_per_bar = 512
    # the rack's shared key and vamp: Dm9-G13-Cmaj9-Am9, one chord per bar, four
    # bars per loop - a static, jazz-influenced ii9-V13-Imaj9-vi9 in the key of C
    # major (D=ii, G=V, C=I, A=vi), rather than a developing song form. Every
    # harmonic patch (bass, strings, lead) re-roots on this on the same
    # bar from the shared clock, so they change chord together regardless of
    # their own Rate sliders; `keys.Keys` isn't harmonic and instead
    # writes out the same progression by hand as fixed voicings (see keys.py)
    harmony = Harmony(key=C, progression=(2, 7, 0, 9), bars_per_chord=1)

    # the kick group is declared first so strings and bass can duck off it;
    # `layout` below sets the display order
    kick_lofi = Slot(kick.KickLofi)
    kick_group = GroupController("Kick", (kick_lofi,))

    lead_muted_keys = Slot(lead.LeadMutedKeys)
    lead_keys = Slot(keys.Keys)
    # a light, "invisible mix help" duck off the kick, not an audible EDM
    # pump - the lofi genre's own subtler take on the deep-house sidechain
    # move (see drums/kick/AGENTS.md's "Sidechaining" reference)
    pad_strings = Slot(
        strings.Strings,
        sidechains=(SidechainSource(kick_group, depth=0.15, release=0.25),),
    )
    bass_conversation = Slot(
        bass.BassConversation,
        sidechains=(SidechainSource(kick_group, depth=0.25, release=0.2),),
    )
    bass_muted = Slot(
        bass.BassMuted,
        sidechains=(SidechainSource(kick_group, depth=0.25, release=0.2),),
    )

    # lead melody: the rack's foreground - either the family's own sparse,
    # rest-heavy pentatonic motif (a "muted pluck") or the existing FM
    # electric piano's close-voiced comping, reused unmodified.
    # `bars=32` rotates which voicing set `keys.Keys` is comping, live-
    # adjustable from this group's own UI sliders (see flet/base.py's
    # `PatchGroup`) - see docs/todos/rack-linking-next.md
    lead_group = EvolvingGroup("Lead Melody", (lead_muted_keys, lead_keys), bars=32)
    # strings: soft, sustained harmonic accompaniment behind the lead.
    # `bars=16` rotates the colour voice between a 9th and a 13th
    # (see strings.py's `COLOUR_TONE_VARIANTS`)
    strings_group = EvolvingGroup("Strings", (pad_strings,), bars=16)
    # bass: sparse, thumpy, four-bar phrase with an occasional offbeat
    # re-entry (see tonal/bass/profiles.py's `_conversation`), or the
    # original one-bar muted groove. `bars=8` rotates each style's own
    # pattern variant (see profiles.py's `CONVERSATION_VARIANTS`/`MUTED_VARIANTS`)
    bass_group = EvolvingGroup("Bass", (bass_conversation, bass_muted), bars=8)
    # high register call-and-response: a soft FM bell, tuned high and
    # sparse. The rack has no cross-patch event bus for the bell to
    # literally listen for a bass hit and answer it, so this is an
    # approximation - a sparse, high, quiet voice on the shared clock
    # rather than one triggered by the bass's own triggers (see
    # lofi/README.md's "Concept-to-patch mapping")
    high_group = GroupController(
        "High Response",
        (Slot(bell.BellFm, root_freq=notes.A5, strike=0.3, ring=1.1, rate=-1),),
    )
    # atmosphere: continuous vinyl dust / tape crackle, felt more than heard
    noise_group = GroupController("Vinyl Dust", (Slot(noise.NoiseDust),))
    snare_group = GroupController("Snare", (Slot(snare.SnareLofi),))
    hat_group = GroupController("Hi-hat", (Slot(hat.GrooveLofi),))
    layout = (
        lead_group,
        strings_group,
        bass_group,
        high_group,
        noise_group,
        kick_group,
        snare_group,
        hat_group,
    )

    # a single rack-wide "Energy" slider - the manual counterpart to the
    # clock-triggered `on_evolve` rotations, see docs/todos/rack-linking-next.md.
    # Each control sweeps its style's own `Param` slider range, so the mapping
    # tracks a range if it's ever retuned.
    macros = (
        Macro(
            SliderSpec(
                "energy",
                0.0,
                1.0,
                0.05,
                0.5,
                "Energy",
                "Lifts brightness and drive together across bass, strings, and lead; low relaxes the whole "
                "rack, high pushes it brighter and more driven.",
            ),
            (
                MacroTarget(
                    bass_conversation, (MacroControl.sweep(bass.GrooveBass.cutoff),)
                ),
                MacroTarget(bass_muted, (MacroControl.sweep(bass.GrooveBass.cutoff),)),
                MacroTarget(
                    pad_strings,
                    (
                        MacroControl.sweep(strings.Strings.brightness),
                        MacroControl.sweep(strings.Strings.shimmer),
                    ),
                ),
                MacroTarget(
                    lead_muted_keys,
                    (
                        MacroControl.sweep(lead.Lead.brightness),
                        MacroControl.sweep(lead.Lead.drive),
                    ),
                ),
                MacroTarget(
                    lead_keys,
                    (
                        MacroControl.sweep(keys.Keys.bark),
                        MacroControl.sweep(keys.Keys.bite),
                    ),
                ),
            ),
        ),
    )
