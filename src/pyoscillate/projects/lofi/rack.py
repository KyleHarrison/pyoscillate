"""Patch definitions for the clock-locked lofi beats-to-study-to rack."""

from pyoscillate.controller import GroupController
from pyoscillate.harmony import C, Harmony
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.drums.snare import snare
from pyoscillate.patches.pitched_percussion.bell import bell
from pyoscillate.patches.texture.noise import noise
from pyoscillate.patches.tonal.bass import groove as bass
from pyoscillate.patches.tonal.keys import keys
from pyoscillate.patches.tonal.lead import lead
from pyoscillate.patches.tonal.strings import strings
from pyoscillate.patches.utility.notes import notes
from pyoscillate.projects.base import Rack
from src.flet.base import PatchGroupDef


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
    # rotates which voicing set `keys.Keys` is comping every 32 bars, so the
    # progression doesn't stay static forever (see
    # docs/todos/group-controller-evolution.md)
    group_controllers = (GroupController(groups=("lead",), bars=32),)

    def build_groups(self) -> tuple[PatchGroupDef, ...]:
        return (
            # lead melody: the rack's foreground - either the family's own sparse,
            # rest-heavy pentatonic motif (a "muted pluck") or the existing FM
            # electric piano's close-voiced comping, reused unmodified
            PatchGroupDef(
                "lead",
                "Lead Melody",
                (lead.LeadMutedKeys(), keys.Keys()),
            ),
            # strings: soft, sustained harmonic accompaniment behind the lead
            PatchGroupDef("strings", "Strings", (strings.Strings(),)),
            # bass: sparse, thumpy, four-bar phrase with an occasional offbeat
            # re-entry (see tonal/bass/profiles.py's `_conversation`), or the
            # original one-bar muted groove
            PatchGroupDef(
                "bass",
                "Bass",
                (bass.BassConversation(), bass.BassMuted()),
            ),
            # high register call-and-response: a soft FM bell, tuned high and
            # sparse. The rack has no cross-patch event bus for the bell to
            # literally listen for a bass hit and answer it, so this is an
            # approximation - a sparse, high, quiet voice on the shared clock
            # rather than one triggered by the bass's own triggers (see
            # lofi/README.md's "Concept-to-patch mapping")
            PatchGroupDef(
                "high",
                "High Response",
                (bell.BellFm(root_freq=notes.A5, strike=0.3, ring=1.1, rate=-1),),
            ),
            # atmosphere: continuous vinyl dust / tape crackle, felt more than heard
            PatchGroupDef("noise", "Vinyl Dust", (noise.NoiseDust(),)),
            PatchGroupDef("kick", "Kick", (kick.KickLofi(),)),
            PatchGroupDef("snare", "Snare", (snare.SnareLofi(),)),
            PatchGroupDef("hat", "Hi-hat", (hat.GrooveLofi(),)),
        )
