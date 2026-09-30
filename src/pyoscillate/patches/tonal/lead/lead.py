# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.lead.lead style=brass
#   style: brass | mellow_70s
"""Dual-oscillator subtractive lead voices.

Two detuned pulse oscillators (a `Pulse`-type `LFO`, whose `sharp` parameter
is duty cycle rather than raw waveshape here) sum into a resonant low-pass
filter whose cutoff is swept by its own ADSR, ahead of a separate amplitude
ADSR and a light saturation stage:

- **Brass Section**: a narrow, detuned pulse pair widened by a slow LFO on
  both oscillators' duty cycle (the recipe's "PW osc1, osc2" LFO routing),
  a dark filter that snaps open on every note for the characteristic brass
  "blat", and a beefy resonant edge.
- **Mellow 70's Lead**: two near-unison plain squares, no PWM, filter wide
  open and static, legato glide between notes for a smooth, vocal lead.

Both play a short melodic motif that follows the rack's chord changes, one
note per 8th note, with a rest that lets each phrase's Release breathe.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from pyo import PyoObject
from pyo.lib.controls import Adsr, SigTo
from pyo.lib.effects import Disto
from pyo.lib.filters import MoogLP
from pyo.lib.generators import LFO

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import GatedVoice, Step
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.utility.notes import notes

# step -> semitone offset above the current chord root; an absent step (6) is
# a rest, giving the phrase somewhere for its Release tail to be heard. The
# default motif for styles that don't override `pattern` (see `Lead.pattern`).
PATTERN = {0: 0, 1: 4, 2: 7, 3: 12, 4: 7, 5: 4, 7: 0}
BASE_DIVISION = NoteDivision.EIGHTH
PULSE_TYPE = 4  # pyo LFO waveform index for Pulse; `sharp` is duty cycle


class Lead(GatedVoice):
    """Monophonic lead: two detuned pulse oscillators into a resonant
    low-pass with its own ADSR, then an amplitude ADSR and light saturation.
    Style subclasses supply fixed detune/PWM/filter/envelope/glide data; the
    graph is identical across styles."""

    volume = Patch.volume.replace(default=0.7)
    base_division: ClassVar[NoteDivision] = BASE_DIVISION
    # this style's melodic motif; a style with a sparser or differently-
    # phrased line overrides it (different profile data, same graph)
    pattern: ClassVar[dict[int, int]] = PATTERN
    # the number of steps one pass of `pattern` spans
    cycle: ClassVar[int] = 8

    # osc1/osc2 detune in semitones (osc2's can exceed an octave, e.g. +12.1)
    osc1_detune: ClassVar[float]
    osc2_detune: ClassVar[float]
    # each oscillator's resting duty cycle (0.5 is a symmetric square)
    osc1_duty: ClassVar[float]
    osc2_duty: ClassVar[float]
    # PWM LFO rate (Hz) and duty-cycle excursion; 0 depth disables PWM
    pwm_rate: ClassVar[float]
    pwm_depth: ClassVar[float]
    # filter base cutoff (Hz), its envelope sweep depth (Hz added on top),
    # and resonance
    filter_base: ClassVar[float]
    filter_env_depth: ClassVar[float]
    filter_resonance: ClassVar[float]
    filter_attack: ClassVar[float]
    filter_release: ClassVar[float]
    # amplitude envelope times (seconds); sustain is always full per the
    # cookbook recipes (100%) and exposed live via `sustain`
    amp_attack: ClassVar[float]
    amp_release: ClassVar[float]
    # portamento time between notes; 0 is an instant jump (no glide)
    glide_time: ClassVar[float]
    # resting saturation drive
    base_drive: ClassVar[float]

    # the graph, assigned by build(); finish() retains every one of them
    pitch1: SigTo
    pitch2: SigTo
    pitch_vibrato: LFO
    osc1_freq: PyoObject
    osc2_freq: PyoObject
    pwm: LFO
    osc1_sharp: PyoObject
    osc2_sharp: PyoObject
    osc1: LFO
    osc2: LFO
    mixed: PyoObject
    filter_env: Adsr
    filtered: MoogLP
    amp_env: Adsr
    shaped: Disto
    voice_signal: PyoObject

    # the rack's harmony, frozen at build time - fed to `next_step`, which
    # build() can no longer close over now that it's a real method
    harmony: Harmony
    _step: Callable[[], Step]

    # anchor register for the melody; re-rooted on the rack's current chord
    # each note, in the octave nearest this note (see `note_root`)
    root_freq = Param(
        notes.A2,
        notes.A4,
        1,
        notes.A3,
        "Register",
        "Moves the melody up or down; low sits in the tenor range, high cuts through above the mix.",
        scale="note",
    )

    @Param(
        0.0,
        6000.0,
        50.0,
        1500.0,
        "Brightness",
        "How far the filter snaps open on each note; low stays dark and covered, high gives a brighter, more cutting attack.",
    )
    def brightness(self, value: float) -> None:
        self.filter_env.mul = value

    @Param(
        0.0,
        0.3,
        0.005,
        0.01,
        "Attack",
        "How quickly each note reaches full volume; near zero is a direct, percussive attack, higher softens the front of the note.",
    )
    def attack(self, value: float) -> None:
        self.amp_env.setAttack(value)

    @Param(
        0.2,
        1.0,
        0.05,
        1.0,
        "Sustain",
        "The held level of a note once it's past its attack; lower makes long notes fade under a held key.",
    )
    def sustain(self, value: float) -> None:
        self.amp_env.setSustain(value)
        self.filter_env.setSustain(value)

    @Param(
        0.0,
        1.0,
        0.02,
        0.0,
        "Vibrato",
        "Depth of a slow pitch wobble on the sustained note; 0 holds the pitch steady.",
    )
    def vibrato(self, value: float) -> None:
        self.pitch_vibrato.mul = value * 8.0

    @Param(
        0.0,
        0.8,
        0.05,
        0.0,
        "Drive",
        "Adds saturation warmth and edge; higher pushes the lead toward a grittier, more aggressive tone.",
    )
    def drive(self, value: float) -> None:
        self.shaped.drive = self.base_drive + value

    rate = rate_param(
        base_division,
        "Halves or doubles the phrase's speed for each step away from its 8th-note default.",
    )

    def note_root(self, clock: Clock) -> float:
        """This voice's current root pitch (Hz), re-rooted on the rack's
        current chord in the octave nearest `root_freq`."""
        return self.harmony.chord_freq(self.root_freq, clock.bar_index)

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony

        initial_root = self.note_root(context.clock)
        self.pitch1 = SigTo(
            value=initial_root * 2 ** (self.osc1_detune / 12), time=self.glide_time
        )
        self.pitch2 = SigTo(
            value=initial_root * 2 ** (self.osc2_detune / 12), time=self.glide_time
        )

        self.pitch_vibrato = LFO(freq=5.0, type=3, sharp=0.5, mul=0.0)
        self.osc1_freq = self.pitch1 + self.pitch_vibrato
        self.osc2_freq = self.pitch2 + self.pitch_vibrato

        # a plain sine LFO, muted (mul=0) whenever a style has no PWM; a
        # single always-built node keeps the graph identical across styles
        self.pwm = LFO(freq=self.pwm_rate, type=3, sharp=0.5, mul=self.pwm_depth)
        self.osc1_sharp = self.osc1_duty + self.pwm
        self.osc2_sharp = self.osc2_duty + self.pwm
        self.osc1 = LFO(freq=self.osc1_freq, sharp=self.osc1_sharp, type=PULSE_TYPE)
        self.osc2 = LFO(freq=self.osc2_freq, sharp=self.osc2_sharp, type=PULSE_TYPE)
        self.mixed = (self.osc1 + self.osc2) * 0.5

        self.filter_env = Adsr(
            attack=self.filter_attack,
            decay=0.2,
            sustain=1.0,
            release=self.filter_release,
            mul=self.filter_env_depth,
            add=self.filter_base,
        )
        self.filtered = MoogLP(
            self.mixed, freq=self.filter_env, res=self.filter_resonance
        )

        self.amp_env = Adsr(
            attack=self.amp_attack,
            decay=0.2,
            sustain=1.0,
            release=self.amp_release,
        )
        self.shaped = Disto(
            self.filtered, drive=self.base_drive, slope=0.7, mul=self.amp_env
        )
        self.voice_signal = self.shaped

        self.schedule(self.base_division, self.rate, context.clock)
        self._step = self.step_pattern(self.cycle, self.pattern)
        return self.finish(self.voice_signal)

    def next_step(self) -> None:
        # derived from the shared clock's own tick, not a local counter
        # that starts at 0 whenever this patch is built or restarted -
        # see `Clock.tick`'s docstring
        step = self._step()
        if not step.hit:
            self.amp_env.stop()
            self.filter_env.stop()
        else:
            target = self.note_root(self._clock) * 2 ** (step.value / 12)
            self.pitch1.value = target * 2 ** (self.osc1_detune / 12)
            self.pitch2.value = target * 2 ** (self.osc2_detune / 12)
            self.amp_env.play()
            self.filter_env.play()


class LeadBrass(Lead):
    """Detuned dual-pulse brass stab: LFO-widened duty cycle on both
    oscillators and a dark filter that snaps open on every note."""

    summary = "Detuned dual-pulse brass stab with an LFO-widened duty cycle and a snapping filter."
    osc1_detune, osc2_detune = -0.1, 12.1
    osc1_duty, osc2_duty = 0.5, 0.3
    pwm_rate, pwm_depth = 5.5, 0.2
    filter_base, filter_env_depth, filter_resonance = 200.0, 4000.0, 0.35
    filter_attack, filter_release = 0.03, 0.6
    amp_attack, amp_release = 0.0, 0.35
    glide_time = 0.0
    base_drive = 0.15


class LeadMellow70s(Lead):
    """Near-unison dual-square lead, no PWM, filter wide open, legato
    glide between notes for a smooth, vocal 70's synth-lead feel."""

    summary = "Near-unison dual-square legato lead with the filter wide open."
    osc1_detune, osc2_detune = -0.1, 0.1
    osc1_duty, osc2_duty = 0.5, 0.5
    pwm_rate, pwm_depth = 0.0, 0.0
    filter_base, filter_env_depth, filter_resonance = 18000.0, 0.0, 0.0
    filter_attack, filter_release = 0.0, 0.0
    amp_attack, amp_release = 0.0, 0.35
    glide_time = 0.02
    base_drive = 0.0


