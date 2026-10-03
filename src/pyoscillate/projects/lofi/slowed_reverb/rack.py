# Run: uv run flet run src/flet/slowed_reverb/app.py
"""Patch definitions for the dark, slowed-and-reverbed lofi rack."""

from pyoscillate.controller import (
    GroupControl,
    GroupController,
    ParamControl,
    SidechainSource,
    Slot,
    SlotTarget,
)
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.evolve import Evolve
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.texture.noise import noise
from pyoscillate.patches.tonal.bass import hover as bass
from pyoscillate.patches.tonal.drone import wash
from pyoscillate.patches.tonal.keys import keys
from pyoscillate.patches.tonal.pluck import pluck
from pyoscillate.patches.tonal.strings import strings
from pyoscillate.projects.base import Rack
from pyoscillate.theory.phrase import Hooks, Progressions, Rhythms
from pyoscillate.theory.pitch import Note


class SlowedReverbRack(Rack):
    """Dark, slowed, bass-dominant lofi rack: a hovering sine-like bass
    under a long, breathing reverb tail, a dark reverberant pad wash, and a
    quiet, dusty texture bed - see README.md for the reference-track
    grounding behind this brief."""

    # felt tempo from the reference track's half-time drag (see README.md)
    bpm = 61
    # The lofi strings follow this vamp; Keys stacks its voicings on the same chords.
    # Its white-note pitch collection also preserves the rack's E-Phrygian
    # colour, while E remains a common tone for the wash underneath it.
    harmony = Harmony(key=Note.KEY_C)
    progression = Progressions.JAZZ_TURNAROUND

    # The kick is declared first so the pad can duck off it; `layout` below
    # sets the display order.
    kick_lofi = Slot(
        kick.KickLofi,
        evolve=Evolve(8, (Rhythms.KICK_LOFI, Rhythms.KICK_LOFI_FULL)),
        level=0.4,
        drive=0.2,
        punch=0.8,
        length=0.8,
        click=0.5,
        rate=-1,
        volume=0.3,
    )
    kick_group = GroupController("Kick", (kick_lofi,))

    lead_strings = Slot(
        strings.Strings,
        evolve=Evolve(8),
        root_freq=Note.F3,
        brightness=3900,
        attack=2.15,
        release=2.9,
        spread=0.2,
        shimmer=0.8,
        colour=0.9,
        volume=0.7,
    )
    lead_keys = Slot(
        keys.Keys,
        evolve=Evolve(8),
        root_freq=Note.E3,
        bark=5.0,
        bite=0.3,
        decay=3.1,
        tremolo=0.85,
        wobble=0.6,
        volume=1.5,
    )
    # the bass hovers on E and the pad holds a static register; neither
    # follows the rack's chord progression (see README.md's shared-harmony note)
    bass_hover = Slot(
        bass.BassHover,
        root_freq=Note.E1,
        cutoff=770,
        reverb_size=0.85,
        reverb_damp=0.85,
        reverb_bal=0.85,
        breath=0.5,
        rate=-1,
        volume=1.6,
    )
    pad_wash = Slot(
        wash.SoundscapeWash,
        evolve=Evolve(16),
        sidechains=(SidechainSource(kick_group, depth=0.15, release=0.3),),
        root_freq=Note.E2,
        detune=0.45,
        detune_bal=0.1,
        pitch_drift=0.8,
        chorus_depth=2.1,
        chorus_feedback=0.8,
        chorus_bal=0.75,
        reverb_size=0.25,
        reverb_damp=0.15,
        reverb_bal=0.75,
        delay_time=1.0,
        delay_feedback=0.7,
        volume=0.5,
    )
    hook_pluck = Slot(
        pluck.PluckHook,
        evolve=Evolve(8, (Hooks.SPARSE_HOOK, Hooks.FULL_HOOK)),
        root_freq=Note.E3,
        rate=-1,
        volume=0.4,
    )
    texture_dust = Slot(
        noise.NoiseDust,
        brightness=1200,
        colour=1.7,
        motion=0.3,
        depth=0.75,
        level=0.35,
        volume=0.3,
    )
    hat_lofi = Slot(
        hat.GrooveLofi,
        evolve=Evolve(8, (Rhythms.HAT_LOFI, Rhythms.HAT_LOFI_FULL)),
        level=0.06,
        cutoff=3500,
        metal=0.1,
        length=0.75,
        rate=-1,
        volume=0.12,
    )

    lead_lift = GroupControl(
        SliderSpec(
            "lift",
            0,
            1,
            0.05,
            0,
            "Lift",
            "Opens the strings' brightness and shimmer and the keys' bark and tremolo.",
        ),
        (
            SlotTarget(
                lead_strings,
                (
                    ParamControl(
                        strings.Strings.brightness,
                        3900,
                        strings.Strings.brightness.spec.maximum,
                    ),
                    ParamControl(
                        strings.Strings.shimmer,
                        0.8,
                        strings.Strings.shimmer.spec.maximum,
                    ),
                    ParamControl(Patch.volume, 0.7, 0.9),
                ),
            ),
            SlotTarget(
                lead_keys,
                (
                    ParamControl(keys.Keys.bark, 5.0, keys.Keys.bark.spec.maximum),
                    ParamControl(
                        keys.Keys.tremolo, 0.85, keys.Keys.tremolo.spec.maximum
                    ),
                    ParamControl(Patch.volume, 1.5, 1.7),
                ),
            ),
        ),
    )
    pad_lift = GroupControl(
        SliderSpec(
            "lift",
            0,
            1,
            0.05,
            0,
            "Lift",
            "Gradually opens the pad's chorus and brings it forward.",
        ),
        (
            SlotTarget(
                pad_wash,
                (
                    ParamControl(
                        wash.SoundscapeWash.chorus_depth,
                        2.1,
                        wash.SoundscapeWash.chorus_depth.spec.maximum,
                    ),
                    ParamControl(Patch.volume, 0.5, 0.65),
                ),
            ),
        ),
    )
    hook_lift = GroupControl(
        SliderSpec(
            "lift",
            0,
            1,
            0.05,
            0,
            "Lift",
            "Brightens the upper hook and brings it forward.",
        ),
        (
            SlotTarget(
                hook_pluck,
                (
                    ParamControl(
                        pluck.PluckHook.brightness,
                        2.4,
                        pluck.PluckHook.brightness.spec.maximum,
                    ),
                    ParamControl(Patch.volume, 0.4, 0.55),
                ),
            ),
        ),
    )
    arrival_lift = GroupControl(
        SliderSpec(
            "lift",
            0,
            1,
            0.05,
            0,
            "Lift",
            "Gradually opens the chorus, upper hook and lead presence for a section arrival.",
        ),
        (lead_lift, pad_lift, hook_lift),
    )

    lead_group = GroupController(
        "Lead",
        (lead_strings, lead_keys),
        "Choose strings or keys to give the wash harmony and pulse.",
        controls=(lead_lift,),
    )
    # foreground: carries ~87% of the reference's RMS - see
    # `bass.hover.BassHover`'s own long reverb tail and breathing swell, which
    # is this rack's main "dark, reverberant" carrier
    bass_group = GroupController("Bass", (bass_hover,))
    # a static, dark reverberant pad bed under the bass - reused unmodified
    # from `tonal/drone`'s existing wash style, just re-tuned dark and distant
    # (see README.md's mapping table)
    pad_group = GroupController("Pad", (pad_wash,), controls=(pad_lift,))
    hook_group = GroupController("Hook", (hook_pluck,), controls=(hook_lift,))
    # the section-arrival layers: its own `lift` moves each inner group's
    # `lift`, which keeps the per-patch mapping with the group that owns it
    arrival_group = GroupController(
        "Arrival",
        (lead_group, pad_group, hook_group),
        "Lead, pad and hook together.",
        controls=(arrival_lift,),
    )
    # quiet, dusty texture bed - reused unmodified from the `boom_bap`
    # sibling's own atmosphere layer, darkened further to match this brief's
    # ~850 Hz mix-wide rolloff
    texture_group = GroupController("Texture", (texture_dust,))
    hat_group = GroupController("Hi-hat", (hat_lofi,))
    layout = (
        arrival_group,
        bass_group,
        texture_group,
        kick_group,
        hat_group,
    )
