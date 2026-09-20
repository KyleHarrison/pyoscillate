from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from ipywidgets import VBox
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv, TrigFunc

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget

# major pentatonic across one octave - consonant, calm, no leading tones
GENERATIVE_SCALE = [0, 2, 4, 7, 9, 12]

MID_ROOT = 330  # E4, current notebook default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        110,
        660,
        1,
        MID_ROOT,
        "Root frequency",
        "Generated melody root.",
        (PyoParamRef(FM, "carrier"),),
    ),
    SliderSpec(
        "note_period",
        1,
        12,
        0.5,
        4.5,
        "Note period",
        "Seconds between notes; changing it rebuilds the Metro.",
        (),
    ),
    SliderSpec(
        "note_duration",
        0.5,
        10,
        0.5,
        3.5,
        "Note duration",
        "Envelope duration; changing it rebuilds the envelope.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "fm_ratio",
        0.5,
        4,
        0.1,
        1.5,
        "FM ratio",
        "Carrier/modulator ratio.",
        (PyoParamRef(FM, "ratio"),),
    ),
    SliderSpec(
        "fm_index",
        0,
        6,
        0.1,
        1.5,
        "FM index",
        "FM brightness.",
        (PyoParamRef(FM, "index"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.6,
        "Reverb size",
        "Room size.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.5,
        "Reverb damping",
        "Damping.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.45,
        "Reverb balance",
        "Dry/wet balance.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
)


@dataclass(eq=False)
class _Generative:
    """Wraps the free-running `Metro` driving note changes, plus a strong
    reference to the `TrigFunc` that picks each new note - see
    `clock_tick.py`'s `_Clocks` docstring for why keeping these references
    around explicitly (not just relying on the summed voice chain) matters
    alongside another `Pattern`-driven callback in the same process.
    """

    metro: Metro
    keepalive: list[Any] = field(default_factory=list)

    def play(self) -> None:
        self.metro.play()

    def stop(self) -> None:
        self.metro.stop()


def build(
    root_freq: float = MID_ROOT,
    note_period: float = 4.5,
    note_duration: float = 3.5,
    fm_ratio: float = 1.5,
    fm_index: float = 1.5,
    reverb_size: float = 0.6,
    reverb_damp: float = 0.5,
    reverb_bal: float = 0.45,
) -> Patch:
    """Free-running generative melody: a new pentatonic note is drawn at random every `note_period` seconds, in real time rather than locked to the shared clock.

    Closer to Eno's tape-loop style generative ambient than a fixed
    arpeggio - notes never repeat in a predictable order, and because the
    period is measured in real seconds (not the shared `Clock`), this voice
    drifts in and out of phase with every other patch instead of locking to
    a downbeat.

    Args:
        root_freq: Base frequency (Hz) the drawn intervals are applied to.
            Raising it brings the melody closer to a lead register;
            lowering it moves it toward the atmosphere/drone register.
        note_period: Seconds between each new random note draw. Larger
            values space notes further apart for a calmer, sparser melody;
            smaller values make it read as more active.
        note_duration: How long each note's envelope sustains, in seconds.
            Longer than `note_period` lets notes overlap into each other
            for a smoother, more legato feel; shorter values give each note
            more separation.
        fm_ratio: Modulator/carrier ratio in the FM voice. Values close to a
            simple ratio (1, 1.5, 2) sound clean and bell-like.
        fm_index: FM modulation index - how bright/buzzy the timbre is.
            Kept low by default so the voice stays soft and rounded.
        reverb_size: Freeverb room size (0-1).
        reverb_damp: Freeverb high-frequency damping (0-1).
        reverb_bal: Freeverb dry/wet balance (0-1). Lower than the
            soundscape patches by default, so the melodic line stays
            legible rather than fully diffused.
    """
    note_metro = Metro(time=note_period)

    envelope_table = CosTable([(0, 0), (800, 1), (4000, 0.5), (8191, 0)])
    note_env = TrigEnv(note_metro, table=envelope_table, dur=note_duration, mul=0.18)

    fm_voice = FM(carrier=root_freq, ratio=fm_ratio, index=fm_index, mul=note_env)
    voice = Freeverb(fm_voice, size=reverb_size, damp=reverb_damp, bal=reverb_bal)

    def next_note() -> None:
        interval = random.choice(GENERATIVE_SCALE)
        fm_voice.carrier = root_freq * pow(2, interval / 12)

    note_func = TrigFunc(note_metro, next_note)
    sequencer = _Generative(metro=note_metro, keepalive=[envelope_table, note_env, note_func])
    return Patch(
        sequencer=sequencer,
        voice=voice,
        controls={
            "root_freq": lambda value: setattr(fm_voice, "carrier", value),
            "fm_ratio": lambda value: setattr(fm_voice, "ratio", value),
            "fm_index": lambda value: setattr(fm_voice, "index", value),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        },
    )


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create mid_generative controls."""
    return patch_widget(
        rack,
        "mid_generative",
        build,
        PARAMETERS,
        controller=controller,
        rebuild_parameters=("note_period", "note_duration"),
    )
