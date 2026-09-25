# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.generative.generative
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, ClassVar

from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv, TrigFunc

from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.utility.notes import notes

# major pentatonic across one octave - consonant, calm, no leading tones
GENERATIVE_SCALE = [0, 2, 4, 7, 9, 12]

MID_ROOT = notes.E4  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A2,
        notes.E5,
        1,
        MID_ROOT,
        "Register",
        "Shifts the generated melody up or down in pitch.",
        (PyoParamRef(FM, "carrier"),),
        scale="note",
    ),
    SliderSpec(
        "note_period",
        1,
        12,
        0.5,
        4.5,
        "Pace",
        "How often a new note is drawn; shorter feels more active, longer spaces the melody out.",
        (),
    ),
    SliderSpec(
        "note_duration",
        0.5,
        10,
        0.5,
        3.5,
        "Note length",
        "Shapes how long each note rings out; shorter feels more plucked and articulate, longer lets notes overlap into a smoother, sustained texture.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "fm_ratio",
        0.5,
        4,
        0.1,
        1.5,
        "Tone character",
        "Detunes the melodic overtones; near a simple ratio sounds clean and bell-like, drifting away adds a warmer, more unstable shimmer.",
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
        0.45,
        "Distance",
        "Blends how much of the melody is heard through the reverb versus dry; higher dissolves it into the atmosphere, lower keeps it present.",
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


VOLUME_DEFAULT = 0.6


class Generative(Patch):
    """Free-running generative melody: a new pentatonic note is drawn at random every `note_period` seconds, in real time rather than locked to the shared clock.

    Closer to Eno's tape-loop style generative ambient than a fixed
    arpeggio - notes never repeat in a predictable order, and because the
    period is measured in real seconds (not the shared `Clock`), this voice
    drifts in and out of phase with every other patch instead of locking to
    a downbeat. `note_period`/`note_duration` are `rebuild_parameters`:
    each is baked into a `Metro`'s fixed `time` or a `TrigEnv`'s `dur` at
    build time, so changing either live can't just update an existing
    control.
    """

    name = "mid_generative"
    title = "Mid - generative melody"
    summary = "Ever-changing generative melody that never quite repeats."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    rebuild_parameters: ClassVar[tuple[str, ...]] = ("note_period", "note_duration")

    root_freq: float
    note_period: float
    note_duration: float
    fm_ratio: float
    fm_index: float
    reverb_size: float
    reverb_damp: float
    reverb_bal: float

    def build(self, **values: Any) -> Patch:
        self.configure(**values)
        root_freq = self.root_freq
        note_metro = Metro(time=self.note_period)

        envelope_table = CosTable([(0, 0), (800, 1), (4000, 0.5), (8191, 0)])
        note_env = TrigEnv(note_metro, table=envelope_table, dur=self.note_duration, mul=0.18)

        fm_voice = FM(carrier=root_freq, ratio=self.fm_ratio, index=self.fm_index, mul=note_env)
        voice = Freeverb(fm_voice, size=self.reverb_size, damp=self.reverb_damp, bal=self.reverb_bal)

        def next_note() -> None:
            interval = random.choice(GENERATIVE_SCALE)
            fm_voice.carrier = root_freq * pow(2, interval / 12)

        note_func = TrigFunc(note_metro, next_note)
        self.sequencer = _Generative(metro=note_metro, keepalive=[envelope_table, note_env, note_func])
        self.voice = voice
        self.controls = {
            "root_freq": lambda value: setattr(fm_voice, "carrier", value),
            "fm_ratio": lambda value: setattr(fm_voice, "ratio", value),
            "fm_index": lambda value: setattr(fm_voice, "index", value),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        }
        self.resources = [note_metro, envelope_table, note_env, fm_voice, note_func]
        return self
