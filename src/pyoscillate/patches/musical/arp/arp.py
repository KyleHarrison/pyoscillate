from __future__ import annotations

from ipywidgets import VBox
from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM

from pyoscillate.clock import BAR, Clock
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

# major pentatonic - consonant, calm, no leading tones to create tension
MID_INTERVALS = [0, 2, 4, 7, 9, 12, 9, 7, 4, 2]

MID_ROOT = 330  # E4, current notebook default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        110,
        660,
        1,
        MID_ROOT,
        "Register",
        "Shifts the melody up or down in pitch relative to the pads and bass beneath it.",
        (PyoParamRef(FM, "carrier"),),
    ),
    SliderSpec(
        "step_bars",
        1,
        8,
        1,
        2,
        "Pace",
        "Sets how often the melody moves; fewer bars feels more active, more bars stretches it into a slower, more spacious unfolding.",
        (),
    ),
    SliderSpec(
        "fm_ratio",
        0.5,
        4,
        0.1,
        1.5,
        "Tone character",
        "Detunes the melody's overtones; near a simple ratio sounds clean and bell-like, drifting away adds a warmer, more unstable shimmer.",
        (PyoParamRef(FM, "ratio"),),
    ),
    SliderSpec(
        "fm_index",
        0,
        6,
        0.1,
        1.5,
        "Brightness",
        "Moves the melody from a plain, mellow tone to a brighter, buzzier, more harmonically complex one.",
        (PyoParamRef(FM, "index"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.6,
        "Space",
        "Sets how large and distant the melody's room feels, from a tight presence to a huge, cavernous decay.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.5,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower settings stay bright and shimmering.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.4,
        "Distance",
        "Blends how much of the melody is heard through the reverb versus dry; higher dissolves it into the atmosphere, lower keeps it present and up front.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
)


def build(
    tempo: Tempo,
    clock: Clock,
    root_freq: float = MID_ROOT,
    step_bars: int = 2,
    fm_ratio: float = 1.5,
    fm_index: float = 1.5,
    reverb_size: float = 0.6,
    reverb_damp: float = 0.5,
    reverb_bal: float = 0.4,
) -> Patch:
    """Slow, fixed pentatonic arpeggio locked to the shared clock, gliding between notes rather than plucking them.

    Args:
        tempo: Shared tempo grid; unused directly here beyond being passed
            through to `clock`, but kept in the signature to match every
            other clocked patch's `build(tempo, clock, ...)` shape.
        clock: Shared master pulse; the melody steps every `step_bars`
            bars, phase-locked to every other patch on the clock.
        root_freq: Base frequency (Hz) of the melody's root note, before
            the `MID_INTERVALS` offsets are applied each step. Raising it
            brings the melody closer to a lead register and easier to pick
            out; lowering it moves it toward the drone/atmosphere register
            and lets it blend in more as a background element.
        step_bars: How many bars pass between melody notes. Larger values
            space the notes further apart for a calmer, more spacious
            melody; smaller values make it read as more active and
            foreground.
        fm_ratio: Modulator/carrier ratio in the FM voice. Values close to a
            simple ratio (1, 1.5, 2) sound clean and bell-like; the default
            gives a calm, consonant timbre appropriate for a background
            mid voice.
        fm_index: FM modulation index - how bright/buzzy the timbre is.
            Kept low by default so the voice stays soft and rounded rather
            than cutting through the mix.
        reverb_size: Freeverb room size (0-1). Moderate by default - present
            enough to sit clearly in the stereo field without dissolving
            into the background as much as the drone/soundscape layers do.
        reverb_damp: Freeverb high-frequency damping (0-1).
        reverb_bal: Freeverb dry/wet balance (0-1). Lower than the
            soundscape patches by default, so the melodic line stays
            legible rather than fully diffused.
    """
    step_time = tempo.bar * step_bars

    # glides to each new note over most of the step time instead of snapping,
    # so the melody drifts between pitches rather than plucking them
    mid_freq = SigTo(value=root_freq, time=step_time * 0.85)

    fm_voice = FM(carrier=mid_freq, ratio=fm_ratio, index=fm_index, mul=0.18)
    voice = Freeverb(fm_voice, size=reverb_size, damp=reverb_damp, bal=reverb_bal)

    step = {"i": 0}

    def next_step() -> None:
        i = step["i"] % len(MID_INTERVALS)
        mid_freq.value = root_freq * pow(2, MID_INTERVALS[i] / 12)
        step["i"] += 1

    sequencer = clock.subscribe(BAR * step_bars, next_step)
    return Patch(
        sequencer=sequencer,
        voice=voice,
        controls={
            "root_freq": lambda value: setattr(mid_freq, "value", value),
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
    """Create mid_arp controls."""
    return patch_widget(
        rack,
        "mid_arp",
        build,
        PARAMETERS,
        controller=controller,
        rebuild_parameters=("step_bars",),
        build_kwargs={"tempo": tempo, "clock": clock},
    )
