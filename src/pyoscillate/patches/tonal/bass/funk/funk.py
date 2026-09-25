# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.funk.funk
"""Funk bass: a syncopated line whose filter opens slowly on every note, a quack.

The voice is the "Funk Bass" recipe from Welsh's Synthesizer Cookbook:

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

The line is a one-bar funk figure on chord tones, re-rooted on each bar's
chord from the rack's `Harmony` (see `Bass.note_root`). It is written as
degrees of a minor-seventh chord, like the groove profiles. Accents scale
the level and the filter sweep together, so accented notes quack harder and
ghost notes stay dark.
"""

from __future__ import annotations

from typing import Any, ClassVar, NamedTuple

from pyo.lib.arithmetic import Pow
from pyo.lib.controls import Adsr, SigTo
from pyo.lib.dynamics import Clip
from pyo.lib.filters import MoogLP
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import LinTable, SawTable
from pyo.lib.triggers import TrigEnv, TrigFunc

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.tonal.bass.base import Bass
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo


class Step(NamedTuple):
    """One 16th of the line. `semitones` is above the chord root, or None for
    a rest; `length` is how long the note is held, in 16ths."""

    semitones: int | None
    accent: float = 1.0
    length: float = 1.0


REST = Step(None)
# root on the One, held; octave pops; minor 7th, 5th and minor 3rd fills;
# dead-note ghosts between them. Every pitch is a tone of the rack's
# minor-seventh chords, so re-rooting keeps the line consonant. The minor
# 7th on the last 16th glides down into the next bar's root.
LINE: tuple[Step, ...] = (
    Step(0, 1.0, 1.8),
    REST,
    REST,
    Step(0, 0.55, 0.4),
    Step(12, 0.9, 0.6),
    REST,
    Step(10, 0.75, 0.9),
    Step(0, 0.55, 0.4),
    REST,
    Step(7, 0.8, 0.6),
    Step(0, 0.55, 0.4),
    Step(3, 0.8, 0.9),
    REST,
    Step(7, 0.7, 0.5),
    Step(12, 0.9, 0.5),
    Step(10, 0.6, 0.5),
)

BASE_DIVISION = NoteDivision.SIXTEENTH
# the cookbook recipe; every time is in seconds, every level 0..1
CUTOFF = 40
RESONANCE = 0.5
QUACK = 6.5
FILTER_ENVELOPE = {"attack": 0.15, "decay": 0.10, "sustain": 0.45, "release": 0.08}
# the recipe's 0 s attack, lengthened just enough not to click
AMP_ENVELOPE = {"attack": 0.002, "decay": 0.29, "sustain": 0.30, "release": 0.40}
GLIDE = 0.02
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
VOLUME_DEFAULT = 0.5
# osc 1 (the saw) sits here; osc 2 (the pulse) is an octave above it
REGISTER_CENTRE = notes.A1
# a static key of A - used only outside a rack that shares its own `Harmony`
FALLBACK_HARMONY = Harmony()

PARAMETERS = (
    SliderSpec(
        "octave",
        0,
        1,
        1,
        0,
        "Register",
        "Lifts the bassline up an octave; low sits deep under the kick, high brings the quack "
        "forward like a slap line. The notes always follow the rack's key and chord changes.",
    ),
    SliderSpec(
        "cutoff",
        20,
        400,
        5,
        CUTOFF,
        "Brightness",
        "How open the filter sits between notes and where every sweep starts from; low is a dark "
        "thud that only the quack brightens, high keeps a buzzy edge on the whole line.",
        (PyoParamRef(Pow, "mul"),),
    ),
    SliderSpec(
        "quack",
        0,
        8,
        0.1,
        QUACK,
        "Quack",
        "How far the filter sweeps open on each note; low is a quiet, muted thump, high a wide, "
        "vocal 'wow' on every accented note. Ghost notes always stay darker.",
        (PyoParamRef(Adsr, "mul"),),
    ),
    SliderSpec(
        "swell",
        0.005,
        0.4,
        0.005,
        FILTER_ENVELOPE["attack"],
        "Swell",
        "How slowly the filter opens, in seconds; short is a snappy pluck on the front of each "
        "note, long a lazy auto-wah that only the held notes reach the top of.",
        (PyoParamRef(Adsr, "attack"),),
    ),
    SliderSpec(
        "resonance",
        0,
        0.95,
        0.05,
        RESONANCE,
        "Growl",
        "Adds a resonant peak that rides the sweep; higher makes the quack more nasal and "
        "rubbery, lower keeps it smooth.",
        (PyoParamRef(MoogLP, "res"),),
    ),
    SliderSpec(
        "length",
        0.3,
        1.5,
        0.05,
        1.0,
        "Length",
        "Scales how long every note is held; short is tight and staccato with more space in the "
        "groove, long lets notes run into each other.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the bassline speed for each step away from its 16th-note grid.",
    ),
)


