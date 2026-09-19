from __future__ import annotations

from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox, interactive_output
from pyo.lib.effects import Chorus, Delay, Freeverb
from pyo.lib.generators import Rossler, SuperSaw

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.psyambient.common import ContinuousSequencer

ROOT_FREQ = 165  # E3, current default


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
    # subtle, slow pitch instability rather than a discrete note pattern -
    # keeps the pad "dreamy" without ever resolving to a new pitch
    pitch_wander = Rossler(pitch=0.02, chaos=0.4, mul=pitch_drift, add=root_freq)

    saw_voice = SuperSaw(freq=pitch_wander, detune=detune, bal=detune_bal, mul=0.2)
    chorused = Chorus(saw_voice, depth=chorus_depth, feedback=chorus_feedback, bal=chorus_bal)
    reverb_voice = Freeverb(chorused, size=reverb_size, damp=reverb_damp, bal=reverb_bal)
    voice = Delay(reverb_voice, delay=delay_time, feedback=delay_feedback, maxdelay=2)

    return Patch(sequencer=ContinuousSequencer(), voice=voice)


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create soundscape_wash controls with parameter descriptions beside each slider."""

    def set_params(
        enabled,
        root_freq,
        detune,
        detune_bal,
        pitch_drift,
        chorus_depth,
        chorus_feedback,
        chorus_bal,
        reverb_size,
        reverb_damp,
        reverb_bal,
        delay_time,
        delay_feedback,
        volume,
    ):
        if controller is not None and controller.applying:
            return
        if not enabled:
            rack.stop("soundscape_wash")
            return

        patch = build(
            root_freq,
            detune,
            detune_bal,
            pitch_drift,
            chorus_depth,
            chorus_feedback,
            chorus_bal,
            reverb_size,
            reverb_damp,
            reverb_bal,
            delay_time,
            delay_feedback,
        )
        patch.volume = volume
        rack.start("soundscape_wash", patch)

    enabled = Checkbox(value=False, description="soundscape_wash on/off")
    root_freq = FloatSlider(min=55, max=440, step=1, value=ROOT_FREQ, description="root_freq")
    detune = FloatSlider(min=0, max=1, step=0.05, value=0.6, description="detune")
    detune_bal = FloatSlider(min=0, max=1, step=0.05, value=0.7, description="detune_bal")
    pitch_drift = FloatSlider(min=0, max=1, step=0.01, value=0.03, description="pitch_drift")
    chorus_depth = FloatSlider(min=0, max=5, step=0.1, value=2.5, description="chorus_depth")
    chorus_feedback = FloatSlider(
        min=0, max=1, step=0.05, value=0.35, description="chorus_feedback"
    )
    chorus_bal = FloatSlider(min=0, max=1, step=0.05, value=0.6, description="chorus_bal")
    reverb_size = FloatSlider(min=0, max=1, step=0.05, value=0.9, description="reverb_size")
    reverb_damp = FloatSlider(min=0, max=1, step=0.05, value=0.35, description="reverb_damp")
    reverb_bal = FloatSlider(min=0, max=1, step=0.05, value=0.9, description="reverb_bal")
    delay_time = FloatSlider(min=0.05, max=2, step=0.05, value=0.8, description="delay_time")
    delay_feedback = FloatSlider(
        min=0, max=0.9, step=0.05, value=0.25, description="delay_feedback"
    )
    volume = FloatSlider(min=0, max=2, step=0.1, value=0.6, description="volume")

    controls = {
        "enabled": enabled,
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
        "volume": volume,
    }
    if controller is not None:
        controller.register(
            "soundscape_wash",
            controls,
            lambda: set_params(**{name: widget.value for name, widget in controls.items()}),
        )

    output = interactive_output(set_params, controls)
    slider_rows = [
        HBox([root_freq, HTML("Base frequency of the SuperSaw voice.")]),
        HBox([detune, HTML("SuperSaw detune depth - higher is thicker and hazier.")]),
        HBox([detune_bal, HTML("Balance toward the detuned oscillators - higher is wider.")]),
        HBox([pitch_drift, HTML("Depth of slow pitch instability - subtle by default.")]),
        HBox([chorus_depth, HTML("Chorus modulation depth - higher is wider and thicker.")]),
        HBox([chorus_feedback, HTML("Chorus feedback - higher adds more density to the haze.")]),
        HBox([chorus_bal, HTML("Chorus dry/wet balance - 0 is dry and 1 is wet.")]),
        HBox([reverb_size, HTML("Reverb room size - larger is more enveloping.")]),
        HBox([reverb_damp, HTML("Reverb high-frequency damping - higher is darker.")]),
        HBox([reverb_bal, HTML("Reverb dry/wet balance - 0 is dry and 1 is wet.")]),
        HBox([delay_time, HTML("Delay time - adds a further layer of spatial repetition.")]),
        HBox(
            [
                delay_feedback,
                HTML("Delay feedback - higher repeats echoes more times before decaying."),
            ]
        ),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
