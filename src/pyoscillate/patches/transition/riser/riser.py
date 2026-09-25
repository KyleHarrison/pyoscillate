# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.transition.riser.riser style=noise
#   style: noise | shift | pitch
"""Tempo-locked riser: one ramp lifts pitch, brightness and level into a downbeat.

A single `Linseg` ramp (pyo example x05/05) runs from 0 to 1 over the riser's
length in bars and drops back to 0 on the phrase downbeat. Raising it to a
live power gives the curve, so Surge moves the energy early or late without
reshaping the table. That one curve drives every destination: the source's
climb, the low-pass opening towards Brightness, and the level.

- `noise`: a band of white noise whose centre climbs through the spectrum;
  pitchless, so it sits over any key.
- `shift`: a detuned saw fifth, single-sideband shifted up by a climbing
  number of Hz (x06/07). The partials move together by the same amount, so
  the chord turns inharmonic and metallic as it rises.
- `pitch`: the same detuned saw fifth gliding up by whole octaves.

The riser starts `length` bars before the end of each `PHRASE_BARS` phrase,
counted from when the patch starts. A Length change takes effect from the next
riser; one already in flight keeps its length and still lands on the downbeat.
"""

from __future__ import annotations

from collections.abc import Callable

from pyo.lib.arithmetic import Pow
from pyo.lib.controls import Linseg, SigTo
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise, SuperSaw

from pyoscillate.clock import Clock
from pyoscillate.patches.base import BuiltPatch
from pyoscillate.patches.common import frequency_shift
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

STYLES = ("noise", "shift", "pitch")

PARAMETERS = (
    SliderSpec(
        "length",
        1,
        8,
        1,
        4,
        "Length",
        "How many bars the build lasts before it lands on the next phrase downbeat; 8 fills the whole phrase.",
    ),
    SliderSpec(
        "climb",
        0.5,
        4,
        0.25,
        2,
        "Climb",
        "How far the riser travels, in octaves: low is a short lift, high is a full sweep from the floor to the top.",
        (PyoParamRef(Pow, "exponent"),),
    ),
    SliderSpec(
        "surge",
        0.5,
        4,
        0.1,
        2,
        "Surge",
        "Where the build puts its energy: low swells early and levels off, high holds back and surges in the last beats.",
        (PyoParamRef(Pow, "exponent"),),
    ),
    SliderSpec(
        "brightness",
        1000,
        16000,
        100,
        8000,
        "Brightness",
        "How open the riser is at its peak; low keeps it behind the mix, high makes it the brightest thing before the drop.",
        (PyoParamRef(Biquad, "freq"),),
    ),
    SliderSpec(
        "level",
        0,
        0.5,
        0.01,
        0.3,
        "Level",
        "How loud the riser is at its peak, just before the downbeat.",
    ),
)
PHRASE_BARS = 8
# the ramp's fall to zero on the downbeat: short enough to read as a cut,
# long enough not to click
CUT_SECONDS = 0.005
# the low-pass opens across this many octaves, ending at Brightness
OPEN_OCTAVES = 4
FILTER_Q = 0.7
# `noise`: where the band centre starts before it climbs, and its width
NOISE_START = 250
NOISE_Q = 1.2
# band-passing leaves much less energy than the saw sources; brings the noise
# wash up to their loudness at the default settings
NOISE_GAIN = 4.4
# `shift` / `pitch`: a root and fifth, as a detuned saw pair
ROOT = notes.A2
CHORD = [ROOT, ROOT * 1.5]
DETUNE = 0.5
BALANCE = 0.7
# `shift`: low-pass the saws before shifting, so partials pushed past Nyquist
# don't fold back as aliasing
PRE_SHIFT_CUTOFF = 4000
# keeps the loudest corner of the range under the output ceiling
VOLUME_DEFAULT = 0.3


