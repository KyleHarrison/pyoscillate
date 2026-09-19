from __future__ import annotations

from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox, interactive_output
from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM, Sine

from pysynth.clock import BAR, Clock
from pysynth.patches.base import Patch, PatchRack
from pysynth.tempo import Tempo

# mostly small steps so the pitch glides rather than leaps
DRONE_INTERVALS = [0, -5, -3, 2, 0, -7, -5, 3]

DRONE_ROOT = 186  # current notebook default


def build(
    tempo: Tempo,
    clock: Clock,
    root_freq: float = DRONE_ROOT,
    reverb_size: float = 0.7,
    reverb_damp: float = 0.7,
    reverb_bal: float = 0.9,
) -> Patch:
    """Slow-winding FM drone: note changes once every 8 bars, with a continuously drifting timbre.

    Args:
        tempo: Shared tempo grid; one drone step is `tempo.bar * 8`, and the
            ratio/index LFO periods are derived from that step time.
        clock: Shared master pulse; the drone steps every 8 bars (`BAR * 8`),
            phase-locked to every other patch on the clock.
        root_freq: Fundamental frequency (Hz) the drone glides between, before
            the `DRONE_INTERVALS` semitone offsets are applied each step.
            Raising it brings the drone closer to the arp's register and
            makes it easier to pick out as a melodic voice; lowering it
            moves it toward the bass and makes it read more as a sustained
            sub layer.
        reverb_size: Freeverb room size (0-1). Larger values give the drone a
            huge, cavernous decay that smears note changes into each other;
            smaller values keep each glide more distinct and present.
        reverb_damp: Freeverb high-frequency damping (0-1). The default is
            low (0.3) so the drone's reverb tail stays bright and shimmering
            rather than going dark and muffled; raise it for a warmer, more
            subdued wash.
        reverb_bal: Freeverb dry/wet balance (0 = fully dry, 1 = fully wet).
            The default is high (0.9) so the drone is heard almost entirely
            through the reverb, which is what makes it sit as a diffuse
            atmospheric bed rather than a distinct pitched voice; lowering
            it brings the raw FM tone forward.
    """
    # the drone changes note far more slowly than the bass (per 16th), arp (per
    # 8th), or either hat
    step_time = tempo.bar * 8

    # glides to each new frequency over most of the step time instead of snapping
    drone_freq = SigTo(value=root_freq, time=step_time * 0.9)

    # ratio and index each ride their own slow LFO, with periods measured in
    # whole drone steps, so the tone keeps evolving independently of pitch changes
    ratio_lfo = Sine(freq=1 / (step_time * 1.3), mul=0.2, add=1.5)
    index_lfo = Sine(freq=1 / (step_time * 0.7), mul=2, add=3)

    fm_voice = FM(carrier=drone_freq, ratio=ratio_lfo, index=index_lfo, mul=0.2)
    voice = Freeverb(fm_voice, size=reverb_size, damp=reverb_damp, bal=reverb_bal)

    step = {"i": 0}

    def next_step() -> None:
        i = step["i"] % len(DRONE_INTERVALS)
        drone_freq.value = root_freq * pow(2, DRONE_INTERVALS[i] / 12)
        step["i"] += 1

    sequencer = clock.subscribe(BAR * 8, next_step)
    return Patch(sequencer=sequencer, voice=voice)


def widget(rack: PatchRack, tempo: Tempo, clock: Clock) -> VBox:
    """Create drone controls with parameter descriptions beside each slider."""

    def set_params(enabled, root_freq, reverb_size, reverb_damp, reverb_bal, volume):
        if not enabled:
            rack.stop("drone")
            return

        drone_patch = build(tempo, clock, root_freq, reverb_size, reverb_damp, reverb_bal)
        drone_patch.volume = volume
        rack.start("drone", drone_patch)

    enabled = Checkbox(value=False, description="drone on/off")
    root_freq = FloatSlider(min=55, max=220, step=1, value=DRONE_ROOT, description="root_freq")
    reverb_size = FloatSlider(min=0, max=1, step=0.05, value=0.7, description="reverb_size")
    reverb_damp = FloatSlider(min=0, max=1, step=0.05, value=0.7, description="reverb_damp")
    reverb_bal = FloatSlider(min=0, max=1, step=0.05, value=0.9, description="reverb_bal")
    volume = FloatSlider(min=0, max=2, step=0.1, value=1.0, description="volume")

    output = interactive_output(
        set_params,
        {
            "enabled": enabled,
            "root_freq": root_freq,
            "reverb_size": reverb_size,
            "reverb_damp": reverb_damp,
            "reverb_bal": reverb_bal,
            "volume": volume,
        },
    )
    slider_rows = [
        HBox([root_freq, HTML("Fundamental frequency the drone glides between.")]),
        HBox([reverb_size, HTML("Reverb room size - larger is more cavernous.")]),
        HBox([reverb_damp, HTML("Reverb high-frequency damping - higher is darker.")]),
        HBox([reverb_bal, HTML("Reverb dry/wet balance - 0 is dry and 1 is wet.")]),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
