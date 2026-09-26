# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.generative.generative
"""A single free-running FM voice: a Metro restarts its note envelope on its
own real-seconds period, and each restart draws a new pentatonic interval at
random, so the melody never resolves into a repeating pattern.
"""

from __future__ import annotations

import random
from typing import ClassVar

from pyo import PyoObject
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv, TrigFunc

from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes

# major pentatonic across one octave - consonant, calm, no leading tones
GENERATIVE_SCALE = [0, 2, 4, 7, 9, 12]

MID_ROOT = notes.E4  # current default


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
    volume_default = 0.6
    rebuild_parameters: ClassVar[tuple[str, ...]] = ("note_period", "note_duration")

    # note envelope: a fast rise then a longer, slightly uneven decay
    ENVELOPE_POINTS: ClassVar[list[tuple[int, float]]] = [(0, 0), (800, 1), (4000, 0.5), (8191, 0)]
    NOTE_LEVEL: ClassVar[float] = 0.18

    envelope_table: CosTable
    note_metro: Metro
    note_env: TrigEnv
    fm_voice: FM
    reverb: Freeverb
    note_func: TrigFunc

    @Param(
        notes.A2,
        notes.E5,
        1,
        MID_ROOT,
        "Register",
        "Shifts the generated melody up or down in pitch.",
        scale="note",
    )
    def root_freq(self, value: float) -> None:
        self.fm_voice.carrier = value

    note_period = Param(
        1,
        12,
        0.5,
        4.5,
        "Pace",
        "How often a new note is drawn; shorter feels more active, longer spaces the melody out.",
    )

    note_duration = Param(
        0.5,
        10,
        0.5,
        3.5,
        "Note length",
        "Shapes how long each note rings out; shorter feels more plucked and articulate, longer lets "
        "notes overlap into a smoother, sustained texture.",
    )

    @Param(
        0.5,
        4,
        0.1,
        1.5,
        "Tone character",
        "Detunes the melodic overtones; near a simple ratio sounds clean and bell-like, drifting away "
        "adds a warmer, more unstable shimmer.",
    )
    def fm_ratio(self, value: float) -> None:
        self.fm_voice.ratio = value

    @Param(
        0,
        6,
        0.1,
        1.5,
        "Brightness",
        "Moves the melody from a plain, mellow tone to a brighter, buzzier, more harmonically complex "
        "one.",
    )
    def fm_index(self, value: float) -> None:
        self.fm_voice.index = value

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Space",
        "Sets how large and distant the melody's room feels, from a tight presence to a huge, cavernous "
        "decay.",
    )
    def reverb_size(self, value: float) -> None:
        self.reverb.size = value

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower "
        "settings stay bright and shimmering.",
    )
    def reverb_damp(self, value: float) -> None:
        self.reverb.damp = value

    @Param(
        0,
        1,
        0.05,
        0.45,
        "Distance",
        "Blends how much of the melody is heard through the reverb versus dry; higher dissolves it into "
        "the atmosphere, lower keeps it present.",
    )
    def reverb_bal(self, value: float) -> None:
        self.reverb.bal = value

    def finish(self, voice: PyoObject) -> Patch:
        """Minimal `finish()` for a musical-structure patch that owns its own
        `Metro` sequencer instead of a `GatedVoice`/`ContinuousVoice` one:
        retain every node stored on `self` and run every `Param` control
        once, same as those bases' own `finish()`."""
        self.voice = voice
        self._bind()
        return self

    def build(self) -> Patch:
        self._reset()

        self.note_metro = Metro(time=self.note_period)

        self.envelope_table = CosTable(self.ENVELOPE_POINTS)
        self.note_env = TrigEnv(
            self.note_metro, table=self.envelope_table, dur=self.note_duration, mul=self.NOTE_LEVEL
        )

        self.fm_voice = FM(mul=self.note_env)
        self.reverb = Freeverb(self.fm_voice)

        def next_note() -> None:
            interval = random.choice(GENERATIVE_SCALE)
            self.fm_voice.carrier = self.root_freq * pow(2, interval / 12)

        self.note_func = TrigFunc(self.note_metro, next_note)
        self.sequencer = self.note_metro
        return self.finish(self.reverb)
