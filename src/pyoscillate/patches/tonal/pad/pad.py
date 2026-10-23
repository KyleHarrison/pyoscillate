# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pad.pad
#   style: dreams | wash | city | aurora | cathedral | chapel | portus | sweep | enceladus
"""Subtractive pads: two oscillators (and noise) through a resonant 24 dB
low-pass, held under a slow envelope, with one slow LFO moving the sound.

A pad here is a `Held` voice (see `common.py`): it holds the rack's chord (or a
line of its tones) and lets go over a long Release, and each chord is made of
detuned copies (`Ensemble`) so it shimmers. What the pad adds is the classic
subtractive recipe:

- two oscillators (saw, square or triangle), each its own pitch offset and
  level; the second can be hard-synced to the first, so its pitch sweeps a
  swirling, vowel-like sync tone;
- noise (Air), which on its own through a ringing filter is a pitched wash;
- a low-pass whose cutoff rests at Brightness, is swung open by its own
  envelope (Opening) on every chord, followed by key tracking if the style
  asks for it, and rings at Resonance;
- one slow LFO (Movement, Movement speed) routed where the style wants it:
  pulse width of the square oscillators, the filter cutoff, the level, the
  second oscillator's pitch (the sync sweep) or the resonance.

The nine styles are the recipes of the cookbook's pad section, each only
profile data on the shared graph. Oscillator offsets are in semitones from the
played note, levels in dB, and the filter cutoff is held as the cookbook's knob
position: 20 Hz to 20 kHz across 0 to 1, logarithmically.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix, Pow, Wrap
from pyo.lib.controls import Adsr, SigTo
from pyo.lib.dynamics import Clip
from pyo.lib.effects import Delay
from pyo.lib.filters import MoogLP
from pyo.lib.generators import LFO, Noise, Phasor
from pyo.lib.tableprocess import Pointer
from pyo.lib.tables import HarmTable, SawTable, SquareTable

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import Ensemble, Phrased, Reverb, Stage
from pyoscillate.patches.params import Param
from pyoscillate.theory.chord import Chord, Chords
from pyoscillate.theory.phrase import PhraseRole, Rhythms
from pyoscillate.theory.pitch import Note


class Wave(Enum):
    """The three oscillator shapes of a pad recipe, as the LFO type pyo plays
    (a square is a pulse built from two saws, see `oscillator`) and the table
    a synced oscillator reads."""

    SAW = 0
    SQUARE = 2
    TRIANGLE = 3

    def oscillator(
        self, freq: PyoObject, duty: PyoObject, mul: PyoObject, max_period: float
    ) -> Stage:
        """One band-limited oscillator, a stream per voice. A square is a pulse
        whose width is `duty` (0.5 is a square), the others ignore it; `max_period`
        is the longest period (s) a pulse can have. pyo's
        own pulse is no duty-cycle square (it sounds an octave up with a DC
        offset), so the pulse is a sawtooth minus itself delayed by `duty` of
        a period: zero-mean and as band-limited as the sawtooth."""
        if self is not Wave.SQUARE:
            tone = LFO(freq=freq, sharp=1.0, type=self.value, mul=mul)
            return Stage(tone, (tone,))
        saw = LFO(freq=freq, sharp=1.0, type=Wave.SAW.value)
        period = Pow(freq, -1)
        offset = period * duty
        late = Delay(saw, delay=offset, maxdelay=max_period)
        edges = saw - late
        pulse = edges * mul
        return Stage(pulse, (saw, period, offset, late, edges, pulse))

    def table(self) -> PyoObject:
        """One cycle of the wave, for an oscillator that is read at a phase
        another sets (hard sync)."""
        if self is Wave.SAW:
            return SawTable(order=32)
        if self is Wave.SQUARE:
            return SquareTable(order=32)
        return HarmTable(
            [
                (1 / n**2) * (-1) ** ((n - 1) // 2) if n % 2 else 0.0
                for n in range(1, 33)
            ]
        )


class SynthPad(Reverb, Ensemble):
    """Subtractive pad: oscillators and noise into a resonant low-pass whose
    cutoff an envelope and a slow LFO move, held under a slow amplitude
    envelope. A style supplies the recipe as class data and its own starting
    values for the shared sliders; the graph is the same for all."""

    copies: ClassVar[int] = 2
    chord_shape: ClassVar[Chord | None] = Chords.TRIAD
    volume = Patch.volume.replace(default=0.3)

    # cutoff knob: 0 is CUTOFF_FLOOR Hz, 1 is CUTOFF_FLOOR * CUTOFF_SPAN Hz
    CUTOFF_FLOOR: ClassVar[float] = 20.0
    CUTOFF_SPAN: ClassVar[float] = 1000.0
    # the widest the pulse of a square swings either side of a half duty at
    # full PWM depth, and the loudest resonance the filter is allowed
    PWM_SPAN: ClassVar[float] = 0.45
    RESONANCE_MAX: ClassVar[float] = 1.2
    # the longest period a pulse can have (s): the lowest note a pad plays is
    # well above 10 Hz
    MAX_PERIOD: ClassVar[float] = 0.1
    # the highest the filter opens (Hz), under pyo's Nyquist
    CUTOFF_CEILING: ClassVar[float] = 10000.0
    # a voice's level at the mix: the oscillators of a chord add in power
    GAIN: ClassVar[float] = 0.2
    # seconds the sliders take to move the graph, so none zippers
    control_glide: ClassVar[float] = 0.05

    # per-style recipe: each oscillator's shape, offset (semitones from the
    # note) and level (dB); None leaves it out
    osc1_wave: ClassVar[Wave | None]
    osc2_wave: ClassVar[Wave | None]
    osc1_semitones: ClassVar[float] = 0.0
    osc2_semitones: ClassVar[float] = 0.0
    osc1_db: ClassVar[float] = 0.0
    osc2_db: ClassVar[float] = 0.0
    # osc2 hard-synced to osc1: its pitch is the sweep of the sync tone
    hard_sync: ClassVar[bool] = False
    # the LFO's shape (a pyo LFO type) and where it goes, each a depth at
    # full Movement: pulse width (fraction of PWM_SPAN), cutoff (of the knob's
    # travel), level (fraction), osc2's pitch (semitones) and the resonance
    motion_shape: ClassVar[int] = 3
    pwm_depth: ClassVar[float] = 0.0
    cutoff_motion: ClassVar[float] = 0.0
    amp_motion: ClassVar[float] = 0.0
    pitch_motion: ClassVar[float] = 0.0
    resonance_motion: ClassVar[float] = 0.0
    # how closely the cutoff follows the note's pitch: 0 stays put, 1 is in
    # step with it (a chord's intervals survive a ringing filter)
    tracking: ClassVar[float] = 0.0
    # the filter envelope, seconds and a sustain fraction; the amplitude
    # envelope's decay (seconds) and sustain fraction
    filter_attack: ClassVar[float] = 0.01
    filter_decay: ClassVar[float] = 0.01
    filter_sustain: ClassVar[float] = 1.0
    filter_release: ClassVar[float] = 0.5
    note_decay = 0.05
    amp_sustain: ClassVar[float] = 1.0

    base_pos: SigTo
    depth: SigTo
    res_level: SigTo
    noise_level: SigTo
    movement_level: SigTo
    motion: LFO
    motion_scaled: PyoObject
    filter_env: Adsr
    pitch_exponent: PyoObject
    pitch_wobble: PyoObject
    pwm_shift: PyoObject
    duty: PyoObject
    osc1_freq: PyoObject
    osc2_freq: PyoObject
    osc1_gain: PyoObject
    osc2_gain: PyoObject
    osc1: PyoObject
    osc2: PyoObject
    osc1_table: PyoObject
    osc2_table: PyoObject
    master_phase: Phasor
    sync_ratio: PyoObject
    sync_ramp: PyoObject
    sync_phase: PyoObject
    noise_gain: PyoObject
    hiss: Noise
    source_sum: PyoObject
    cutoff_travel: PyoObject
    cutoff_pos: PyoObject
    cutoff_clip: PyoObject
    cutoff_hz: PyoObject
    key_track: PyoObject
    voice_cutoff: PyoObject
    voice_cutoff_clip: PyoObject
    res_swing: PyoObject
    res_signal: PyoObject
    filtered: MoogLP
    filtered_mix: Mix
    amp_swing: PyoObject
    amp_wobble: PyoObject
    swelled: PyoObject

    phrase_roles = (PhraseRole.CHORD_HIT,)
    phrase = Phrased.phrase.replace(
        default=Rhythms.BAR_PULSE,
        help_text="Picks when in the bar the chord is sounded, from one held chord a bar to a backbeat or a "
        "swung pulse; every voice draws on the same shared patterns.",
    )
    root_freq = Ensemble.root_freq.replace(
        help_text="Moves the whole chord up or down; low is a dark, heavy bed, high is a thin, bright, floating one.",
    )
    legato = Ensemble.legato.replace(default=0.9)
    spread = Ensemble.spread.replace(default=7)
    reverb_size = Reverb.reverb_size.replace(default=0.75)
    reverb_bal = Reverb.reverb_bal.replace(default=0.35)

    @Param(
        40,
        16000,
        0.02,
        2400,
        "Brightness",
        "How open the pad's filter rests; low is a dark, muffled, distant pad, high is a bright, buzzy, airy one.",
        scale="cutoff",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.base_pos.value = math.log(value / self.CUTOFF_FLOOR) / math.log(
            self.CUTOFF_SPAN
        )

    @Param(
        0,
        1,
        0.05,
        0,
        "Opening",
        "How far the filter swells open on every chord; none keeps the tone as set, high blooms from dark to bright as the chord arrives.",
        sweep=True,
    )
    def opening(self, value: float) -> None:
        self.depth.value = value

    @Param(
        0,
        1,
        0.05,
        0,
        "Resonance",
        "How strongly the filter rings at its cutoff; none is smooth and round, a lot is a vocal, whistling edge that sings as the filter moves.",
        sweep=True,
    )
    def resonance(self, value: float) -> None:
        self.res_level.value = value

    @Param(
        0,
        1,
        0.05,
        0,
        "Air",
        "How much breath-like noise is mixed under the tone; none is clean, a little is a soft hiss, a lot is a wash of noise.",
        sweep=True,
    )
    def air(self, value: float) -> None:
        self.noise_level.value = value

    @Param(
        0,
        1.5,
        0.05,
        1.0,
        "Movement",
        "How far the slow motion travels (the width of the pulse, the filter, the level or the pitch, as the pad is built); none holds the pad still, a lot makes it sway and swirl.",
        sweep=True,
    )
    def movement(self, value: float) -> None:
        self.movement_level.value = value

    @Param(
        0.05,
        8,
        0.05,
        1.0,
        "Movement speed",
        "How fast the slow motion cycles, in times a second; slow is a tide, fast is a shimmer.",
        sweep=True,
        advanced=True,
    )
    def movement_speed(self, value: float) -> None:
        self.motion.freq = value

    @classmethod
    def voice_trim(cls) -> float:
        """The level each oscillator is trimmed to before the filter: the
        voices of a chord add in power, and a quiet signal keeps the resonant
        filter well inside its stable range."""
        return cls.GAIN / cls.voice_count() ** 0.5

    @classmethod
    def linear(cls, db: float) -> float:
        """A level in dB as the amplitude it multiplies by."""
        return 10 ** (db / 20)

    def make_tone(self) -> PyoObject:
        self.base_pos = SigTo(value=0.5, time=self.control_glide)
        self.depth = SigTo(value=0, time=self.control_glide)
        self.res_level = SigTo(value=0, time=self.control_glide)
        self.noise_level = SigTo(value=0, time=self.control_glide)
        self.movement_level = SigTo(value=1, time=self.control_glide)
        self.motion = LFO(freq=1.0, type=self.motion_shape, sharp=0.5)
        self.motion_scaled = self.motion * self.movement_level
        self.filter_env = Adsr(
            attack=self.filter_attack,
            decay=self.filter_decay,
            sustain=self.filter_sustain,
            release=self.filter_release,
        )

        self.pitch_exponent = self.motion_scaled * (self.pitch_motion / 12)
        self.pitch_wobble = Pow(2, self.pitch_exponent)
        self.pwm_shift = self.motion_scaled * (self.pwm_depth * self.PWM_SPAN)
        self.duty = self.pwm_shift + 0.5

        stages: list[PyoObject] = []
        if self.osc1_wave:
            self.osc1_freq = self.held_pitch * Note.semitone_ratio(self.osc1_semitones)
            self.osc1_gain = self.voice_gain * (
                self.linear(self.osc1_db) * self.voice_trim()
            )
            stage = self.osc1_wave.oscillator(
                self.osc1_freq, self.duty, self.osc1_gain, self.MAX_PERIOD
            )
            self.osc1 = stage.output
            self.retain(*stage.resources)
            stages.append(self.osc1)
        if self.osc2_wave:
            self.osc2_gain = self.voice_gain * (
                self.linear(self.osc2_db) * self.voice_trim()
            )
            ratio = Note.semitone_ratio(self.osc2_semitones)
            if self.hard_sync:
                # the slave reads its table at the master's phase times the
                # pitch ratio, wrapped, so it restarts with every master cycle
                self.master_phase = Phasor(
                    freq=self.held_pitch * Note.semitone_ratio(self.osc1_semitones)
                )
                self.sync_ratio = self.pitch_wobble * (
                    ratio / Note.semitone_ratio(self.osc1_semitones)
                )
                self.sync_ramp = self.master_phase * self.sync_ratio
                self.sync_phase = Wrap(self.sync_ramp, min=0, max=1)
                self.osc2_table = self.osc2_wave.table()
                self.osc2 = Pointer(
                    self.osc2_table, self.sync_phase, mul=self.osc2_gain
                )
            else:
                self.osc2_freq = self.held_pitch * self.pitch_wobble * ratio
                stage = self.osc2_wave.oscillator(
                    self.osc2_freq, self.duty, self.osc2_gain, self.MAX_PERIOD
                )
                self.osc2 = stage.output
                self.retain(*stage.resources)
            stages.append(self.osc2)
        self.noise_gain = self.voice_gain * self.noise_level * self.voice_trim()
        self.hiss = Noise(mul=self.noise_gain)
        stages.append(self.hiss)

        # the sources add voice by voice: every partial sum is kept alive
        sums = [stages[0]]
        for stage in stages[1:]:
            sums.append(sums[-1] + stage)
        self.retain(*sums)
        self.source_sum = sums[-1]

        self.cutoff_travel = self.filter_env * self.depth
        self.cutoff_pos = (
            self.base_pos + self.cutoff_travel + self.motion_scaled * self.cutoff_motion
        )
        self.cutoff_clip = Clip(self.cutoff_pos, min=0, max=1)
        self.cutoff_hz = Pow(self.CUTOFF_SPAN, self.cutoff_clip, mul=self.CUTOFF_FLOOR)
        self.key_track = Pow(self.held_pitch * (1 / Note.A3), self.tracking)
        self.voice_cutoff = self.cutoff_hz * self.key_track
        self.voice_cutoff_clip = Clip(
            self.voice_cutoff, min=self.CUTOFF_FLOOR, max=self.CUTOFF_CEILING
        )
        # a square LFO taking the resonance away on its high half is the
        # cookbook's resonance modulation: it swings from rung to damped
        self.res_swing = (self.motion_scaled + 1) * (self.resonance_motion * 0.5)
        self.res_signal = Clip(
            self.res_level - self.res_swing, min=0, max=self.RESONANCE_MAX
        )
        self.filtered = MoogLP(
            self.source_sum, freq=self.voice_cutoff_clip, res=self.res_signal
        )
        self.filtered_mix = Mix(self.filtered, voices=1)

        self.amp_swing = (self.motion_scaled + 1) * (self.amp_motion * -0.5)
        self.amp_wobble = self.amp_swing + 1
        self.swelled = self.filtered_mix * self.amp_wobble
        return self.swelled

    def voice_stage(self, signal: PyoObject) -> PyoObject:
        self.note_env.sustain = self.amp_sustain
        self.reverb = self.add_reverb(signal)
        return self.reverb

    def on_attack(self) -> None:
        self.filter_env.play()

    def check_lift(self) -> None:
        lifting = (
            self._release_tick is not None and self._clock.tick >= self._release_tick
        )
        super().check_lift()
        if lifting:
            self.filter_env.stop()


class AndroidDreams(SynthPad):
    """Android Dreams: a low square and a synced sawtooth swirling under a
    breath of noise, the sync sweeping slowly while the pulse and the filter
    sway; a soft, strange, electronic lullaby."""

    title = "Android Dreams"
    summary = "Swirling synced-oscillator pad with a breath of noise, a slow dream."

    osc1_wave = Wave.SQUARE
    osc2_wave = Wave.SAW
    osc1_semitones = -24.0
    osc2_semitones = -1.0
    hard_sync = True
    pwm_depth = 1.0
    cutoff_motion = 0.10
    pitch_motion = 3.0

    volume = SynthPad.volume.replace(default=0.2)
    brightness = SynthPad.brightness.replace(default=2400)
    resonance = SynthPad.resonance.replace(default=0.3)
    air = SynthPad.air.replace(default=0.5)
    movement_speed = SynthPad.movement_speed.replace(default=0.25)
    attack = SynthPad.attack.replace(default=0.45)
    release = SynthPad.release.replace(default=2.25)


class CelestialWash(SynthPad):
    """Celestial Wash: no oscillators, only noise through a filter that rings
    at the note, pulsing as its resonance is switched on and off, swelling in
    and fading away while the chord is held."""

    title = "Celestial Wash"
    summary = "Pitched noise wash that swells, pulses and fades, with no oscillators."

    osc1_wave = None
    osc2_wave = None
    motion_shape = 2
    resonance_motion = 1.0
    tracking = 1.0
    note_decay = 5.85
    amp_sustain = 0.0

    volume = SynthPad.volume.replace(default=1.2)
    brightness = SynthPad.brightness.replace(default=1000)
    resonance = SynthPad.resonance.replace(default=1.0)
    air = SynthPad.air.replace(default=1.0)
    movement_speed = SynthPad.movement_speed.replace(default=5.5)
    attack = SynthPad.attack.replace(default=1.65)
    release = SynthPad.release.replace(maximum=6.0, default=4.4)


class DarkCity(SynthPad):
    """Dark City: a square two octaves down and a sawtooth a seventh under the
    note, a dark filter that takes five seconds to open and a pulse that
    breathes; a looming, nocturnal bed."""

    title = "Dark City"
    summary = "Deep, brooding pad whose dark filter slowly opens and settles."

    osc1_wave = Wave.SQUARE
    osc2_wave = Wave.SAW
    osc1_semitones = -24.0
    osc2_semitones = -11.92
    pwm_depth = 1.0
    filter_attack = 5.15
    filter_decay = 6.35
    filter_sustain = 0.5
    filter_release = 5.2
    note_decay = 3.9
    amp_sustain = 0.7

    volume = SynthPad.volume.replace(default=0.25)
    brightness = SynthPad.brightness.replace(default=300)
    opening = SynthPad.opening.replace(default=0.75)
    movement_speed = SynthPad.movement_speed.replace(default=4.0)
    attack = SynthPad.attack.replace(default=0.005)
    release = SynthPad.release.replace(maximum=8.0, default=6.35)


class Aurora(SynthPad):
    """Aurora: two squares a few cents either side of the note, their pulses
    swaying, through a ringing filter that opens over a second and a half; the
    shimmering curtain of a polar sky."""

    title = "Aurora"
    summary = "Shimmering pulse-width pad that opens like a curtain of light."

    osc1_wave = Wave.SQUARE
    osc2_wave = Wave.SQUARE
    osc1_semitones = 0.10
    osc2_semitones = -0.10
    pwm_depth = 0.9
    filter_attack = 1.5
    filter_decay = 0.5

    brightness = SynthPad.brightness.replace(default=40)
    opening = SynthPad.opening.replace(default=0.5)
    resonance = SynthPad.resonance.replace(default=0.65)
    movement_speed = SynthPad.movement_speed.replace(default=4.0)
    attack = SynthPad.attack.replace(default=0.6)
    release = SynthPad.release.replace(default=0.6)


class GalacticCathedral(SynthPad):
    """Galactic Cathedral: two squares, the second two octaves up and quieter,
    a ringing filter drifting open and shut on a very slow tide and a long
    release; a vast, stone, stained-glass stack."""

    title = "Galactic Cathedral"
    summary = "Vast, ringing two-octave pulse pad with a slow tide in its filter."

    osc1_wave = Wave.SQUARE
    osc2_wave = Wave.SQUARE
    osc1_semitones = -0.11
    osc2_semitones = 24.11
    osc2_db = -6.0
    cutoff_motion = 0.10

    brightness = SynthPad.brightness.replace(default=1200)
    resonance = SynthPad.resonance.replace(default=0.6)
    movement_speed = SynthPad.movement_speed.replace(default=0.3)
    attack = SynthPad.attack.replace(default=0.4)
    release = SynthPad.release.replace(default=2.25)


class GalacticChapel(SynthPad):
    """Galactic Chapel: two triangles an octave apart, the filter and the
    level drifting together on a very slow tide; the hushed, intimate cousin of
    the cathedral."""

    title = "Galactic Chapel"
    summary = "Hushed, soft triangle pad with the level and filter slowly swaying."

    osc1_wave = Wave.TRIANGLE
    osc2_wave = Wave.TRIANGLE
    osc2_semitones = 12.0
    osc2_db = -6.0
    cutoff_motion = 0.10
    amp_motion = 0.17

    brightness = SynthPad.brightness.replace(default=1400)
    resonance = SynthPad.resonance.replace(default=0.65)
    movement_speed = SynthPad.movement_speed.replace(default=0.3)
    attack = SynthPad.attack.replace(default=0.35)
    release = SynthPad.release.replace(default=2.25)


class Portus(SynthPad):
    """Portus: two triangles an octave apart that glide slowly from chord to
    chord, through a ringing filter that blooms open over almost two seconds; a
    drifting, harbour-lights sound."""

    title = "Portus"
    summary = "Slow, gliding triangle pad whose ringing filter blooms on each chord."

    osc1_wave = Wave.TRIANGLE
    osc2_wave = Wave.TRIANGLE
    osc2_semitones = 12.0
    filter_attack = 1.8
    filter_decay = 0.5
    filter_release = 2.9

    brightness = SynthPad.brightness.replace(default=75)
    opening = SynthPad.opening.replace(default=0.7)
    resonance = SynthPad.resonance.replace(default=0.7)
    glide = SynthPad.glide.replace(maximum=2.0, default=1.5)
    attack = SynthPad.attack.replace(default=1.5)
    release = SynthPad.release.replace(maximum=4.0, default=3.3)


class PostApocalypticSyncSweep(SynthPad):
    """Post-Apocalyptic Sync Sweep: two low squares, the second hard-synced to
    the first with its pitch swinging far either way, under a ringing filter
    that opens over two seconds and closes again; a rusted, grinding sky."""

    title = "Post-Apocalyptic Sync Sweep"
    summary = "Grinding hard-sync pad whose pitch sweeps and filter opens and closes."

    osc1_wave = Wave.SQUARE
    osc2_wave = Wave.SQUARE
    osc1_semitones = -24.0
    osc2_semitones = -12.0
    osc2_db = -6.0
    hard_sync = True
    pitch_motion = 4.5
    filter_attack = 2.1
    filter_decay = 5.2
    filter_sustain = 0.0
    filter_release = 3.0

    brightness = SynthPad.brightness.replace(default=40)
    opening = SynthPad.opening.replace(default=0.5)
    resonance = SynthPad.resonance.replace(default=0.65)
    movement_speed = SynthPad.movement_speed.replace(default=0.7)
    attack = SynthPad.attack.replace(default=0.005)
    release = SynthPad.release.replace(default=0.6)


class TerraEnceladus(SynthPad):
    """Terra Enceladus: a sawtooth over a square an octave down, the square's
    pulse width swaying on a slow tide; an icy, alien, glassy bed."""

    title = "Terra Enceladus"
    summary = "Cold sawtooth-and-pulse pad with the pulse width slowly swaying."

    osc1_wave = Wave.SAW
    osc2_wave = Wave.SQUARE
    osc2_semitones = -12.0
    osc2_db = -3.0
    pwm_depth = 1.0

    volume = SynthPad.volume.replace(default=0.25)
    brightness = SynthPad.brightness.replace(default=1300)
    movement_speed = SynthPad.movement_speed.replace(default=1.75)
    attack = SynthPad.attack.replace(default=0.4)
    release = SynthPad.release.replace(default=2.25)
