# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.fm.fm
#   style: bark | grit
"""FM bass: every note barks bright, then settles to a rounder tone.

The index follows a break-point table (pyo example x10/01's index
`LinTable` 20 → 10 → 0, scaled to 1 → 0.5 → 0) read over Settle seconds, on
top of a steady Edge floor. Accented steps scale the bark as well as the
level, so the groove's accents hit harder and brighter. That is the FM
equivalent of velocity opening the index.

- `bark` (`FmBassBark`): two-operator FM (x03/03 `FM`) at integer ratio 1, so
  the spectrum stays harmonic and the note keeps a clear pitch at any index.
- `grit` (`FmBassGrit`): `CrossFM` (x03/03) at ratio 2. The carrier modulates
  the modulator back, which roughens the bark into a buzzier, less stable
  edge.

The note line is the `rolling` groove melody by default, on the shared clock. Both
styles share the `FmBass` base below; only the operator pair built in
`tone()` differs, since that is genuinely different behavior, not just
different profile data (`patches/AGENTS.md`'s design rule 1).
"""

from __future__ import annotations

from typing import Any

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.filters import ButHP
from pyo.lib.generators import FM, CrossFM
from pyo.lib.tables import CosTable, LinTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import RootPitch
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.tonal.bass.base import Bass
from pyoscillate.tempo import Tempo
from pyoscillate.theory.pitch import Note

STYLES = ("bark", "grit")
BASE_DIVISION = NoteDivision.SIXTEENTH

# x10/01's index break-points, normalised: a fast drop to half, then a
# linear fall to nothing over the rest of Settle
INDEX_POINTS = [(0, 1.0), (512, 0.5), (8191, 0.0)]
# the bass core's amplitude shape: a quick rise, a held body, then the release
AMP_POINTS = [(0, 0.0), (80, 1.0), (2100, 0.5), (8191, 0.0)]
# `grit`: how strongly the carrier modulates the modulator back, relative to
# the main index
CROSS = 0.5
# FM keeps a constant amplitude whatever the index, so the peak is GAIN x
# accent x volume before the subsonic high-pass, whose phase shift adds up to
# ~25% to the crest at the lowest Register
GAIN = 0.3
# under the lowest Register (30 Hz), which loses under 1 dB to it
SUBSONIC = 20


