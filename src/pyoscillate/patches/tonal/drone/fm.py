from __future__ import annotations

from pyo.lib.controls import SigTo
from pyo.lib.effects import Delay, Freeverb
from pyo.lib.generators import FM, Lorenz, Rossler

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousSequencer
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.utility.notes import notes

ROOT_FREQ = notes.A2  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        55,
        220,
        1,
        ROOT_FREQ,
        "Register",
        "Sets the pad's held pitch, the carrier tone everything else is built on.",
        (PyoParamRef(FM, "carrier"),),
    ),
    SliderSpec(
        "chaos_speed",
        0.01,
        0.5,
        0.01,
        0.04,
        "Drift speed",
        "How fast the pad's timbre wanders; lower is slower and more hypnotic, higher feels more restless.",
        (PyoParamRef(Rossler, "pitch"), PyoParamRef(Lorenz, "pitch")),
    ),
    SliderSpec(
        "chaos_amount",
        0,
        1,
        0.05,
        0.6,
        "Instability",
        "How unpredictable the wander is; higher feels more psychedelic and alive, lower stays closer to a steady tone.",
        (PyoParamRef(Rossler, "chaos"), PyoParamRef(Lorenz, "chaos")),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.85,
        "Space",
        "Sets how enveloping the pad's room feels; larger is more immersive and distant.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.4,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher is warmer and more muffled, lower stays brighter and shimmering.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.85,
        "Distance",
        "Blends how much of the pad is heard through the reverb versus dry; higher dissolves it into the space, lower keeps it present.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
    SliderSpec(
        "delay_time",
        0.05,
        2,
        0.05,
        0.6,
        "Echo spacing",
        "Sets the time between echo repeats, smearing the timbral drift across time.",
        (PyoParamRef(Delay, "delay"),),
    ),
    SliderSpec(
        "delay_feedback",
        0,
        0.9,
        0.05,
        0.35,
        "Echo density",
        "Sets how many times each echo repeats before decaying; higher creates a denser, more layered wash.",
        (PyoParamRef(Delay, "feedback"),),
    ),
)


def build(
    root_freq: float = ROOT_FREQ,
    chaos_speed: float = 0.04,
    chaos_amount: float = 0.6,
    reverb_size: float = 0.85,
    reverb_damp: float = 0.4,
    reverb_bal: float = 0.85,
    delay_time: float = 0.6,
    delay_feedback: float = 0.35,
) -> Patch:
    """Free-running FM pad whose timbre is driven entirely by chaotic attractors, with no clocked note pattern at all.

    Args:
        root_freq: Carrier frequency (Hz) of the FM voice. The pitch never
            changes - all movement in this pad comes from the timbre
            drifting underneath a held note, which is what gives it a
            dreamy, sound-design character rather than a melodic one.
        chaos_speed: `pitch` parameter shared by the two attractors driving
            ratio and index - how fast they wander. The low default makes
            the timbre drift almost too slowly to consciously track, which
            reads as spacious and hypnotic; raising it makes the pad
            audibly restless and unstable.
        chaos_amount: `chaos` parameter shared by both attractors, 0-1.
            Higher values push the wander further from smooth, LFO-like
            regularity toward true unpredictability - more psychedelic,
            less "breathing"; lower values pull it back toward periodic
            movement.
        reverb_size: Freeverb room size (0-1). Large by default so the pad
            reads as an enveloping space rather than a distinct voice;
            lowering it brings the raw FM tone forward.
        reverb_damp: Freeverb high-frequency damping (0-1). Higher values
            darken the tail for a more distant, underwater quality; lower
            values keep it bright and shimmering.
        reverb_bal: Freeverb dry/wet balance (0-1). Kept high by default so
            the pad is heard mostly through its reverb space.
        delay_time: Delay line time in seconds. Combined with the reverb,
            this smears each moment of the pad's timbral drift into the
            next, thickening the sense of a continuously evolving texture.
        delay_feedback: Delay feedback (0-1). Higher values repeat each
            echo more times before decaying, building a denser, more
            psychedelic wash; lower values give a single, subtle slap.
    """
    # Rossler wanders smoothly, Lorenz more angularly - pairing them on ratio
    # and index gives the timbre two independently-textured axes of drift
    # instead of both parameters moving in the same "shape" of way
    live = {
        name: SigTo(value=value, time=0.15)
        for name, value in {
            "root_freq": root_freq,
            "chaos_speed": chaos_speed,
            "chaos_amount": chaos_amount,
            "reverb_size": reverb_size,
            "reverb_damp": reverb_damp,
            "reverb_bal": reverb_bal,
            "delay_time": delay_time,
            "delay_feedback": delay_feedback,
        }.items()
    }

    ratio_chaos = Rossler(pitch=live["chaos_speed"], chaos=live["chaos_amount"], mul=0.4, add=1.5)
    index_speed = live["chaos_speed"] * 1.3
    index_chaos = Lorenz(pitch=index_speed, chaos=live["chaos_amount"], mul=3, add=4)

    fm_voice = FM(carrier=live["root_freq"], ratio=ratio_chaos, index=index_chaos, mul=0.2)
    reverb_voice = Freeverb(
        fm_voice,
        size=live["reverb_size"],
        damp=live["reverb_damp"],
        bal=live["reverb_bal"],
    )
    voice = Delay(
        reverb_voice,
        delay=live["delay_time"],
        feedback=live["delay_feedback"],
        maxdelay=2,
    )

    return Patch(
        sequencer=ContinuousSequencer(),
        voice=voice,
        controls={
            name: lambda value, control=control: setattr(control, "value", value)
            for name, control in live.items()
        },
        resources=(
            *live.values(),
            ratio_chaos,
            index_speed,
            index_chaos,
            fm_voice,
            reverb_voice,
        ),
    )
