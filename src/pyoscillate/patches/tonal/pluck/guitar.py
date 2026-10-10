# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pluck.guitar
"""Guitars: a plucked steel string through a hollow body (with a 12-string's
octave strings to blend in), or a bright string pushed through a saturating
amplifier with a tremolo and a speaker. Both are `PluckedString` (see
`string.py` for the string itself); the style is what follows it."""

from __future__ import annotations

from pyo import PyoObject
from pyo.lib.effects import Disto
from pyo.lib.filters import ButLP
from pyo.lib.generators import Sine

from pyoscillate.patches.common import Body
from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.pluck.string import Courses, PluckedString
from pyoscillate.theory.phrase import Hooks
from pyoscillate.theory.pitch import Note


class GuitarAcoustic(Courses, Body, PluckedString):
    """Steel-string acoustic guitar: a plucked string through a hollow wooden
    body, ringing and mellowing on the chord tones, with octave strings a
    12-string adds when Doubling is raised."""

    title = "Guitar - Acoustic"
    summary = "Warm, ringing acoustic-guitar figure outlining the rack's chords."

    # the 12-string's octave strings, there only as far as Doubling brings them in
    courses = ((1.0, 1.0), (2.0, 0.6))
    # the body's loudest resonances: the air inside, the top plate and its
    # next mode, each an octave apart
    body_modes = (Note.G2, Note.G3, Note.G4)
    body_q = (6, 8, 8)
    click_freq = 2500

    # a flat pick, a lively hand and a little of the pick's own sound
    hardness = PluckedString.hardness.replace(default=0.5)
    dynamics = PluckedString.dynamics.replace(default=0.6)
    looseness = PluckedString.looseness.replace(default=0.25)
    pick_noise = PluckedString.pick_noise.replace(default=0.25)
    # a six-string until the octave strings are brought in
    doubling = Courses.doubling.replace(
        default=0,
        help_text="Brings in the octave strings of a 12-string guitar; none is a plain six-string, full is the bright, chiming shimmer of a 12-string.",
    )
    spread = Courses.spread.replace(
        help_text="How far the 12-string's octave strings are out of tune with the main strings; none is clean and chiming, a little is a lush, chorused shimmer.",
    )

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(string)


class GuitarElectric(PluckedString):
    """Electric guitar: a bright, long-ringing string pushed through a
    saturating amplifier whose crunch swells as the note dies away, with a
    tremolo and a speaker cabinet."""

    title = "Guitar - Electric"
    summary = "Bright, singing electric-guitar figure outlining the rack's chords."

    amp: Disto
    cabinet: ButLP
    tremolo_lfo: Sine
    tremolo_out: PyoObject

    phrase = PluckedString.phrase.replace(default=Hooks.FULL_HOOK)
    sustain = PluckedString.sustain.replace(default=3.5)
    brightness = PluckedString.brightness.replace(default=8000)
    position = PluckedString.position.replace(default=0.12)
    # a hard pick, a strong lean on the accents, a singing fretting hand
    hardness = PluckedString.hardness.replace(default=0.65)
    dynamics = PluckedString.dynamics.replace(default=0.7)
    looseness = PluckedString.looseness.replace(default=0.2)
    pick_noise = PluckedString.pick_noise.replace(default=0.3)
    vibrato = PluckedString.vibrato.replace(default=12)

    @Param(
        0,
        1,
        0.05,
        0.4,
        "Drive",
        "How hard the amp is pushed; low is a clean, glassy string, high is a crunchy, compressed lead tone whose edge and sustain grow as each note dies away.",
        sweep=True,
    )
    def drive(self, value: float) -> None:
        self.saturate(self.amp, value)

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Tone",
        "Sets the amp's tone control; low is a dark, woolly sound, high is a bright, cutting one.",
        sweep=True,
    )
    def tone(self, value: float) -> None:
        # `Disto`'s slope is how much it filters: 1 is darkest
        self.amp.slope = 1 - value

    @Param(
        2000,
        9000,
        0.02,
        5000,
        "Speaker",
        "How much of the amp's fizz the speaker cabinet lets through; low is a dark, closed-back cab that tames the crunch, high is an open, raw, cutting top end.",
        scale="cutoff",
        sweep=True,
    )
    def speaker(self, value: float) -> None:
        self.cabinet.freq = value

    @Param(
        0,
        1,
        0.05,
        0,
        "Tremolo",
        "How deeply the amp's level pulses; none is steady, a little is a vintage, shimmering swell, a lot is a choppy, surf-guitar throb.",
        sweep=True,
    )
    def tremolo(self, value: float) -> None:
        self.tremolo_lfo.mul = value * 0.5
        self.tremolo_lfo.add = 1 - value * 0.5

    @Param(
        0.5,
        10,
        0.1,
        4.5,
        "Tremolo speed",
        "How fast the tremolo pulses, in cycles a second; slow is a lazy swell, fast is a nervous flutter.",
        sweep=True,
        advanced=True,
    )
    def tremolo_speed(self, value: float) -> None:
        self.tremolo_lfo.freq = value

    def voice_stage(self, string: PyoObject) -> PyoObject:
        self.amp = Disto(string, drive=0, slope=0.5)
        self.cabinet = ButLP(self.amp, freq=5000)
        self.tremolo_lfo = Sine(freq=4.5, mul=0, add=1)
        self.tremolo_out = self.cabinet * self.tremolo_lfo
        return self.tremolo_out
