"""Patch definitions for the clock-locked lofi beats-to-study-to rack."""

from pyoscillate.controller import EvolvingGroup, GroupController
from pyoscillate.harmony import C, Harmony
from pyoscillate.patches.base import SidechainSource
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
from pyoscillate.projects.base import Macro, Rack


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
    lead_muted_keys: lead.LeadMutedKeys
    lead_keys: keys.Keys
    pad_strings: strings.Strings
    bass_conversation: bass.BassConversation
    bass_muted: bass.BassMuted
    kick: GroupController

    @staticmethod
    def _lerp(spec: SliderSpec, value: float) -> float:
        return spec.minimum + value * (spec.maximum - spec.minimum)

    def _apply_energy(self, value: float) -> None:
        """The lofi rack's one macro: a single 0-1 "Energy" push that lifts (or
        relaxes) brightness and drive together across bass, strings, and lead -
        same "push a value into the patches" shape as `on_evolve`, just
        user-triggered from a slider instead of the clock. Reuses each
        style's own `Param` slider range (rather than restating min/max here) so
        the mapping tracks a range if it's ever retuned. Both bass styles have
        `cutoff`; the lead group's two styles have `brightness`/`drive`
        (`lead.Lead`) or `bark`/`bite` (`keys.Keys`), assigned separately."""
        cutoff = self._lerp(bass.GrooveBass.cutoff.spec, value)
        self.bass_conversation.cutoff = cutoff
        self.bass_muted.cutoff = cutoff

        self.pad_strings.brightness = self._lerp(strings.Strings.brightness.spec, value)
        self.pad_strings.shimmer = self._lerp(strings.Strings.shimmer.spec, value)

        self.lead_muted_keys.brightness = self._lerp(lead.Lead.brightness.spec, value)
        self.lead_muted_keys.drive = self._lerp(lead.Lead.drive.spec, value)
        self.lead_keys.bark = self._lerp(keys.Keys.bark.spec, value)
        self.lead_keys.bite = self._lerp(keys.Keys.bite.spec, value)

    # a single rack-wide "Energy" slider - the manual counterpart to task 1's
    # clock-triggered `on_evolve` rotations, see docs/todos/rack-linking-next.md
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
            _apply_energy,
        ),
    )

    def build_groups(self) -> tuple[GroupController, ...]:
        # the kick is built first so strings and bass can duck off it; the groups
        # are returned in display order below
        self.kick = GroupController("Kick", (kick.KickLofi(),))
        self.lead_muted_keys = lead.LeadMutedKeys()
        self.lead_keys = keys.Keys()
        self.pad_strings = strings.Strings(
            sidechains=(SidechainSource(self.kick, depth=0.15, release=0.25),)
        )
        self.bass_conversation = bass.BassConversation(
            sidechains=(SidechainSource(self.kick, depth=0.25, release=0.2),)
        )
        self.bass_muted = bass.BassMuted(
            sidechains=(SidechainSource(self.kick, depth=0.25, release=0.2),)
        )
        return (
            # lead melody: the rack's foreground - either the family's own sparse,
            # rest-heavy pentatonic motif (a "muted pluck") or the existing FM
            # electric piano's close-voiced comping, reused unmodified.
            # `bars=32` rotates which voicing set `keys.Keys` is comping, live-
            # adjustable from this group's own UI sliders (see flet/base.py's
            # `PatchGroup`) - see docs/todos/rack-linking-next.md
            EvolvingGroup(
                "Lead Melody", (self.lead_muted_keys, self.lead_keys), bars=32
            ),
            # strings: soft, sustained harmonic accompaniment behind the lead.
            # `bars=16` rotates the colour voice between a 9th and a 13th
            # (see strings.py's `COLOUR_TONE_VARIANTS`). A light, "invisible mix
            # help" duck off the kick, not an audible EDM pump - the lofi genre's
            # own subtler take on the deep-house sidechain move (see
            # drums/kick/AGENTS.md's "Sidechaining" reference)
            EvolvingGroup("Strings", (self.pad_strings,), bars=16),
            # bass: sparse, thumpy, four-bar phrase with an occasional offbeat
            # re-entry (see tonal/bass/profiles.py's `_conversation`), or the
            # original one-bar muted groove. `bars=8` rotates each style's own
            # pattern variant (see profiles.py's `CONVERSATION_VARIANTS`/
            # `MUTED_VARIANTS`)
            EvolvingGroup("Bass", (self.bass_conversation, self.bass_muted), bars=8),
            # high register call-and-response: a soft FM bell, tuned high and
            # sparse. The rack has no cross-patch event bus for the bell to
            # literally listen for a bass hit and answer it, so this is an
            # approximation - a sparse, high, quiet voice on the shared clock
            # rather than one triggered by the bass's own triggers (see
            # lofi/README.md's "Concept-to-patch mapping")
            GroupController(
                "High Response",
                (bell.BellFm(root_freq=notes.A5, strike=0.3, ring=1.1, rate=-1),),
            ),
            # atmosphere: continuous vinyl dust / tape crackle, felt more than heard
            GroupController("Vinyl Dust", (noise.NoiseDust(),)),
            self.kick,
            GroupController("Snare", (snare.SnareLofi(),)),
            GroupController("Hi-hat", (hat.GrooveLofi(),)),
        )
