"""Patch definitions for the clock-locked lofi beats-to-study-to rack."""

from collections.abc import Callable

from pyoscillate.controller import GroupController
from pyoscillate.harmony import C, Harmony
from pyoscillate.patches.base import Patch, SidechainSource
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
from pyoscillate.projects.base import MacroSpec, Rack


def _lerp(spec: SliderSpec, value: float) -> float:
    return spec.minimum + value * (spec.maximum - spec.minimum)


def _apply_energy(value: float, resolve_group_patch: Callable[[str], Patch | None]) -> None:
    """The lofi rack's one macro: a single 0-1 "Energy" push that lifts (or
    relaxes) brightness and drive together across bass, strings, and lead -
    same "push a value into whichever patch is active" shape as `on_evolve`,
    just user-triggered from a slider instead of the clock. Reuses each
    style's own `Param` slider range (rather than restating min/max here) so
    the mapping tracks a range if it's ever retuned, and `configure()` skips
    whichever of these names a given active style doesn't have - `bass` group
    has just `cutoff`, `lead` group's two styles have `brightness`/`drive`
    (`lead.Lead`) or `bark`/`bite` (`keys.Keys`)."""
    bass_patch = resolve_group_patch("bass")
    if bass_patch is not None:
        bass_patch.configure(cutoff=_lerp(bass.GrooveBass.cutoff.spec, value))

    strings_patch = resolve_group_patch("strings")
    if strings_patch is not None:
        strings_patch.configure(
            brightness=_lerp(strings.Strings.brightness.spec, value),
            shimmer=_lerp(strings.Strings.shimmer.spec, value),
        )

    lead_patch = resolve_group_patch("lead")
    if lead_patch is not None:
        lead_patch.configure(
            brightness=_lerp(lead.Lead.brightness.spec, value),
            drive=_lerp(lead.Lead.drive.spec, value),
            bark=_lerp(keys.Keys.bark.spec, value),
            bite=_lerp(keys.Keys.bite.spec, value),
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
    # a single rack-wide "Energy" slider - the manual counterpart to task 1's
    # clock-triggered `on_evolve` rotations, see docs/todos/rack-linking-next.md
    macro = MacroSpec(
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
    )

    def build_groups(self) -> tuple[GroupController, ...]:
        return (
            # lead melody: the rack's foreground - either the family's own sparse,
            # rest-heavy pentatonic motif (a "muted pluck") or the existing FM
            # electric piano's close-voiced comping, reused unmodified.
            # `bars=32` rotates which voicing set `keys.Keys` is comping, live-
            # adjustable from this group's own UI sliders (see flet/base.py's
            # `PatchGroup`) - see docs/todos/rack-linking-next.md
            GroupController(
                "lead",
                "Lead Melody",
                (lead.LeadMutedKeys(), keys.Keys()),
                bars=32,
            ),
            # strings: soft, sustained harmonic accompaniment behind the lead.
            # `bars=16` rotates the colour voice between a 9th and a 13th
            # (see strings.py's `COLOUR_TONE_VARIANTS`) - see
            # docs/todos/rack-linking-next.md
            # a light, "invisible mix help" duck off the kick, not an audible EDM
            # pump - the lofi genre's own subtler take on the deep-house sidechain
            # move (see drums/kick/CLAUDE.md's "Sidechaining" reference and
            # docs/todos/rack-linking-next.md)
            GroupController(
                "strings",
                "Strings",
                (strings.Strings(sidechain=SidechainSource("kick", depth=0.15, release=0.25)),),
                bars=16,
            ),
            # bass: sparse, thumpy, four-bar phrase with an occasional offbeat
            # re-entry (see tonal/bass/profiles.py's `_conversation`), or the
            # original one-bar muted groove. `bars=8` rotates each style's own
            # pattern variant (see profiles.py's `CONVERSATION_VARIANTS`/
            # `MUTED_VARIANTS`) - see docs/todos/rack-linking-next.md
            GroupController(
                "bass",
                "Bass",
                (
                    bass.BassConversation(
                        sidechain=SidechainSource("kick", depth=0.25, release=0.2)
                    ),
                    bass.BassMuted(sidechain=SidechainSource("kick", depth=0.25, release=0.2)),
                ),
                bars=8,
            ),
            # high register call-and-response: a soft FM bell, tuned high and
            # sparse. The rack has no cross-patch event bus for the bell to
            # literally listen for a bass hit and answer it, so this is an
            # approximation - a sparse, high, quiet voice on the shared clock
            # rather than one triggered by the bass's own triggers (see
            # lofi/README.md's "Concept-to-patch mapping")
            GroupController(
                "high",
                "High Response",
                (bell.BellFm(root_freq=notes.A5, strike=0.3, ring=1.1, rate=-1),),
            ),
            # atmosphere: continuous vinyl dust / tape crackle, felt more than heard
            GroupController("noise", "Vinyl Dust", (noise.NoiseDust(),)),
            GroupController("kick", "Kick", (kick.KickLofi(),)),
            GroupController("snare", "Snare", (snare.SnareLofi(),)),
            GroupController("hat", "Hi-hat", (hat.GrooveLofi(),)),
        )
