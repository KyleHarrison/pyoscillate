# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.reese.reese
#   style: wobble | heave
"""Wobble bass: a detuned saw stack over a pure sub, its filter moved by a
tempo-locked LFO.

The voice is a Reese (several slightly detuned saws, whose beating gives the
slow phasing) with the one thing dubstep adds: the low-pass cutoff is
modulated at a fraction of the bar, so the bass opens and closes in time with
the drums.

- a `SuperSaw` (pyo's seven-detuned-saw stack) at the note's pitch, mixed to
  mono and trimmed before the filter. Thickness moves the saws apart.
- a 24 dB ladder low-pass (`MoogLP`) whose cutoff is `Brightness x
  2^(wobble)`: the LFO counts octaves, like 1 V/oct on an analogue filter, so
  an even sine moves the tone by an even musical interval at any depth.
- the LFO is a sine at `1 / (bar x fraction)` Hz, restarted on every note so
  each note begins on the same phase of the wobble (closed, then opening)
  instead of wherever a free-running LFO happened to be. Its rate is a
  `NoteDivision`-style fraction of the bar, so it follows tempo changes.
- waveshaping (`Disto`) after the filter. The filter's resonance peak then
  feeds the shaper, which is where the growl comes from.
- a sine sub at the note's pitch, outside the filter and the shaper, so the
  weight under 60 Hz stays clean whatever the wobble does above it.
- an amplitude `Adsr` held for the phrase step's own length and released at
  its end, like `FunkBass`: a held note rings across several wobble cycles, a
  short stab is gone before the filter has moved.

The line is a `BassLines` phrase by default, a held root with short stabs,
re-rooted on each bar's chord from the rack's `Harmony`
(see `Bass.chord_root`). Accents scale the level.

The two styles share all of this and differ in the data and the wobble speed:
`wobble` (`ReeseWobble`) moves in eighths over held roots and stabs, `heave`
(`ReeseHeave`) breathes in half notes over one held root a bar.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.arithmetic import Pow
from pyo.lib.controls import Adsr
from pyo.lib.dynamics import Clip
from pyo.lib.effects import Disto
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Sine, SuperSaw
from pyo.lib.tables import LinTable
from pyo.lib.triggers import TrigEnv, TrigFunc

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.tonal.bass.base import Bass
from pyoscillate.theory.phrase import BassLines
from pyoscillate.theory.pitch import Note

STYLES = ("wobble", "heave")
BASE_DIVISION = NoteDivision.SIXTEENTH
# pyo's MoogLP blows up to NaN, which the limiter turns into silence for the
# rest of the patch, when a fast sweep drives it high with a hot input (see
# `funk.py`). The saw stack is trimmed to a safe peak before the filter and the
# cutoff is capped well under Nyquist.
CUTOFF_CEILING = 8000
CUTOFF_FLOOR = 30
FILTER_TRIM = 0.4
# the stack, the shaper and the sub are summed under the output ceiling
TONE_GAIN = 0.5
SUB_GAIN = 0.6
GAIN = 0.5
# the amplitude envelope: a near-instant attack to a held body
AMP_ENVELOPE = {"attack": 0.004, "decay": 0.12, "sustain": 0.85, "release": 0.06}
# a sine that starts at its minimum, so every note opens from a closed filter
LFO_PHASE = 0.75


class Reese(Bass):
    """Wobble bass base: detuned saws and a sub through an LFO-swept ladder
    low-pass and a shaper. Style variants subclass this and change only the
    starting values; see the module docstring for the sonic detail."""

    volume = Patch.volume.replace(default=0.6)
    # the sub sits at F1: every chord root of a minor-key progression lands
    # within a tritone of it, so the line stays in the sub range
    register_centre: ClassVar[float] = Note.F1
    phrase = Bass.phrase.replace(default=BassLines.BASS_DROP)
    glide = Bass.glide.replace(default=0.02)

    # the wobble's period as a fraction of a bar, and its label, in the order
    # of the Speed dropdown
    WOBBLE_BARS: ClassVar[tuple[float, ...]] = (
        1 / 2,
        1 / 4,
        1 / 6,
        1 / 8,
        1 / 12,
        1 / 16,
    )
    WOBBLE_LABELS: ClassVar[tuple[str, ...]] = (
        "1/2",
        "1/4",
        "1/4 triplet",
        "1/8",
        "1/8 triplet",
        "1/16",
    )

    # the graph, assigned by build(); finish() retains every one of them
    stack: SuperSaw
    stack_mono: Mix
    trimmed: PyoObject
    wobble_lfo: Sine
    cutoff_freq: Pow
    safe_cutoff: Clip
    filtered: MoogLP
    shaper: Disto
    sub_osc: Sine
    tone_mix: PyoObject
    note_gate_table: LinTable
    note_gate: TrigEnv
    amp: Adsr
    level: PyoObject
    body: PyoObject
    gate_end: TrigFunc

    octave = Bass.octave.replace(
        help_text="Lifts the bass up an octave; low is a chest-rattling sub, high brings the wobble forward "
        "so it reads on small speakers. The notes always follow the rack's key and chord changes.",
    )

    @Param(
        60,
        1500,
        10,
        180,
        "Brightness",
        "Where the filter rests between wobbles; low is a dark, closed growl that only the wobble opens, "
        "high keeps a buzzy edge on the whole line.",
        scale="cutoff",
        sweep=True,
    )
    def cutoff(self, value: float) -> None:
        self.cutoff_freq.mul = value

    @Param(
        0,
        5,
        0.1,
        3.0,
        "Wobble",
        "How far the filter opens on every wobble, in octaves; none is a steady, droning bass, high is a "
        "wide, vowel-like wub that swings from muffled to harsh.",
        sweep=True,
    )
    def depth(self, value: float) -> None:
        self.wobble_lfo.mul = value / 2
        self.wobble_lfo.add = value / 2

    @Param(
        0,
        len(WOBBLE_BARS) - 1,
        1,
        3,
        "Wobble speed",
        "How often the filter opens, locked to the tempo: 1/2 and 1/4 heave slowly under the beat, 1/8 "
        "and the triplets wub in time with the drums, 1/16 is a fast, rasping flutter.",
        options=WOBBLE_LABELS,
    )
    def speed(self, value: float) -> None:
        self.retime_wobble()

    @Param(
        0,
        0.95,
        0.05,
        0.45,
        "Bite",
        "Adds a resonant peak that rides the wobble; higher makes it more nasal and vocal, lower keeps it "
        "smooth and round.",
        sweep=True,
    )
    def resonance(self, value: float) -> None:
        self.filtered.res = value

    @Param(
        0,
        0.95,
        0.05,
        0.4,
        "Growl",
        "Saturates the filtered bass; none is a clean wobble, high is a snarling, distorted growl with "
        "more upper harmonics.",
        sweep=True,
    )
    def growl(self, value: float) -> None:
        self.shaper.drive = value

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Thickness",
        "How far the stacked saws drift apart; none is a single, narrow saw, high is a wide, slowly "
        "phasing wall of sound.",
        sweep=True,
    )
    def thickness(self, value: float) -> None:
        self.stack.detune = value

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Sub",
        "The clean sine weight under the wobble; none leaves only the growl, high adds a deep, steady "
        "foundation that the wobble never touches.",
        sweep=True,
    )
    def sub(self, value: float) -> None:
        self.sub_osc.mul = value * SUB_GAIN

    # read live off `self.length` by next_step() - see `patches/AGENTS.md`'s
    # note on a parameter only read by a sequencer callback
    length = Param(
        0.3,
        1.5,
        0.05,
        1.0,
        "Length",
        "Scales how long every note is held; short is tight and staccato with more air between wobbles, "
        "long lets notes run into each other.",
    )

    rate = rate_param(
        BASE_DIVISION,
        "Halves or doubles the bassline speed for each step away from its 16th-note grid.",
    )

    def current_root(self) -> float:
        return self.chord_root()

    def retime_wobble(self) -> None:
        """Set the wobble's frequency from the current Speed and the shared
        tempo: one cycle per `WOBBLE_BARS[speed]` of a bar."""
        bars = self.WOBBLE_BARS[int(self.speed)]
        self.wobble_lfo.freq = 1 / (self._tempo.bar * bars)

    def build(self, context: BuildContext) -> Patch:
        """Build the wobble bass: saws and a sub through a tempo-locked,
        LFO-swept low-pass."""
        self._reset()
        # silent until the clock ticks (see tests/pyoscillate/patches/test_gated_patches.py)
        self.trigger.stop()
        self._context = context
        self._tempo = context.tempo

        self.pitch_signal(self.register_centre)
        self.stack = SuperSaw(freq=self.bent_pitch, detune=0.5, bal=0.7)
        self.stack_mono = self.stack.mix(1)
        self.trimmed = self.stack_mono * FILTER_TRIM

        # neutral depth: the `depth` control sets the real one
        self.wobble_lfo = Sine(freq=1, phase=LFO_PHASE, mul=0, add=0)
        self.sync(context.tempo, lambda t: self.retime_wobble())
        # the LFO counts octaves above `cutoff`
        self.cutoff_freq = Pow(base=2, exponent=self.wobble_lfo, mul=self.cutoff)
        self.safe_cutoff = Clip(self.cutoff_freq, min=CUTOFF_FLOOR, max=CUTOFF_CEILING)
        self.filtered = MoogLP(self.trimmed, freq=self.safe_cutoff, res=self.resonance)
        self.shaper = Disto(self.filtered, drive=self.growl, slope=0.6)

        # the sub is outside the filter and the shaper
        self.sub_osc = Sine(freq=self.bent_pitch, mul=0)
        self.tone_mix = self.shaper * TONE_GAIN + self.sub_osc

        # the gate: held open for the note's length, then its end trigger
        # releases the envelope. A new note restarts it, so a long note's
        # release never lands on the note after it.
        self.note_gate_table = LinTable([(0, 1), (8191, 1)])
        self.note_gate = TrigEnv(
            self.trigger, self.note_gate_table, dur=context.tempo.sixteenth
        )
        self.sync(context.tempo, lambda t: setattr(self.note_gate, "dur", t.sixteenth))
        self.amp = Adsr(**AMP_ENVELOPE)
        self.level = self.amp * GAIN
        self.body = self.tone_mix * self.level
        self.gate_end = TrigFunc(self.note_gate["trig"], self.note_off)

        self.schedule_pattern(context)
        return self.finish(self.add_gate(self.body, context))

    def note_off(self) -> None:
        self.amp.stop()

    def next_step(self) -> None:
        # derived from the shared clock's own tick - see `Clock.tick`'s docstring
        step = self._step()
        if not step.hit:
            return
        line = self.selected_phrase
        self.pitch.value = Note.transpose(self.current_root(), step.value)
        self.note_gate.dur = (
            self._tempo.sixteenth * line.lengths[step.index] * self.length
        )
        self.amp.mul = line.accents[step.index]
        # every note starts the wobble from the same point
        self.wobble_lfo.reset()
        self.amp.play()
        self.trigger.play()


class ReeseWobble(Reese):
    """Fast, rhythmic wobble: held roots and short stabs, the filter wubbing
    in eighths."""

    title = "Bass - Wobble"
    summary = "Heavy half-time wobble bass: held roots and stabs, the filter wubbing in eighths."
    phrase = Reese.phrase.replace(default=BassLines.BASS_DROP)


class ReeseHeave(Reese):
    """Slow, wide heave: one held root a bar, the filter breathing in half
    notes, thicker and cleaner than the wobble."""

    title = "Bass - Heave"
    summary = "Slow, wide, heaving bass: one held root a bar, the filter breathing in half notes."
    phrase = Reese.phrase.replace(default=BassLines.BASS_HEAVE)
    glide = Reese.glide.replace(default=0.05)
    speed = Reese.speed.replace(default=0)
    depth = Reese.depth.replace(default=3.5)
    thickness = Reese.thickness.replace(default=0.75)
    growl = Reese.growl.replace(default=0.2)
    resonance = Reese.resonance.replace(default=0.3)
