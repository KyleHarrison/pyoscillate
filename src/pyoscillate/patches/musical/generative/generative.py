# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.generative.generative
"""A single free-running FM voice: a Metro restarts its note envelope on its
own real-seconds period, and each restart draws a new pentatonic interval at
random, so the melody never resolves into a repeating pattern.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.generators import FM
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv, TrigFunc

from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Reverb, SeededDraws
from pyoscillate.patches.params import Param
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.scale import Scales

# major pentatonic across one octave - consonant, calm, no leading tones

MID_ROOT = Note.E4  # current default


class Generative(SeededDraws, Reverb, Patch):
    """Free-running generative melody: a new pentatonic note is drawn at random every `note_period` seconds, in real time rather than locked to the shared clock.

    Closer to Eno's tape-loop style generative ambient than a fixed
    arpeggio - notes never repeat in a predictable order, and because the
    period is measured in real seconds (not the shared `Clock`), this voice
    drifts in and out of phase with every other patch instead of locking to
    a downbeat. `note_period`/`note_duration` are `rebuild` parameters:
    each is baked into a `Metro`'s fixed `time` or a `TrigEnv`'s `dur` at
    build time, so changing either live can't just update an existing
    control.
    """

    name = "mid_generative"
    title = "Mid - generative melody"
    summary = "Ever-changing generative melody that never quite repeats."
    volume = Patch.volume.replace(default=0.6)

    # note envelope: a fast rise then a longer, slightly uneven decay
    ENVELOPE_POINTS: ClassVar[list[tuple[int, float]]] = [
        (0, 0),
        (800, 1),
        (4000, 0.5),
        (8191, 0),
    ]
    NOTE_LEVEL: ClassVar[float] = 0.18

    envelope_table: CosTable
    note_metro: Metro
    note_env: TrigEnv
    fm_voice: FM
    note_func: TrigFunc
    harmony: Harmony

    @Param(
        Note.A2,
        Note.E5,
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
        rebuild=True,
    )

    note_duration = Param(
        0.5,
        10,
        0.5,
        3.5,
        "Note length",
        "Shapes how long each note rings out; shorter feels more plucked and articulate, longer lets "
        "notes overlap into a smoother, sustained texture.",
        rebuild=True,
    )

    @Param(
        0.5,
        4,
        0.1,
        1.5,
        "Tone character",
        "Detunes the melodic overtones; near a simple ratio sounds clean and bell-like, drifting away "
        "adds a warmer, more unstable shimmer.",
        sweep=True,
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
        sweep=True,
    )
    def fm_index(self, value: float) -> None:
        self.fm_voice.index = value

    reverb_bal = Reverb.reverb_bal.replace(default=0.45)

    def finish(self, voice: PyoObject) -> Patch:
        """Minimal `finish()` for a musical-structure patch that owns its own
        `Metro` sequencer instead of a `GatedVoice`/`ContinuousVoice` one:
        retain every node stored on `self` and run every `Param` control
        once, same as those bases' own `finish()`."""
        self.voice = voice
        self._bind()
        return self

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony

        self.note_metro = Metro(time=self.note_period)

        self.envelope_table = CosTable(self.ENVELOPE_POINTS)
        self.note_env = TrigEnv(
            self.note_metro,
            table=self.envelope_table,
            dur=self.note_duration,
            mul=self.NOTE_LEVEL,
        )

        self.fm_voice = FM(mul=self.note_env)
        self.reverb = self.add_reverb(self.fm_voice)

        self.note_func = TrigFunc(self.note_metro, self.next_note)
        self.sequencer = self.note_metro
        return self.finish(self.reverb)

    def next_note(self) -> None:
        interval = self.draws.choice(Scales.MAJOR_PENTATONIC_OCTAVE.offsets)
        self.fm_voice.carrier = self.harmony.quantise(
            self.root_freq * pow(2, interval / 12)
        )