class FmBass(RootPitch, Bass):
    """FM bass base: every note barks bright, then settles to a rounder
    tone. Style variants subclass this and override `tone()` for FM vs.
    CrossFM; the rest of the graph is identical. See the module docstring
    for the sonic detail."""

    volume = Patch.volume.replace(default=0.42)

    # the graph, assigned by build(); finish() retains every one of them
    index_table: LinTable
    amp_table: CosTable
    bark: TrigEnv
    floor: SigTo
    index: PyoObject
    amp: TrigEnv
    level: PyoObject
    tone_signal: PyoObject
    body: ButHP

    # the live tempo and current step accent `next_step` and the
    # `growl`/`length` controls read, assigned by build()
    _tempo: Tempo
    _accent: float

    # read live off `self.root_freq` by build()'s trigger-time callback - no
    # control body needed, see `patches/AGENTS.md`'s note on a parameter
    # only read by a sequencer callback
    root_freq = RootPitch.root_freq.replace(
        minimum=Note.B0,
        maximum=Note.A2,
        default=Note.A1,
        help_text="Moves the bassline up or down; low sits under the kick as weight, high brings the bark forward as a melodic line.",
    )

    # whole steps only: an integer ratio keeps every note pitched (see AGENTS.md)
    @Param(
        1,
        4,
        1,
        1,
        "Hollow",
        "Which harmonics the bark carries: 1 is a full, saw-like buzz, 2 a hollower, square-like "
        "one, higher thins it toward a nasal, reedy edge. The note keeps its pitch throughout.",
        sweep=True,
    )
    def ratio(self, value: float) -> None:
        self.tone_signal.ratio = value

    @Param(
        0,
        12,
        0.5,
        6,
        "Growl",
        "How hard each note barks: low is a soft, round thump, high a bright, buzzing snarl at the "
        "start of every note.",
        sweep=True,
    )
    def growl(self, value: float) -> None:
        self.bark.mul = value * self._accent

    @Param(
        0.02,
        0.4,
        0.01,
        0.12,
        "Settle",
        "How long the bark takes to die down, in seconds: short is a quick pluck on the front of "
        "the note, long a slow, wah-like close.",
        sweep=True,
    )
    def settle(self, value: float) -> None:
        self.bark.dur = value

    @Param(
        0,
        3,
        0.1,
        0.5,
        "Edge",
        "The brightness left once the bark has settled: at 0 the note settles to a pure sub, "
        "higher keeps a buzzing edge under the whole note.",
        sweep=True,
    )
    def edge(self, value: float) -> None:
        self.floor.value = value

    @Param(
        0.3,
        1.5,
        0.05,
        0.9,
        "Length",
        "How long each note lasts, in 16ths: short is tight and staccato, long runs one note into "
        "the next.",
        sweep=True,
    )
    def length(self, value: float) -> None:
        self.amp.dur = self._tempo.sixteenth * value

    rate = rate_param(
        BASE_DIVISION,
        "Halves or doubles the bassline speed for each step away from its 16th-note grid.",
    )

    def tone(
        self, index: PyoObject, level: PyoObject
    ) -> tuple[PyoObject, tuple[Any, ...]]:
        """This style's FM operator pair, unfiltered, plus any extra Pyo
        objects it built for `build()` to retain. Overridden per style."""
        raise NotImplementedError

    def build(self, context: BuildContext) -> Patch:
        """Build an FM bassline whose index barks on each note."""
        self._reset()
        # matches the free `Trig()` this voice used before it was migrated
        # onto `Bass`'s trigger: silent until the clock ticks (see
        # tests/pyoscillate/patches/test_gated_patches.py)
        self.trigger.stop()
        self._tempo = context.tempo
        self._accent = 1.0

        self.pitch_signal(self.root_freq)
        self.index_table = LinTable(INDEX_POINTS)
        self.amp_table = CosTable(AMP_POINTS)
        self.bark = TrigEnv(
            self.trigger, self.index_table, dur=self.settle, mul=self.growl
        )
        self.floor = SigTo(value=self.edge, time=0.05, init=self.edge)
        self.index = self.bark + self.floor
        self.amp = TrigEnv(
            self.trigger, self.amp_table, dur=self._tempo.sixteenth * self.length
        )
        self.sync(
            context.tempo,
            lambda t: setattr(self.amp, "dur", t.sixteenth * self.length),
        )
        self.level = self.amp * GAIN

        self.tone_signal, tone_resources = self.tone(self.index, self.level)
        self.retain(*tone_resources)
        # at ratio 1 the first lower sideband lands on 0 Hz, so the bark carries a
        # DC offset that follows the index envelope: a subsonic thump that eats
        # headroom. CrossFM's feedback does the same at high index. A 2nd-order
        # high-pass below the lowest Register clears it; pyo's one-pole DCBlock
        # is too slow for an offset that moves within a few milliseconds.
        self.body = ButHP(self.tone_signal, freq=SUBSONIC)

        self.schedule_pattern(context)
        return self.finish(self.add_gate(self.body, context))

    def next_step(self) -> None:
        # the step comes from the shared clock's own tick - see `Clock.tick`'s
        # docstring
        step = self._step()
        if not step.hit:
            return
        self._accent = self.selected_phrase.accents[step.index]
        self.pitch.value = Note.transpose(self.root_freq, step.value)
        self.bark.mul = self.growl * self._accent
        self.amp.mul = self._accent
        self.trigger.play()


class FmBassBark(FmBass):
    """Clean, harmonic bark: two-operator FM at ratio 1."""

    ratio = FmBass.ratio.replace(default=1)

    def tone(
        self, index: PyoObject, level: PyoObject
    ) -> tuple[PyoObject, tuple[Any, ...]]:
        tone = FM(carrier=self.bent_pitch, index=index, mul=level)
        return tone, ()


class FmBassGrit(FmBass):
    """Grittier, less stable bark: carrier and modulator cross-modulate at ratio 2."""

    ratio = FmBass.ratio.replace(default=2)

    def tone(
        self, index: PyoObject, level: PyoObject
    ) -> tuple[PyoObject, tuple[Any, ...]]:
        cross = index * CROSS
        tone = CrossFM(carrier=self.bent_pitch, ind1=cross, ind2=index, mul=level)
        return tone, (cross,)
