# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.funk.funk
"""Funk bass: a syncopated line whose filter opens slowly on every note, a quack.

The voice is the "Funk Bass" recipe:

- a saw and a 30% pulse, one octave apart, at equal level. The pulse is two
  copies of the same saw with their phases 0.3 of a cycle apart, subtracted.
  The result is a zero-mean pulse that is band-limited like the saw.
- a 24 dB ladder low-pass (`MoogLP`) sitting almost shut at 40 Hz, with
  medium resonance.
- a filter envelope with a slow 150 ms attack (A 0.15 s, D 0.10 s, S 45%,
  R 0.08 s) that sweeps the cutoff up by several octaves. Because the attack
  is slow, the filter opens across the note rather than on the front of it,
  and that swell is the quack. Short ghost notes end before the filter has
  opened, so they stay dark and thuddy.
- an amplitude envelope with an instant attack that drops to a lower held
  level (A 0, D 0.29 s, S 30%, R 0.40 s).
- mono, with a 20 ms glide on every note change.

The envelope drives the cutoff exponentially (octaves, like 1 V/oct on an
analogue filter), so the note quacks bright and then settles dark instead of
staying bright for the whole sustain. The cookbook's "envelope 85%" is a
synth knob position; `QUACK` octaves is its reading here, tuned by ear.

The line is `BassLines.BASS_FUNK` by default, a one-bar funk figure on chord
tones, re-rooted on each bar's chord from the rack's `Harmony` (see
`Bass.chord_root`). Its pitches are tones of a minor-seventh chord, like the
other bass lines. Accents scale
the level and the filter sweep together, so accented notes quack harder and
ghost notes stay dark.
"""

from __future__ import annotations

from pyo import PyoObject
from pyo.lib.arithmetic import Pow
from pyo.lib.controls import Adsr, SigTo
from pyo.lib.dynamics import Clip
from pyo.lib.filters import MoogLP
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import LinTable, SawTable
from pyo.lib.triggers import TrigEnv, TrigFunc

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.tonal.bass.base import Bass
from pyoscillate.theory.phrase import BassLines
from pyoscillate.theory.pitch import Note

BASE_DIVISION = NoteDivision.SIXTEENTH
# the cookbook recipe; every time is in seconds, every level 0..1
CUTOFF = 40
RESONANCE = 0.5
QUACK = 6.5
FILTER_ENVELOPE = {"attack": 0.15, "decay": 0.10, "sustain": 0.45, "release": 0.08}
# the recipe's 0 s attack, lengthened just enough not to click
AMP_ENVELOPE = {"attack": 0.002, "decay": 0.29, "sustain": 0.30, "release": 0.40}
# pyo's MoogLP blows up to NaN, which the limiter turns into silence for the
# rest of the patch, when a fast sweep drives it high with a hot input.
# Measured offline: at Growl 0.95 and a sweep to 12 kHz it stays finite with
# an input peak around 1 and fails at 2. So the mix is trimmed to that level
# before the filter, and the cutoff is capped with margin.
CUTOFF_CEILING = 8000
# the saw and the pulse peak at about 1.4 and 2.2 (the table's Gibbs
# overshoot included), so their sum peaks near 3.7
FILTER_TRIM = 0.25
PULSE_WIDTH = 0.3
# harmonics in the saw table: enough to stay bright where the filter is wide
# open, and below Nyquist for the top of the line (osc 2 at ~310 Hz)
SAW_ORDER = 64
GAIN = 0.4


