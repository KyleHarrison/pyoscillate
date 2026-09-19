from __future__ import annotations

from ipywidgets import VBox
from pyo.lib.controls import SigTo
from pyo.lib.effects import Chorus, Delay, Freeverb
from pyo.lib.generators import Rossler, SuperSaw

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.psyambient.common import ContinuousSequencer
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget

ROOT_FREQ = 165  # E3, current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        55,
        440,
        1,
        ROOT_FREQ,
        "Root frequency",
        "Base frequency of the wash.",
        (PyoParamRef(SuperSaw, "freq"),),
    ),
    SliderSpec(
        "detune",
        0,
        1,
        0.05,
        0.6,
        "Detune",
        "Oscillator spread - higher is thicker and hazier.",
        (PyoParamRef(SuperSaw, "detune"),),
    ),
    SliderSpec(
        "detune_bal",
        0,
        1,
        0.05,
        0.7,
        "Detune balance",
        "Balance toward detuned oscillators.",
        (PyoParamRef(SuperSaw, "bal"),),
    ),
    SliderSpec(
        "pitch_drift",
        0,
        1,
        0.01,
        0.03,
        "Pitch drift",
        "Depth of slow pitch instability.",
        (),
    ),
    SliderSpec(
        "chorus_depth",
        0,
        5,
        0.1,
        2.5,
        "Chorus depth",
        "Chorus modulation depth.",
        (PyoParamRef(Chorus, "depth"),),
    ),
    SliderSpec(
        "chorus_feedback",
        0,
        1,
        0.05,
        0.35,
        "Chorus feedback",
        "Density of the chorus repeats.",
        (PyoParamRef(Chorus, "feedback"),),
    ),
    SliderSpec(
        "chorus_bal",
        0,
        1,
        0.05,
        0.6,
        "Chorus balance",
        "Chorus dry/wet balance.",
        (PyoParamRef(Chorus, "bal"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.9,
        "Reverb size",
        "Reverb room size.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.35,
        "Reverb damping",
        "Reverb high-frequency damping.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.9,
        "Reverb balance",
        "Reverb dry/wet balance.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
    SliderSpec(
        "delay_time",
        0.05,
        2,
        0.05,
        0.8,
        "Delay time",
        "Delay line time.",
        (PyoParamRef(Delay, "delay"),),
    ),
    SliderSpec(
        "delay_feedback",
        0,
        0.9,
        0.05,
        0.25,
        "Delay feedback",
        "Delay feedback.",
        (PyoParamRef(Delay, "feedback"),),
    ),
)


def build(
    root_freq: float = ROOT_FREQ,
    detune: float = 0.6,
    detune_bal: float = 0.7,
    pitch_drift: float = 0.03,
    chorus_depth: float = 2.5,
    chorus_feedback: float = 0.35,
    chorus_bal: float = 0.6,
    reverb_size: float = 0.9,
    reverb_damp: float = 0.35,
    reverb_bal: float = 0.9,
    delay_time: float = 0.8,
    delay_feedback: float = 0.25,
) -> Patch:
    """Washy detuned pad: a SuperSaw voice smeared with chorus, reverb, and delay for a shoegaze-style dream-pop ambience.

    Unlike `soundscape_fm`/`soundscape_filter`, the "evolving" quality here
    comes mostly from spatial smear (chorus/reverb/delay) rather than
    timbral or filter movement - the character is width and haze rather
    than wander.

    Args:
        root_freq: Base frequency (Hz) of the `SuperSaw` voice.
        detune: `SuperSaw` detune depth (0-1). Higher values spread the
            seven internal oscillators further apart in pitch, thickening
            the wash and making it feel hazier; lower values keep it
            closer to a single clean tone.
        detune_bal: `SuperSaw` balance between the center oscillator and
            the detuned ones (0-1). Higher values push the mix toward the
            detuned layers for a wider, less centered tone; lower values
            keep more of a stable, in-tune core audible underneath.
        pitch_drift: Depth (in Hz added to `root_freq`) of a slow `Rossler`
            attractor riding on the whole voice's pitch. Kept subtle by
            default so it reads as a gentle, dreamy instability rather than
            an audible wobble; raising it makes the pad noticeably detune
            over time.
        chorus_depth: `Chorus` modulation depth (0-5). Higher values widen
            and thicken the wash further; lower values keep the chorus
            effect subtle.
        chorus_feedback: `Chorus` feedback (0-1). Higher values make the
            chorused delay lines repeat more, adding density to the haze.
        chorus_bal: `Chorus` dry/wet balance (0-1). Higher values dissolve
            the pad further into the chorus effect.
        reverb_size: Freeverb room size (0-1). Very large by default so the
            pad reads as a huge, diffuse space rather than a distinct
            voice.
        reverb_damp: Freeverb high-frequency damping (0-1). Higher values
            darken the tail; lower values keep it airy and bright.
        reverb_bal: Freeverb dry/wet balance (0-1). Kept high so the pad is
            heard almost entirely through its reverb space.
        delay_time: Delay line time in seconds, adding a further layer of
            spatial repetition on top of the chorus and reverb.
        delay_feedback: Delay feedback (0-1). Higher values repeat each
            echo more times before decaying, for a denser wash.
    """
    live = {
        name: SigTo(value=value, time=0.15)
        for name, value in {
            "root_freq": root_freq,
            "detune": detune,
            "detune_bal": detune_bal,
            "pitch_drift": pitch_drift,
            "chorus_depth": chorus_depth,
            "chorus_feedback": chorus_feedback,
            "chorus_bal": chorus_bal,
            "reverb_size": reverb_size,
            "reverb_damp": reverb_damp,
            "reverb_bal": reverb_bal,
            "delay_time": delay_time,
            "delay_feedback": delay_feedback,
        }.items()
    }

    # subtle, slow pitch instability rather than a discrete note pattern -
    # keeps the pad "dreamy" without ever resolving to a new pitch
    pitch_wander = Rossler(pitch=0.02, chaos=0.4, mul=live["pitch_drift"], add=live["root_freq"])

    saw_voice = SuperSaw(freq=pitch_wander, detune=live["detune"], bal=live["detune_bal"], mul=0.2)
    chorused = Chorus(
        saw_voice,
        depth=live["chorus_depth"],
        feedback=live["chorus_feedback"],
        bal=live["chorus_bal"],
    )
    reverb_voice = Freeverb(
        chorused,
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
    )


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create soundscape_wash controls."""
    return patch_widget(rack, "soundscape_wash", build, PARAMETERS, controller=controller)
