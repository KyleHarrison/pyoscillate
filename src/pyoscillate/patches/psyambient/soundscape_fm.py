from __future__ import annotations

from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox, interactive_output
from pyo.lib.effects import Delay, Freeverb
from pyo.lib.generators import FM, Lorenz, Rossler

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.psyambient.common import ContinuousSequencer

ROOT_FREQ = 110  # A2, current default


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
    ratio_chaos = Rossler(pitch=chaos_speed, chaos=chaos_amount, mul=0.4, add=1.5)
    index_chaos = Lorenz(pitch=chaos_speed * 1.3, chaos=chaos_amount, mul=3, add=4)

    fm_voice = FM(carrier=root_freq, ratio=ratio_chaos, index=index_chaos, mul=0.2)
    reverb_voice = Freeverb(fm_voice, size=reverb_size, damp=reverb_damp, bal=reverb_bal)
    voice = Delay(reverb_voice, delay=delay_time, feedback=delay_feedback, maxdelay=2)

    return Patch(sequencer=ContinuousSequencer(), voice=voice)


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create soundscape_fm controls with parameter descriptions beside each slider."""

    def set_params(
        enabled,
        root_freq,
        chaos_speed,
        chaos_amount,
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
            rack.stop("soundscape_fm")
            return

        patch = build(
            root_freq,
            chaos_speed,
            chaos_amount,
            reverb_size,
            reverb_damp,
            reverb_bal,
            delay_time,
            delay_feedback,
        )
        patch.volume = volume
        rack.start("soundscape_fm", patch)

    enabled = Checkbox(value=False, description="soundscape_fm on/off")
    root_freq = FloatSlider(min=55, max=220, step=1, value=ROOT_FREQ, description="root_freq")
    chaos_speed = FloatSlider(min=0.01, max=0.5, step=0.01, value=0.04, description="chaos_speed")
    chaos_amount = FloatSlider(min=0, max=1, step=0.05, value=0.6, description="chaos_amount")
    reverb_size = FloatSlider(min=0, max=1, step=0.05, value=0.85, description="reverb_size")
    reverb_damp = FloatSlider(min=0, max=1, step=0.05, value=0.4, description="reverb_damp")
    reverb_bal = FloatSlider(min=0, max=1, step=0.05, value=0.85, description="reverb_bal")
    delay_time = FloatSlider(min=0.05, max=2, step=0.05, value=0.6, description="delay_time")
    delay_feedback = FloatSlider(
        min=0, max=0.9, step=0.05, value=0.35, description="delay_feedback"
    )
    volume = FloatSlider(min=0, max=2, step=0.1, value=0.6, description="volume")

    controls = {
        "enabled": enabled,
        "root_freq": root_freq,
        "chaos_speed": chaos_speed,
        "chaos_amount": chaos_amount,
        "reverb_size": reverb_size,
        "reverb_damp": reverb_damp,
        "reverb_bal": reverb_bal,
        "delay_time": delay_time,
        "delay_feedback": delay_feedback,
        "volume": volume,
    }
    if controller is not None:
        controller.register(
            "soundscape_fm",
            controls,
            lambda: set_params(**{name: widget.value for name, widget in controls.items()}),
        )

    output = interactive_output(set_params, controls)
    slider_rows = [
        HBox([root_freq, HTML("Carrier frequency - the pad's held pitch.")]),
        HBox(
            [
                chaos_speed,
                HTML("How fast the timbre wanders - lower is slower and more hypnotic."),
            ]
        ),
        HBox(
            [
                chaos_amount,
                HTML("How unpredictable the wander is - higher is more psychedelic."),
            ]
        ),
        HBox([reverb_size, HTML("Reverb room size - larger is more enveloping.")]),
        HBox([reverb_damp, HTML("Reverb high-frequency damping - higher is darker.")]),
        HBox([reverb_bal, HTML("Reverb dry/wet balance - 0 is dry and 1 is wet.")]),
        HBox([delay_time, HTML("Delay time - smears the timbral drift across time.")]),
        HBox(
            [
                delay_feedback,
                HTML("Delay feedback - higher repeats echoes more times before decaying."),
            ]
        ),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