class FunkBass(Bass):
    """Funk bass: a syncopated line whose filter quacks open on every note.
    See the module docstring for the sonic detail."""

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    needs_harmony: ClassVar[bool] = True

    octave: float
    cutoff: float
    quack: float
    swell: float
    resonance: float
    length: float
    rate: float

    def build(self, tempo: Tempo, clock: Clock, harmony: Harmony | None = None, **values: Any) -> Patch:
        """Build the funk bassline: saw + pulse through a slowly swept ladder low-pass."""
        self.configure(**values)
        self._reset()
        # matches the free `Trig()` this voice used before it was migrated
        # onto `Bass`'s trigger: silent until the clock ticks (see
        # tests/pyoscillate/patches/test_gated_patches.py)
        self.trigger.stop()
        current_root = self.note_root(
            REGISTER_CENTRE, clock, harmony=harmony or FALLBACK_HARMONY, octave=self.octave
        )
        state = {"step": 0, "quack": self.quack, "length": self.length}

        pitch = SigTo(value=REGISTER_CENTRE, time=GLIDE, init=REGISTER_CENTRE)
        upper_pitch = pitch * 2
        saw_table = SawTable(order=SAW_ORDER)
        saw = Osc(saw_table, freq=pitch)
        # a saw minus the same saw a fraction of a cycle later is a pulse of that
        # width; both saws are zero-mean, so the pulse is too
        pulse_lead = Osc(saw_table, freq=upper_pitch)
        pulse_lag = Osc(saw_table, freq=upper_pitch, phase=PULSE_WIDTH)
        pulse = pulse_lead - pulse_lag
        mix = saw + pulse
        trimmed = mix * FILTER_TRIM

        # the gate: held open for the note's length, then its end trigger
        # releases both envelopes. A new note restarts it, so a long note's
        # release never lands on the note after it.
        gate_table = LinTable([(0, 1), (8191, 1)])
        gate = TrigEnv(self.trigger, gate_table, dur=tempo.sixteenth)
        amp = Adsr(**AMP_ENVELOPE)
        level = amp * GAIN
        sweep = Adsr(
            attack=self.swell,
            decay=FILTER_ENVELOPE["decay"],
            sustain=FILTER_ENVELOPE["sustain"],
            release=FILTER_ENVELOPE["release"],
            mul=self.quack,
        )
        # the envelope counts octaves above `cutoff`
        cutoff_freq = Pow(base=2, exponent=sweep, mul=self.cutoff)
        safe_cutoff = Clip(cutoff_freq, min=0, max=CUTOFF_CEILING)
        filtered = MoogLP(trimmed, freq=safe_cutoff, res=self.resonance)
        voice = filtered * level
        self.retain(
            pitch,
            upper_pitch,
            saw_table,
            saw,
            pulse_lead,
            pulse_lag,
            pulse,
            mix,
            trimmed,
            gate_table,
            gate,
            amp,
            level,
            sweep,
            cutoff_freq,
            safe_cutoff,
            filtered,
        )

        def note_off() -> None:
            amp.stop()
            sweep.stop()

        gate_end = TrigFunc(gate["trig"], note_off)
        self.retain(gate_end)

        def next_step() -> None:
            step = LINE[state["step"] % len(LINE)]
            state["step"] += 1
            if step.semitones is None:
                return
            root = current_root()
            pitch.value = root * 2 ** (step.semitones / 12)
            gate.dur = tempo.sixteenth * step.length * state["length"]
            amp.mul = step.accent
            sweep.mul = state["quack"] * step.accent
            amp.play()
            sweep.play()
            self.trigger.play()

        self.schedule(BASE_DIVISION, self.rate, clock, next_step)
        return self.finish(
            voice,
            {
                "cutoff": lambda value: setattr(cutoff_freq, "mul", value),
                "quack": lambda value: state.update(quack=value),
                "swell": lambda value: setattr(sweep, "attack", value),
                "resonance": lambda value: setattr(filtered, "res", value),
                "length": lambda value: state.update(length=value),
            },
        )
