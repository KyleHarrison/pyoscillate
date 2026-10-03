# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.transition.riser.riser
#   style: noise | shift | pitch
"""Tempo-locked riser: one ramp lifts pitch, brightness and level into a downbeat.

A single `Linseg` ramp (pyo example x05/05) runs from 0 to 1 over the riser's
length in bars and drops back to 0 on the phrase downbeat. Raising it to a
live power gives the curve, so Surge moves the energy early or late without
reshaping the table. That one curve drives every destination: the source's
climb, the low-pass opening towards Brightness, and the level.

- `noise` (`RiserNoise`): a band of white noise whose centre climbs through
  the spectrum; pitchless, so it sits over any key.
- `shift` (`RiserShift`): a detuned saw fifth, single-sideband shifted up by
  a climbing number of Hz (x06/07). The partials move together by the same
  amount, so the chord turns inharmonic and metallic as it rises.
- `pitch` (`RiserPitch`): the same detuned saw fifth gliding up by whole
  octaves.

The riser starts `length` bars before the end of each `PHRASE_BARS` phrase,
counted from when the patch starts. A Length change takes effect from the next
riser; one already in flight keeps its length and still lands on the downbeat.

All three styles share the ramp, curve, filter opening and level stage
(`Riser.build`); only the climbing source in `rising_source()` differs, since
that is genuinely different behavior, not just different profile data
(`patches/AGENTS.md`'s design rule 1).

This is a one-shot gesture rather than a repeating clocked hit, so there is
no Rate slider: `build()` subscribes `next_bar()` directly to `clock.bar`
(one tick per bar) instead of going through `GatedVoice.schedule()`'s
rate machinery, and `Length` only ever changes when the next riser
starts, read straight off `self.length` with no mirrored state.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.arithmetic import Pow
from pyo.lib.controls import Linseg, SigTo
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise, SuperSaw

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Gate, GatedVoice, frequency_shift
from pyoscillate.patches.params import Param
from pyoscillate.tempo import Tempo
from pyoscillate.theory import notes

STYLES = ("noise", "shift", "pitch")
PHRASE_BARS = 8
# `shift` / `pitch`: a root and fifth, as a detuned saw pair
ROOT = notes.A2
CHORD = [ROOT, ROOT * 1.5]
DETUNE = 0.5
BALANCE = 0.7


def _ramp_points(
    tempo: Tempo, bars: int, cut_seconds: float
) -> list[tuple[float, float]]:
    """Break-points for one riser: 0 → 1 across `bars`, cut to 0 on the downbeat."""
    duration = tempo.bar * bars
    return [(0, 0), (duration - cut_seconds, 1), (duration, 0)]


class Riser(Gate, GatedVoice):
    """Tempo-locked riser: one ramp lifts pitch, brightness and level into a
    downbeat. Style variants subclass this and override `rising_source()`;
    the ramp, curve, filter opening and level stage are identical. See the
    module docstring for the sonic detail."""

    volume = Patch.volume.replace(default=0.3)

    # the ramp's fall to zero on the downbeat: short enough to read as a cut,
    # long enough not to click
    cut_seconds: ClassVar[float] = 0.005
    # the low-pass opens across this many octaves, ending at Brightness
    octave_span: ClassVar[float] = 4
    filter_q: ClassVar[float] = 0.7

    # the graph, assigned by build(); finish() retains every one of them
    climb_control: SigTo
    surge_control: SigTo
    brightness_control: SigTo
    level_control: SigTo
    ramp: Linseg
    tension: Pow
    climb_octaves: PyoObject
    climb_ratio: Pow
    risen: PyoObject
    open_octaves: PyoObject
    opening: Pow
    cutoff_floor: PyoObject
    cutoff: PyoObject
    filtered: Biquad
    gain: PyoObject
    voice_signal: PyoObject
    _bar: int
    _tempo: Tempo

    # only read at the top of each bar (next_bar()), so it needs no live
    # control - assigning the parameter already keeps self.length current
    length = Param(
        1,
        8,
        1,
        4,
        "Length",
        "How many bars the build lasts before it lands on the next phrase downbeat; 8 fills the whole phrase.",
    )

    @Param(
        0.5,
        4,
        0.25,
        2,
        "Climb",
        "How far the riser travels, in octaves: low is a short lift, high is a full sweep from the floor to the top.",
        sweep=True,
    )
    def climb(self, value: float) -> None:
        self.climb_control.value = value

    @Param(
        0.5,
        4,
        0.1,
        2,
        "Surge",
        "Where the build puts its energy: low swells early and levels off, high holds back and surges in the last beats.",
        sweep=True,
    )
    def surge(self, value: float) -> None:
        self.surge_control.value = value

    @Param(
        1000,
        16000,
        100,
        8000,
        "Brightness",
        "How open the riser is at its peak; low keeps it behind the mix, high makes it the brightest thing before the drop.",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.brightness_control.value = value

    @Param(
        0,
        0.5,
        0.01,
        0.3,
        "Level",
        "How loud the riser is at its peak, just before the downbeat.",
    )
    def level(self, value: float) -> None:
        self.level_control.value = value

    def rising_source(self, climb_ratio: PyoObject) -> None:
        """This style's climbing source, built from `climb_ratio` (2 **
        octaves the ramp has travelled so far) and assigned to `self.risen`
        (plus any other nodes it needs, also assigned to `self`). Overridden
        per style."""
        raise NotImplementedError

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self._bar = 0
        self._tempo = context.tempo

        self.climb_control = SigTo(value=self.climb, time=0.15, init=self.climb)
        self.surge_control = SigTo(value=self.surge, time=0.15, init=self.surge)
        self.brightness_control = SigTo(
            value=self.brightness, time=0.15, init=self.brightness
        )
        self.level_control = SigTo(value=self.level, time=0.15, init=self.level)

        self.ramp = Linseg(
            _ramp_points(context.tempo, round(self.length), self.cut_seconds),
            initToFirstVal=True,
        )
        self.tension = Pow(self.ramp, self.surge_control)
        self.climb_octaves = self.tension * self.climb_control
        self.climb_ratio = Pow(2, self.climb_octaves)

        self.rising_source(self.climb_ratio)

        # cutoff = Brightness × 2^(octave_span × (tension − 1))
        self.open_octaves = self.tension * self.octave_span
        self.opening = Pow(2, self.open_octaves)
        self.cutoff_floor = self.brightness_control * 2**-self.octave_span
        self.cutoff = self.cutoff_floor * self.opening
        self.filtered = Biquad(self.risen, freq=self.cutoff, q=self.filter_q, type=0)
        self.gain = self.tension * self.level_control
        self.voice_signal = self.filtered * self.gain

        # one tick per bar, not a `NoteDivision` rate
        self.schedule_steps(context.clock, context.clock.bar, self.next_bar)
        return self.finish(self.add_gate(self.voice_signal, context))

    def next_bar(self) -> None:
        length = round(self.length)
        if self._bar % PHRASE_BARS == PHRASE_BARS - length:
            self.ramp.setList(_ramp_points(self._tempo, length, self.cut_seconds))
            self.ramp.play()
        self._bar += 1


class RiserNoise(Riser):
    """Band of white noise whose centre climbs through the spectrum;
    pitchless, so it sits over any key."""

    title = "Riser - Noise"

    # `noise`: where the band centre starts before it climbs, and its width
    noise_start: ClassVar[float] = 250
    noise_q: ClassVar[float] = 1.2
    # band-passing leaves much less energy than the saw sources; brings the
    # noise wash up to their loudness at the default settings
    noise_gain: ClassVar[float] = 4.4

    noise: Noise
    noise_centre: PyoObject
    noise_makeup: Pow

    def rising_source(self, climb_ratio: PyoObject) -> None:
        self.noise = Noise()
        self.noise_centre = climb_ratio * self.noise_start
        # a constant-Q band passes bandwidth, and so noise power, in
        # proportion to its centre; 1/sqrt of the climb keeps the level on the
        # curve rather than on the climb, as the clap's makeup does
        self.noise_makeup = Pow(climb_ratio, -0.5, mul=self.noise_gain)
        self.risen = Biquad(
            self.noise,
            freq=self.noise_centre,
            q=self.noise_q,
            type=2,
            mul=self.noise_makeup,
        )


class RiserShift(Riser):
    """Detuned saw fifth, single-sideband shifted up by a climbing number of
    Hz. The partials move together by the same amount, so the chord turns
    inharmonic and metallic as it rises."""

    title = "Riser - Shift"

    # low-pass the saws before shifting, so partials pushed past Nyquist
    # don't fold back as aliasing
    pre_shift_cutoff: ClassVar[float] = 4000

    chord_source: SuperSaw
    chord_mono: PyoObject
    prefiltered: Biquad
    shift_ratio: PyoObject
    shift_hz: PyoObject

    def rising_source(self, climb_ratio: PyoObject) -> None:
        self.chord_source = SuperSaw(freq=CHORD, detune=DETUNE, bal=BALANCE)
        self.chord_mono = self.chord_source.mix(1)
        self.prefiltered = Biquad(
            self.chord_mono, freq=self.pre_shift_cutoff, q=self.filter_q, type=0
        )
        # the root climbs `climb` octaves; every other partial moves by the same Hz
        self.shift_ratio = climb_ratio - 1
        self.shift_hz = self.shift_ratio * ROOT
        shifted = frequency_shift(self.prefiltered, self.shift_hz)
        self.risen = shifted.output
        self.retain(*shifted.resources)


class RiserPitch(Riser):
    """The same detuned saw fifth gliding up by whole octaves."""

    title = "Riser - Pitch"

    chord_freqs: PyoObject
    chord_source: SuperSaw

    def rising_source(self, climb_ratio: PyoObject) -> None:
        self.chord_freqs = climb_ratio * CHORD
        self.chord_source = SuperSaw(freq=self.chord_freqs, detune=DETUNE, bal=BALANCE)
        self.risen = self.chord_source.mix(1)
