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
        "Register",
        "Shifts the arpeggio up or down in pitch; higher settles brighter and clear of the bass, lower pulls it toward a darker, more muddied register.",
        (PyoParamRef(FM, "carrier"),),
    ),
    SliderSpec(
        "step_division",
        1,
        16,
        1,
        8,
        "Speed",
        "Sets how quickly the arpeggio steps; lower values race by breathlessly, higher values stretch it into a slower, more spacious pattern.",
        (),
    ),
    SliderSpec(
        "fm_ratio",
        0.1,
        4,
        0.1,
        0.4,
        "Tone character",
        "Detunes the pad's overtones; near a simple ratio sounds clean and bell-like, drifting away adds a warm, unstable, slightly dissonant shimmer.",
        (PyoParamRef(FM, "ratio"),),
    ),
    SliderSpec(
        "fm_index",
        0,
        10,
        0.1,
        3,
        "Brightness",
        "Moves the pad from a plain, mellow tone to a brighter, buzzier, more harmonically complex one.",
        (PyoParamRef(FM, "index"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.25,
        "Space",
        "Sets how large and distant the pad's room feels, from a tight close ambience to a huge, cavernous decay.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.15,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower settings stay bright and shimmering.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.1,
        "Distance",
        "Blends how much of the pad is heard through the reverb versus dry; higher dissolves it into an atmospheric wash, lower keeps it present and up front.",
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
    arp_env = TrigEnv(arp_trig, table=envelope_table, dur=step_time * 1.2, mul=arp_swell, add=-0.3)

    # slow, detuned ratio for a warm, slightly unstable atmospheric tone
    fm_voice = FM(carrier=arp_root, ratio=fm_ratio, index=fm_index, mul=arp_env, add=-0.3)
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
        resources=(arp_trig, arp_swell, envelope_table, arp_env, fm_voice),
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
