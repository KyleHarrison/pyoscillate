# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.canon.canon
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, ClassVar

from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv, TrigFunc

from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes

# major pentatonic across one octave - consonant, calm, no leading tones
CANON_SCALE = [0, 2, 4, 7, 9, 12]

CANON_ROOT = notes.A3  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A2,
        notes.A4,
        1,
        CANON_ROOT,
        "Register",
        "Shifts voice A's melody up or down in pitch; voice B follows at its own interval offset.",
        scale="note",
    ),
    SliderSpec(
        "voice_a_period",
        1,
        12,
        0.5,
        5.0,
        "Voice A pace",
        "How often voice A draws a new note; shorter feels more active, longer spaces it out.",
    ),
    SliderSpec(
        "voice_b_period",
        1,
        12,
        0.5,
        7.5,
        "Voice B pace",
        "How often voice B draws a new note; set apart from voice A's pace so the two drift in and out of alignment.",
    ),
    SliderSpec(
        "voice_b_interval",
        0,
        12,
        1,
        7,
        "Voice separation",
        "Sets voice B's pitch offset from voice A; wider intervals separate the two voices more clearly, narrower blends them together.",
    ),
    SliderSpec(
        "note_duration",
        0.5,
        10,
        0.5,
        4.0,
        "Note length",
        "Shapes how long each note rings out; shorter feels more plucked and articulate, longer lets notes overlap into a smoother, sustained texture.",
    ),
    SliderSpec(
        "fm_ratio",
        0.5,
        4,
        0.1,
        1.5,
        "Tone character",
        "Detunes the melodic overtones; near a simple ratio sounds clean and bell-like, drifting away adds a warmer, more unstable shimmer.",
    ),
    SliderSpec(
        "fm_index",
        0,
        6,
        0.1,
        1.5,
        "Brightness",
        "Moves the melody from a plain, mellow tone to a brighter, buzzier, more harmonically complex one.",
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.7,
        "Space",
        "Sets how large and distant the canon's room feels, from a tight presence to a huge, cavernous decay.",
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.5,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower settings stay bright and shimmering.",
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.5,
        "Distance",
        "Blends how much of the canon is heard through the reverb versus dry; higher dissolves it into the atmosphere, lower keeps it present.",
    ),
)


@dataclass(eq=False)
class _Duet:
    """Wraps the two independently-timed, free-running `Metro`s driving each
    voice's note changes, plus strong references to their `TrigFunc`
    callbacks - see `clock_tick.py`'s `_Clocks` docstring for why this
    keepalive matters alongside another `Pattern`-driven callback.
    """

    metros: list[Metro]
    keepalive: list[Any] = field(default_factory=list)

    def play(self) -> None:
        for metro in self.metros:
            metro.play()

    def stop(self) -> None:
        for metro in self.metros:
            metro.stop()


VOLUME_DEFAULT = 0.6


class Canon(Patch):
    """Two-voice generative canon: a pair of melodic voices, each drawing random pentatonic notes on
    its own free-running period, so they drift in and out of alignment like an ever-shifting call and
    response.

    Both voices draw from the same scale, so they always stay consonant
    with each other, but their unrelated (non-integer-ratio) periods mean
    they rarely repeat the same relationship to one another - the "canon"
    quality comes from that drift, not from one voice literally echoing
    the other. `voice_a_period`/`voice_b_period`/`voice_b_interval`/
    `note_duration` are all `rebuild_parameters`: each is baked into a
    `Metro`'s fixed `time` or a `TrigEnv`'s `dur` at build time, so changing
    any of them live can't just update an existing control.
    """

    name = "mid_canon"
    title = "Mid - two-voice canon"
    summary = "Two melodic voices in a slow-shifting call and response."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    rebuild_parameters: ClassVar[tuple[str, ...]] = (
        "voice_a_period",
        "voice_b_period",
        "voice_b_interval",
        "note_duration",
    )

    root_freq: float
    voice_a_period: float
    voice_b_period: float
    voice_b_interval: float
    note_duration: float
    fm_ratio: float
    fm_index: float
    reverb_size: float
    reverb_damp: float
    reverb_bal: float

    def build(self, **values: Any) -> Patch:
        self.configure(**values)
        root_freq = self.root_freq
        envelope_table = CosTable([(0, 0), (800, 1), (4000, 0.5), (8191, 0)])

        voice_a_metro = Metro(time=self.voice_a_period)
        voice_a_env = TrigEnv(voice_a_metro, table=envelope_table, dur=self.note_duration, mul=0.18)
        voice_a_fm = FM(
            carrier=root_freq, ratio=self.fm_ratio, index=self.fm_index, mul=voice_a_env
        )

        voice_b_root = root_freq * pow(2, self.voice_b_interval / 12)
        voice_b_metro = Metro(time=self.voice_b_period)
        voice_b_env = TrigEnv(voice_b_metro, table=envelope_table, dur=self.note_duration, mul=0.14)
        voice_b_fm = FM(
            carrier=voice_b_root, ratio=self.fm_ratio, index=self.fm_index, mul=voice_b_env
        )

        source = voice_a_fm + voice_b_fm
        voice = Freeverb(source, size=self.reverb_size, damp=self.reverb_damp, bal=self.reverb_bal)

        def next_voice_a() -> None:
            interval = random.choice(CANON_SCALE)
            voice_a_fm.carrier = root_freq * pow(2, interval / 12)

        def next_voice_b() -> None:
            interval = random.choice(CANON_SCALE)
            voice_b_fm.carrier = voice_b_root * pow(2, interval / 12)

        voice_a_func = TrigFunc(voice_a_metro, next_voice_a)
        voice_b_func = TrigFunc(voice_b_metro, next_voice_b)

        self.sequencer = _Duet(
            metros=[voice_a_metro, voice_b_metro],
            keepalive=[
                envelope_table,
                voice_a_env,
                voice_b_env,
                voice_a_func,
                voice_b_func,
            ],
        )
        self.voice = voice
        self.controls = {
            "root_freq": lambda value: setattr(voice_a_fm, "carrier", value),
            "fm_ratio": lambda value: (
                setattr(voice_a_fm, "ratio", value),
                setattr(voice_b_fm, "ratio", value),
            ),
            "fm_index": lambda value: (
                setattr(voice_a_fm, "index", value),
                setattr(voice_b_fm, "index", value),
            ),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        }
        self.resources = [
            envelope_table,
            voice_a_metro,
            voice_a_env,
            voice_a_fm,
            voice_b_metro,
            voice_b_env,
            voice_b_fm,
            source,
            voice_a_func,
            voice_b_func,
        ]
        return self