# 16th-note steps (one bar) -> semitones above the chord root, mostly rests
# (absent steps): a minor-pentatonic-ish phrase (root, minor 3rd, 5th, minor
# 7th) that leaves space after each two- or three-note idea, rather than
# filling every subdivision - see lofi/README.md, "The melody should often
# leave space after a phrase."
MUTED_KEYS_PATTERN = {0: 0, 3: 3, 6: 7, 8: 10, 11: 7, 13: 3}


class LeadMutedKeys(Lead):
    """Near-unison dual-pulse pair, no PWM, dark and narrow filter sweep, no
    drive: a soft, covered pluck rather than a synth lead - the rack's
    lofi lead-melody voice. Plays a sparse, rest-heavy pentatonic motif
    instead of the family's default arpeggio (see `MUTED_KEYS_PATTERN`)."""

    title = "Lead - Muted Keys"
    summary = "Soft, dark dual-pulse pluck playing a sparse, rest-heavy minor-pentatonic motif."
    base_division = NoteDivision.SIXTEENTH
    pattern = MUTED_KEYS_PATTERN
    cycle = 16
    osc1_detune, osc2_detune = -0.05, 0.05
    osc1_duty, osc2_duty = 0.5, 0.45
    pwm_rate, pwm_depth = 0.0, 0.0
    filter_base, filter_env_depth, filter_resonance = 900.0, 700.0, 0.15
    filter_attack, filter_release = 0.01, 0.5
    amp_attack, amp_release = 0.005, 0.6
    glide_time = 0.0
    base_drive = 0.0
    rate = rate_param(
        base_division,
        "Halves or doubles the phrase's speed for each step away from its 16th-note default.",
    )
