from __future__ import annotations

from ipywidgets import (
    VBox,
)
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM, Sine
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

# arpeggio shape: root, minor 3rd, 5th, minor 7th, octave, up and back down
ARP_INTERVALS = [0, 3, 7, 10, 12, 10, 7, 3]

ARP_ROOT = 207  # current notebook default

PARAMETERS = (
    SliderSpec(
        "arp_root",
        110,
        440,
        1,
        ARP_ROOT,
        "Arpeggio root",
        "Root frequency.",
        (PyoParamRef(FM, "carrier"),),
    ),
    SliderSpec(
        "step_division",
        1,
        16,
        1,
        8,
        "Step division",
        "Clock spacing; changing it rebuilds the clock subscription.",
        (),
    ),
    SliderSpec(
        "fm_ratio",
        0.1,
        4,
        0.1,
        0.4,
        "FM ratio",
        "Carrier/modulator ratio.",
        (PyoParamRef(FM, "ratio"),),
    ),
    SliderSpec(
        "fm_index",
        0,
        10,
        0.1,
        3,
        "FM index",
        "FM brightness.",
        (PyoParamRef(FM, "index"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.25,
        "Reverb size",
        "Room size.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.15,
        "Reverb damping",
        "High-frequency damping.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.1,
        "Reverb balance",
        "Dry/wet balance.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
)


def build(
    tempo: Tempo,
    clock: Clock,
    arp_root: float = ARP_ROOT,
    step_division: int = 8,
    fm_ratio: float = 0.4,
    fm_index: float = 3,
    reverb_size: float = 0.25,
    reverb_damp: float = 0.15,
    reverb_bal: float = 0.1,
) -> Patch:
    """FM pad voice arpeggiated on the clock, with a slow amplitude swell and reverb.

    Args:
        tempo: Shared tempo grid; the swell period and envelope duration are
            derived from the resulting step time.
        clock: Shared master pulse; the arpeggio steps every `step_division`
            16th notes, phase-locked to every other patch on the clock.
        arp_root: Base frequency (Hz) of the arpeggio's root note, before the
            `ARP_INTERVALS` offsets are applied each step. Raising it moves
            the whole pad up in register; lowering it pushes the pad down
            toward the drone/bass range and can make the arpeggio read as
            muddier or more likely to clash with the bass.
        step_division: How often the arpeggio advances, in 16th notes (see
            `pyoscillate.clock`'s `SIXTEENTH`/`EIGHTH`/`FOURTH`/`BAR`, or any
            multiple of them). Larger values space the notes further apart
            and slow the arpeggio down; smaller values speed it up. The
            swell period and envelope duration scale with this so the pad
            keeps sounding right at any speed.
        fm_ratio: Ratio of modulator frequency to carrier frequency in the FM
            voice. Simple ratios (0.5, 1, 2) sound bell-like and harmonic;
            the default's slightly-off ratio (0.5012) is deliberately
            detuned so the partials beat softly against each other for a
            warm, unstable, analog-ish texture. Push it further from a
            simple ratio for a more dissonant, metallic tone; pull it toward
            an exact ratio for a cleaner, more tonal pad.
        fm_index: FM modulation index - how far the modulator swings the
            carrier's instantaneous frequency. Higher values add more
            sideband energy, producing a brighter, buzzier, more complex
            timbre; lower values approach a plain sine tone. Because `index`
            is fixed here (unlike the drone's LFO-modulated index), it sets
            a constant brightness for the whole pad.
        reverb_size: Freeverb room size (0-1). Larger values simulate a
            bigger space with a longer, denser decay tail, pushing the pad
            further back in the mix; smaller values give a tighter, more
            present ambience.
        reverb_damp: Freeverb high-frequency damping (0-1). Higher values
            absorb more high end as the reverb tail decays, making the
            trailing reverb sound darker and softer; lower values let the
            tail stay bright and ring on longer.
        reverb_bal: Freeverb dry/wet balance (0 = fully dry, 1 = fully wet).
            Higher values dissolve the pad further into the reverb space;
            lower values keep more of the direct, unprocessed FM tone
            audible.
    """
    arp_trig = Trig()
    step_time = tempo.sixteenth * step_division

    # slow swell over 32 steps so the pad breathes in and out across two bars
    arp_swell = Sine(freq=1 / (32 * step_time), mul=0.01, add=0.5)

    # dur is longer than the step time so envelopes overlap into a sustained pad
    envelope_table = CosTable([(0, 0), (2000, 1), (5000, 0.4), (8191, 0)])
    arp_env = TrigEnv(
        arp_trig, table=envelope_table, dur=step_time * 1.2, mul=arp_swell, add=-0.3
    )

    # slow, detuned ratio for a warm, slightly unstable atmospheric tone
    fm_voice = FM(
        carrier=arp_root, ratio=fm_ratio, index=fm_index, mul=arp_env, add=-0.3
    )
    voice = Freeverb(fm_voice, size=reverb_size, damp=reverb_damp, bal=reverb_bal)

    step = {"i": 0}

    def next_step() -> None:
        i = step["i"] % len(ARP_INTERVALS)
        fm_voice.carrier = arp_root * pow(2, ARP_INTERVALS[i] / 12)
        arp_trig.play()
        step["i"] += 1

    sequencer = clock.subscribe(step_division, next_step)
    return Patch(
        sequencer=sequencer,
        voice=voice,
        controls={
            "arp_root": lambda value: setattr(fm_voice, "carrier", value),
            "fm_ratio": lambda value: setattr(fm_voice, "ratio", value),
            "fm_index": lambda value: setattr(fm_voice, "index", value),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        },
    )


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
) -> VBox:
    """Create atmosphere controls."""
    return patch_widget(
        rack,
        "atmosphere",
        build,
        PARAMETERS,
        controller=controller,
        rebuild_parameters=("step_division",),
        build_kwargs={"tempo": tempo, "clock": clock},
    )

    """

    def set_params(
        enabled,
        step_division,
        arp_root,
        fm_ratio,
        fm_index,
        reverb_size,
        reverb_damp,
        reverb_bal,
        volume,
    ):
        if controller is not None and controller.applying:
            return
        if not enabled:
            rack.stop("atmosphere")
            return

        atmosphere_patch = build(
            tempo,
            clock,
            arp_root,
            step_division,
            fm_ratio,
            fm_index,
            reverb_size,
            reverb_damp,
            reverb_bal,
        )
        atmosphere_patch.volume = volume
        rack.start("atmosphere", atmosphere_patch)

    enabled = Checkbox(value=False, description="atmosphere on/off")
    step_division = IntSlider(min=1, max=16, step=1, value=8, description="step_division")
    arp_root = FloatSlider(min=110, max=440, step=1, value=ARP_ROOT, description="arp_root")
    fm_ratio = FloatSlider(min=0.1, max=4, step=0.1, value=0.4, description="fm_ratio")
    fm_index = FloatSlider(min=0, max=10, step=0.1, value=3, description="fm_index")
    reverb_size = FloatSlider(min=0, max=1, step=0.05, value=0.25, description="reverb_size")
    reverb_damp = FloatSlider(min=0, max=1, step=0.05, value=0.15, description="reverb_damp")
    reverb_bal = FloatSlider(min=0, max=1, step=0.05, value=0.1, description="reverb_bal")
    volume = FloatSlider(min=0, max=2, step=0.1, value=0.6, description="volume")

    controls = {
        "enabled": enabled,
        "step_division": step_division,
        "arp_root": arp_root,
        "fm_ratio": fm_ratio,
        "fm_index": fm_index,
        "reverb_size": reverb_size,
        "reverb_damp": reverb_damp,
        "reverb_bal": reverb_bal,
        "volume": volume,
    }
    if controller is not None:
        controller.register(
            "atmosphere",
            controls,
            lambda: set_params(**{name: widget.value for name, widget in controls.items()}),
        )

    output = interactive_output(
        set_params,
        controls,
    )
    slider_rows = [
        HBox(
            [
                step_division,
                HTML("How often the arpeggio advances, in 16th notes - larger is slower."),
            ]
        ),
        HBox([arp_root, HTML("Base frequency of the arpeggio's root note.")]),
        HBox(
            [
                fm_ratio,
                HTML(
                    "Modulator/carrier ratio in the FM voice - controls harmonic versus dissonant tone."
                ),
            ]
        ),
        HBox([fm_index, HTML("FM modulation depth - higher is brighter and buzzier.")]),
        HBox([reverb_size, HTML("Reverb room size - larger is bigger and more distant.")]),
        HBox([reverb_damp, HTML("Reverb high-frequency damping - higher is darker.")]),
        HBox([reverb_bal, HTML("Reverb dry/wet balance - 0 is dry and 1 is wet.")]),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
    """