def _ramp_points(tempo: Tempo, bars: int) -> list[tuple[float, float]]:
    """Break-points for one riser: 0 → 1 across `bars`, cut to 0 on the downbeat."""
    duration = tempo.bar * bars
    return [(0, 0), (duration - CUT_SECONDS, 1), (duration, 0)]


def build(
    tempo: Tempo,
    clock: Clock,
    style: str = "noise",
    length: float = 4,
    climb: float = 2,
    surge: float = 2,
    brightness: float = 8000,
    level: float = 0.3,
) -> BuiltPatch:
    """Build a riser that lands on every `PHRASE_BARS` downbeat; `style` picks the source."""
    if style not in STYLES:
        raise ValueError(f"unknown riser style {style!r}; expected one of {STYLES}")

    live = {
        name: SigTo(value=value, time=0.15, init=value)
        for name, value in {
            "climb": climb,
            "surge": surge,
            "brightness": brightness,
            "level": level,
        }.items()
    }
    state = {"bar": 0, "length": round(length)}
    ramp = Linseg(_ramp_points(tempo, state["length"]), initToFirstVal=True)
    tension = Pow(ramp, live["surge"])
    climb_octaves = tension * live["climb"]
    climb_ratio = Pow(2, climb_octaves)
    resources: list = [*live.values(), ramp, tension, climb_octaves, climb_ratio]

    if style == "noise":
        noise = Noise()
        centre = climb_ratio * NOISE_START
        # a constant-Q band passes bandwidth, and so noise power, in
        # proportion to its centre; 1/sqrt of the climb keeps the level on the
        # curve rather than on the climb, as the clap's makeup does
        makeup = Pow(climb_ratio, -0.5, mul=NOISE_GAIN)
        risen = Biquad(noise, freq=centre, q=NOISE_Q, type=2, mul=makeup)
        resources += [noise, centre, makeup, risen]
    elif style == "shift":
        chord = SuperSaw(freq=CHORD, detune=DETUNE, bal=BALANCE)
        chord_mono = chord.mix(1)
        prefiltered = Biquad(chord_mono, freq=PRE_SHIFT_CUTOFF, q=FILTER_Q, type=0)
        # the root climbs `climb` octaves; every other partial moves by the same Hz
        shift_ratio = climb_ratio - 1
        shift_hz = shift_ratio * ROOT
        shifted = frequency_shift(prefiltered, shift_hz)
        risen = shifted.output
        resources += [chord, chord_mono, prefiltered, shift_ratio, shift_hz, *shifted.resources, risen]
    else:
        chord_freqs = climb_ratio * CHORD
        chord = SuperSaw(freq=chord_freqs, detune=DETUNE, bal=BALANCE)
        risen = chord.mix(1)
        resources += [chord_freqs, chord, risen]

    # cutoff = Brightness × 2^(OPEN_OCTAVES × (tension − 1))
    open_octaves = tension * OPEN_OCTAVES
    opening = Pow(2, open_octaves)
    cutoff_floor = live["brightness"] * 2**-OPEN_OCTAVES
    cutoff = cutoff_floor * opening
    filtered = Biquad(risen, freq=cutoff, q=FILTER_Q, type=0)
    gain = tension * live["level"]
    voice = filtered * gain
    resources += [open_octaves, opening, cutoff_floor, cutoff, filtered, gain]

    def next_bar() -> None:
        if state["bar"] % PHRASE_BARS == PHRASE_BARS - state["length"]:
            ramp.setList(_ramp_points(tempo, state["length"]))
            ramp.play()
        state["bar"] += 1

    division = clock.subscribe(clock.bar, next_bar)

    def set_length(value: float) -> None:
        state["length"] = round(value)

    return BuiltPatch(
        sequencer=division,
        voice=voice,
        controls={
            "length": set_length,
            **{
                name: lambda value, control=control: setattr(control, "value", value)
                for name, control in live.items()
            },
        },
        resources=tuple(resources),
    )


def make_builder(style: str) -> Callable[..., BuiltPatch]:
    """Return a builder with one riser style fixed for a rack entry."""
    return lambda **values: build(style=style, **values)
