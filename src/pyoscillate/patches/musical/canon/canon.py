# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.canon.canon
"""Two independent, free-running FM voices, each restarting its own note on
its own Metro period and drawing a new pentatonic interval at random. The
two periods share no common ratio, so the pair drifts in and out of
alignment instead of locking into a fixed round; a shared reverb glues the
two voices into one space.
"""

from __future__ import annotations

import random
from typing import ClassVar

from pyo import PyoObject
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv, TrigFunc

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import SequencerGroup
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes

# major pentatonic across one octave - consonant, calm, no leading tones
CANON_SCALE = [0, 2, 4, 7, 9, 12]

CANON_ROOT = notes.A3  # current default


class Canon(Patch):
    """Two-voice generative canon: a pair of melodic voices, each drawing random pentatonic notes on
    its own free-running period, so they drift in and out of alignment like an ever-shifting call and
    response.

    Both voices draw from the same scale, so they always stay consonant
    with each other, but their unrelated (non-integer-ratio) periods mean
    they rarely repeat the same relationship to one another - the "canon"
    quality comes from that drift, not from one voice literally echoing
    the other. `voice_a_period`/`voice_b_period`/`voice_b_interval`/
    `note_duration` are all `rebuild` parameters: each is baked into a
    `Metro`'s fixed `time` or a `TrigEnv`'s `dur` at build time, so changing
    any of them live can't just update an existing control.
    """

    name = "mid_canon"
    title = "Mid - two-voice canon"
    summary = "Two melodic voices in a slow-shifting call and response."
    volume = Patch.volume.replace(default=0.6)

    # shared note envelope: a fast rise then a longer, slightly uneven decay
    ENVELOPE_POINTS: ClassVar[list[tuple[int, float]]] = [
        (0, 0),
        (800, 1),
        (4000, 0.5),
        (8191, 0),
    ]
    # each voice's fixed level, so voice A sits a touch forward of voice B
    VOICE_A_LEVEL: ClassVar[float] = 0.18
    VOICE_B_LEVEL: ClassVar[float] = 0.14

    # voice B's root at build time (root_freq shifted by voice_b_interval);
    # only recomputed on rebuild, so a live root_freq change doesn't retune
    # voice B's random draws until the patch next rebuilds
    voice_b_root: float

    envelope_table: CosTable
    voice_a_metro: Metro
    voice_a_env: TrigEnv
    voice_a_fm: FM
    voice_b_metro: Metro
    voice_b_env: TrigEnv
    voice_b_fm: FM
    source: PyoObject
    reverb: Freeverb
    voice_a_func: TrigFunc
    voice_b_func: TrigFunc

    @Param(
        notes.A2,
        notes.A4,
        1,
        CANON_ROOT,
        "Register",
        "Shifts voice A's melody up or down in pitch; voice B follows at its own interval offset.",
        scale="note",
    )
    def root_freq(self, value: float) -> None:
        self.voice_a_fm.carrier = value

    voice_a_period = Param(
        1,
        12,
        0.5,
        5.0,
        "Voice A pace",
        "How often voice A draws a new note; shorter feels more active, longer spaces it out.",
        rebuild=True,
    )

    voice_b_period = Param(
        1,
        12,
        0.5,
        7.5,
        "Voice B pace",
        "How often voice B draws a new note; set apart from voice A's pace so the two drift in and out "
        "of alignment.",
        rebuild=True,
    )

    voice_b_interval = Param(
        0,
        12,
        1,
        7,
        "Voice separation",
        "Sets voice B's pitch offset from voice A; wider intervals separate the two voices more clearly, "
        "narrower blends them together.",
        rebuild=True,
    )

    note_duration = Param(
        0.5,
        10,
        0.5,
        4.0,
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
    )
    def fm_ratio(self, value: float) -> None:
        self.voice_a_fm.ratio = value
        self.voice_b_fm.ratio = value

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
        self.voice_a_fm.index = value
        self.voice_b_fm.index = value

    @Param(
        0,
        1,
        0.05,
        0.7,
        "Space",
        "Sets how large and distant the canon's room feels, from a tight presence to a huge, cavernous "
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
        0.5,
        "Distance",
        "Blends how much of the canon is heard through the reverb versus dry; higher dissolves it into "
        "the atmosphere, lower keeps it present.",
    )
    def reverb_bal(self, value: float) -> None:
        self.reverb.bal = value

    def finish(self, voice: PyoObject) -> Patch:
        """Minimal `finish()` for a musical-structure patch that owns its own
        multi-`Metro` sequencer instead of a `GatedVoice`/`ContinuousVoice`
        one: retain every node stored on `self` and run every `Param`
        control once, same as those bases' own `finish()`."""
        self.voice = voice
        self._bind()
        return self

    def build(self, context: BuildContext) -> Patch:
        self._reset()

        self.envelope_table = CosTable(self.ENVELOPE_POINTS)

        self.voice_a_metro = Metro(time=self.voice_a_period)
        self.voice_a_env = TrigEnv(
            self.voice_a_metro,
            table=self.envelope_table,
            dur=self.note_duration,
            mul=self.VOICE_A_LEVEL,
        )
        self.voice_a_fm = FM(mul=self.voice_a_env)

        self.voice_b_root = self.root_freq * pow(2, self.voice_b_interval / 12)
        self.voice_b_metro = Metro(time=self.voice_b_period)
        self.voice_b_env = TrigEnv(
            self.voice_b_metro,
            table=self.envelope_table,
            dur=self.note_duration,
            mul=self.VOICE_B_LEVEL,
        )
        self.voice_b_fm = FM(carrier=self.voice_b_root, mul=self.voice_b_env)

        self.source = self.voice_a_fm + self.voice_b_fm
        self.reverb = Freeverb(self.source)

        self.voice_a_func = TrigFunc(self.voice_a_metro, self.next_voice_a)
        self.voice_b_func = TrigFunc(self.voice_b_metro, self.next_voice_b)

        self.sequencer = SequencerGroup(
            sequencers=(self.voice_a_metro, self.voice_b_metro)
        )
        return self.finish(self.reverb)

    def next_voice_a(self) -> None:
        interval = random.choice(CANON_SCALE)
        self.voice_a_fm.carrier = self.root_freq * pow(2, interval / 12)

    def next_voice_b(self) -> None:
        interval = random.choice(CANON_SCALE)
        self.voice_b_fm.carrier = self.voice_b_root * pow(2, interval / 12)
