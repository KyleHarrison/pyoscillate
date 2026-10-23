# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.lead.synth
#   style: solo | lead | slide | sync | pwm | trance5th
"""Subtractive synth leads, the recipes of the cookbook's lead section.

The graph and the controls are `lead.Lead`'s (two oscillators, a resonant
low-pass swept by its own envelope, an amplitude envelope, glide, vibrato and
a line played over the rack's chord); what this adds is the oscillators of the
recipes. Each is a saw, a square or a triangle at its own pitch offset and
level, and a square is a true pulse: `lead.Lead`'s pulse is pyo's type-4 `LFO`,
which is no duty-cycle square (see `pad/pad.py`), so here a square comes from
`pad.pad.Wave`, a sawtooth minus itself delayed by the pulse width. The pulse
width can sway on a slow LFO (the recipes' "PW osc1, osc2" routing), and the
second oscillator can be hard-synced to the first: it is read from a table at
the first's phase times the pitch ratio, so its pitch sweeps a sync tone.

The six styles are only profile data on that graph. Filter cutoffs are the
cookbook's knob positions turned into Hz (20 Hz to 20 kHz across 0 to 1, on a
log scale) and the envelope's travel is the Brightness slider, in Hz.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Pow, Wrap
from pyo.lib.generators import LFO, Phasor
from pyo.lib.tableprocess import Pointer

from pyoscillate.patches.base import Patch
from pyoscillate.patches.tonal.lead.lead import Lead
from pyoscillate.patches.tonal.pad.pad import Wave


class SynthLead(Lead):
    """Subtractive lead whose oscillators are chosen by the style: each a
    saw, square or triangle, optionally the second synced to the first."""

    volume = Patch.volume.replace(default=1.0)

    # a voice's level before the filter: a quiet signal keeps the resonant
    # filter well inside its stable range
    SOURCE_TRIM: ClassVar[float] = 0.25
    # the longest period (s) a pulse can have; the line is far above 10 Hz
    MAX_PERIOD: ClassVar[float] = 0.1

    # per-style oscillators: shape and level (dB); the offsets and pulse
    # widths are `Lead`'s osc1_detune, osc2_detune, osc1_duty and osc2_duty
    osc1_wave: ClassVar[Wave]
    osc2_wave: ClassVar[Wave]
    osc1_db: ClassVar[float] = 0.0
    osc2_db: ClassVar[float] = 0.0
    # osc2 hard-synced to osc1, which is then only the sync's clock and not
    # heard; its pitch swings `sweep_semitones` either way at `sweep_rate` Hz
    hard_sync: ClassVar[bool] = False
    sweep_semitones: ClassVar[float] = 0.0
    sweep_rate: ClassVar[float] = 0.5

    osc_sum: PyoObject
    master_phase: Phasor
    sweep_motion: LFO
    sweep_exponent: PyoObject
    sweep_wobble: PyoObject
    freq_ratio: PyoObject
    sync_ratio: PyoObject
    sync_ramp: PyoObject
    sync_phase: PyoObject
    osc2_table: PyoObject

    @classmethod
    def linear(cls, db: float) -> float:
        """A level in dB as the amplitude it multiplies by."""
        return 10 ** (db / 20)

    def make_source(self) -> PyoObject:
        self.pwm = LFO(freq=self.pwm_rate, type=3, sharp=0.5, mul=self.pwm_depth)
        self.osc1_sharp = self.osc1_duty + self.pwm
        self.osc2_sharp = self.osc2_duty + self.pwm
        level1 = self.linear(self.osc1_db) * self.SOURCE_TRIM
        level2 = self.linear(self.osc2_db) * self.SOURCE_TRIM
        if not self.hard_sync:
            stage = self.osc1_wave.oscillator(
                self.osc1_freq, self.osc1_sharp, level1, self.MAX_PERIOD
            )
            self.osc1 = stage.output
            self.retain(*stage.resources)
            stage = self.osc2_wave.oscillator(
                self.osc2_freq, self.osc2_sharp, level2, self.MAX_PERIOD
            )
            self.osc2 = stage.output
            self.retain(*stage.resources)
            self.osc_sum = self.osc1 + self.osc2
            return self.osc_sum * 1.0
        # the slave reads its table at the master's phase times the pitch
        # ratio, wrapped, so it restarts with every master cycle
        self.sweep_motion = LFO(freq=self.sweep_rate, type=3, sharp=0.5)
        self.sweep_exponent = self.sweep_motion * (self.sweep_semitones / 12)
        self.sweep_wobble = Pow(2, self.sweep_exponent)
        self.master_phase = Phasor(freq=self.osc1_freq)
        self.freq_ratio = self.osc2_freq * Pow(self.osc1_freq, -1)
        self.sync_ratio = self.freq_ratio * self.sweep_wobble
        self.sync_ramp = self.master_phase * self.sync_ratio
        self.sync_phase = Wrap(self.sync_ramp, min=0, max=1)
        self.osc2_table = self.osc2_wave.table()
        self.osc2 = Pointer(self.osc2_table, self.sync_phase, mul=level2)
        return self.osc2 * 1.0


class MonoSolo(SynthLead):
    """Mono Solo: two narrow pulses a few cents apart, a quick slide between
    notes and a moderate vibrato, through a ringing filter that barks open on
    each note; a singing, vocal synth solo."""

    title = "Mono Solo"
    summary = "Narrow, detuned pulse solo with a vocal bark, glide and vibrato."

    osc1_wave = Wave.SQUARE
    osc2_wave = Wave.SQUARE
    osc1_detune, osc2_detune = 0.0, 0.04
    osc1_duty, osc2_duty = 0.3, 0.2
    pwm_rate, pwm_depth = 0.0, 0.0
    vibrato_rate = 4.5
    filter_base, filter_env_depth, filter_resonance = 40.0, 6000.0, 0.54
    filter_attack, filter_decay, filter_sustain, filter_release = 0.0, 0.3, 0.4, 0.35
    amp_attack, amp_release = 0.0, 0.35
    base_drive = 0.0

    glide = Lead.glide.replace(default=0.04)
    vibrato = Lead.vibrato.replace(default=0.35)
    brightness = Lead.brightness.replace(default=6000.0)


class NewAgeLead(SynthLead):
    """New Age Lead: two squares five cents either side of the note, both
    pulses swaying, through a ringing filter that opens and settles on every
    note; a glassy, drifting, shimmering line."""

    title = "New Age Lead"
    summary = (
        "Shimmering pulse-width lead with a ringing filter that blooms on each note."
    )

    osc1_wave = Wave.SQUARE
    osc2_wave = Wave.SQUARE
    osc1_detune, osc2_detune = 0.05, -0.05
    osc1_duty, osc2_duty = 0.5, 0.5
    pwm_rate, pwm_depth = 5.5, 0.2
    filter_base, filter_env_depth, filter_resonance = 1400.0, 6000.0, 0.78
    filter_attack, filter_decay, filter_sustain, filter_release = 0.0, 1.2, 0.2, 0.6
    amp_attack, amp_release = 0.05, 0.35
    base_drive = 0.0

    brightness = Lead.brightness.replace(default=6000.0)


class RnbSlide(SynthLead):
    """R&B Slide: two triangles, an octave and three octaves up, sliding
    between notes while a ringing filter takes over a second to open; a
    smooth, whistling, high slide."""

    title = "R&B Slide"
    summary = "High, soft triangle lead that slides between notes under a slowly opening filter."

    osc1_wave = Wave.TRIANGLE
    osc2_wave = Wave.TRIANGLE
    osc2_db = -6.0
    osc1_detune, osc2_detune = 12.0, 36.0
    osc1_duty, osc2_duty = 0.5, 0.5
    pwm_rate, pwm_depth = 0.0, 0.0
    filter_base, filter_env_depth, filter_resonance = 1900.0, 6000.0, 0.54
    filter_attack, filter_release = 1.2, 6.3
    amp_attack, amp_release = 0.02, 0.6
    base_drive = 0.0

    glide = Lead.glide.replace(default=0.02)
    brightness = Lead.brightness.replace(default=6000.0)


class ScreamingSync(SynthLead):
    """Screaming Sync: a square hard-synced to a silent oscillator an octave
    down, its pitch swinging slowly either way so the sync tone shrieks up and
    down; a raw, tearing lead."""

    title = "Screaming Sync"
    summary = "Hard-sync lead whose swinging pitch makes the tone scream."

    osc1_wave = Wave.SAW
    osc2_wave = Wave.SQUARE
    osc1_detune, osc2_detune = -12.0, 0.0
    osc1_duty, osc2_duty = 0.5, 0.5
    pwm_rate, pwm_depth = 0.0, 0.0
    hard_sync = True
    sweep_semitones, sweep_rate = 4.5, 0.66
    filter_base, filter_env_depth, filter_resonance = 10000.0, 0.0, 0.0
    filter_attack, filter_release = 0.0, 0.0
    amp_attack, amp_release = 0.0, 0.6
    base_drive = 0.0

    glide = Lead.glide.replace(default=0.02)
    brightness = Lead.brightness.replace(default=0.0)


class StringsPwm(SynthLead):
    """Strings Pulse-Width Modulation: two squares ten cents apart, their
    pulses swaying slowly, through a filter that opens over the note; a lush,
    chorused string-machine line."""

    title = "Strings PWM"
    summary = "Lush string-machine lead of two slowly swaying pulses."

    osc1_wave = Wave.SQUARE
    osc2_wave = Wave.SQUARE
    osc1_detune, osc2_detune = -0.1, 0.1
    osc1_duty, osc2_duty = 0.5, 0.5
    pwm_rate, pwm_depth = 2.0, 0.21
    filter_base, filter_env_depth, filter_resonance = 2000.0, 6000.0, 0.0
    filter_attack, filter_release = 0.09, 3.0
    amp_attack, amp_release = 0.11, 0.35
    base_drive = 0.0

    brightness = Lead.brightness.replace(default=6000.0)


class Trance5th(SynthLead):
    """Trance 5th: a square and a second a fifth above, their pulses swaying
    fast, the filter wide open and no release; the stacked-fifth stab of a
    trance riff."""

    title = "Trance 5th"
    summary = "Fast pulse-width swaying square-and-fifth lead, wide open and cut short."

    osc1_wave = Wave.SQUARE
    osc2_wave = Wave.SQUARE
    osc1_detune, osc2_detune = 0.0, 7.0
    osc1_duty, osc2_duty = 0.5, 0.5
    pwm_rate, pwm_depth = 6.0, 0.36
    filter_base, filter_env_depth, filter_resonance = 10000.0, 0.0, 0.0
    filter_attack, filter_release = 0.0, 0.005
    amp_attack, amp_release = 0.0, 0.005
    base_drive = 0.0

    brightness = Lead.brightness.replace(default=0.0)