class FunkBass(Bass):
    """Funk bass: a syncopated line whose filter quacks open on every note.
    See the module docstring for the sonic detail."""

    volume = Patch.volume.replace(default=0.5)
    # the recipe's 20 ms glide on every note change
    glide = Bass.glide.replace(default=0.02)
    phrase = Bass.phrase.replace(default=BassLines.BASS_FUNK)

    # the graph, assigned by build(); finish() retains every one of them
    pitch: SigTo
    upper_pitch: PyoObject
    saw_table: SawTable
    saw: Osc
    pulse_lead: Osc
    pulse_lag: Osc
    pulse: PyoObject
    mix: PyoObject
    trimmed: PyoObject
    note_gate_table: LinTable
    note_gate: TrigEnv
    amp: Adsr
    level: PyoObject
    sweep: Adsr
    cutoff_freq: Pow
    safe_cutoff: Clip
    filtered: MoogLP
    gate_end: TrigFunc
    body: PyoObject

    octave = Bass.octave.replace(
        help_text="Lifts the bassline up an octave; low sits deep under the kick, high brings the "
        "quack forward like a slap line. The notes always follow the rack's key and chord changes.",
    )

    @Param(
        20,
        400,
        5,
        CUTOFF,
        "Brightness",
        "How open the filter sits between notes and where every sweep starts from; low is a dark "
        "thud that only the quack brightens, high keeps a buzzy edge on the whole line.",
        sweep=True,
    )
    def cutoff(self, value: float) -> None:
        self.cutoff_freq.mul = value

    # read live off `self.quack` by build()'s trigger-time callback - no
    # control body needed, see `patches/AGENTS.md`'s note on a parameter
    # only read by a sequencer callback
    quack = Param(
        0,
        8,
        0.1,
        QUACK,
        "Quack",
        "How far the filter sweeps open on each note; low is a quiet, muted thump, high a wide, "
        "vocal 'wow' on every accented note. Ghost notes always stay darker.",
        advanced=True,
    )

    @Param(
        0.005,
        0.4,
        0.005,
        FILTER_ENVELOPE["attack"],
        "Swell",
        "How slowly the filter opens, in seconds; short is a snappy pluck on the front of each "
        "note, long a lazy auto-wah that only the held notes reach the top of.",
        sweep=True,
        advanced=True,
    )
    def swell(self, value: float) -> None:
        self.sweep.attack = value

    @Param(
        0,
        0.95,
        0.05,
        RESONANCE,
        "Growl",
        "Adds a resonant peak that rides the sweep; higher makes the quack more nasal and "
        "rubbery, lower keeps it smooth.",
        sweep=True,
    )
    def resonance(self, value: float) -> None:
        self.filtered.res = value

    # read live off `self.length` by build()'s trigger-time callback - see
    # the note on `quack` above
    length = Param(
        0.3,
        1.5,
        0.05,
        1.0,
        "Length",
        "Scales how long every note is held; short is tight and staccato with more space in the "
        "groove, long lets notes run into each other.",
    )

    rate = rate_param(
        BASE_DIVISION,
        "Halves or doubles the bassline speed for each step away from its 16th-note grid.",
    )

    def current_root(self) -> float:
        return self.chord_root()

    def build(self, context: BuildContext) -> Patch:
        """Build the funk bassline: saw + pulse through a slowly swept ladder low-pass."""
        self._reset()
        # matches the free `Trig()` this voice used before it was migrated
        # onto `Bass`'s trigger: silent until the clock ticks (see
        # tests/pyoscillate/patches/test_gated_patches.py)
        self.trigger.stop()
        self._context = context
        self._tempo = context.tempo

        # osc 1 (the saw) sits at the register centre; osc 2 (the pulse) is an
        # octave above it
        self.upper_pitch = self.pitch_signal(self.register_centre) * 2
        self.saw_table = SawTable(order=SAW_ORDER)
        self.saw = Osc(self.saw_table, freq=self.bent_pitch)
        # a saw minus the same saw a fraction of a cycle later is a pulse of that
        # width; both saws are zero-mean, so the pulse is too
        self.pulse_lead = Osc(self.saw_table, freq=self.upper_pitch)
        self.pulse_lag = Osc(self.saw_table, freq=self.upper_pitch, phase=PULSE_WIDTH)
        self.pulse = self.pulse_lead - self.pulse_lag
        self.mix = self.saw + self.pulse
        self.trimmed = self.mix * FILTER_TRIM

        # the gate: held open for the note's length, then its end trigger
        # releases both envelopes. A new note restarts it, so a long note's
        # release never lands on the note after it.
        self.note_gate_table = LinTable([(0, 1), (8191, 1)])
        self.note_gate = TrigEnv(
            self.trigger, self.note_gate_table, dur=context.tempo.sixteenth
        )
        self.sync(context.tempo, lambda t: setattr(self.note_gate, "dur", t.sixteenth))
        self.amp = Adsr(**AMP_ENVELOPE)
        self.level = self.amp * GAIN
        self.sweep = Adsr(
            attack=self.swell,
            decay=FILTER_ENVELOPE["decay"],
            sustain=FILTER_ENVELOPE["sustain"],
            release=FILTER_ENVELOPE["release"],
            mul=self.quack,
        )
        # the envelope counts octaves above `cutoff`
        self.cutoff_freq = Pow(base=2, exponent=self.sweep, mul=self.cutoff)
        self.safe_cutoff = Clip(self.cutoff_freq, min=0, max=CUTOFF_CEILING)
        self.filtered = MoogLP(self.trimmed, freq=self.safe_cutoff, res=self.resonance)
        self.body = self.filtered * self.level

        self.gate_end = TrigFunc(self.note_gate["trig"], self.note_off)

        self.schedule_pattern(context)
        return self.finish(self.add_gate(self.body, context))

    def note_off(self) -> None:
        self.amp.stop()
        self.sweep.stop()

    def next_step(self) -> None:
        # derived from the shared clock's own tick - see `Clock.tick`'s
        # docstring
        step = self._step()
        if not step.hit:
            return
        melody = self.selected_phrase
        accent = melody.accents[step.index]
        root = self.current_root()
        self.pitch.value = Note.transpose(root, step.value)
        self.note_gate.dur = (
            self._tempo.sixteenth * melody.lengths[step.index] * self.length
        )
        self.amp.mul = accent
        self.sweep.mul = self.quack * accent
        self.amp.play()
        self.sweep.play()
        self.trigger.play()
