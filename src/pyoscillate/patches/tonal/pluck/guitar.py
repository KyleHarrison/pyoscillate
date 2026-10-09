# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pluck.guitar
"""Guitars: a plucked steel string through a hollow body, or a bright string
pushed through a saturating amplifier. Both are `PluckedString` (see
`string.py` for the string itself); the style is what follows it."""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.effects import Disto
from pyo.lib.filters import ButLP

from pyoscillate.patches.common import Body
from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.pluck.string import PluckedString
from pyoscillate.theory.phrase import Hooks
from pyoscillate.theory.pitch import Note


class GuitarAcoustic(Body, PluckedString):
    """Steel-string acoustic guitar: a plucked string through a hollow wooden
    body, ringing and mellowing on the chord tones."""

    title = "Guitar - Acoustic"
    summary = "Warm, ringing acoustic-guitar figure outlining the rack's chords."

    # the body's loudest resonances: the air inside, the top plate and its
    # next mode, each an octave apart
    body_modes = (Note.G2, Note.G3, Note.G4)
    body_q = (6, 8, 8)

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(string)


class GuitarElectric(PluckedString):
    """Electric guitar: a bright, long-ringing string pushed through a
    saturating amplifier whose crunch swells as the note dies away."""

    title = "Guitar - Electric"
    summary = "Bright, singing electric-guitar figure outlining the rack's chords."

    # the level the string sustains at (below its strike): Drive rescales the
    # amp so a note at this level keeps its loudness however hard it
    # saturates, and the strike is then squashed rather than boosted
    string_peak: ClassVar[float] = 0.05
    # `Disto` divides by 1 - drive, so full drive would be infinite gain
    max_drive: ClassVar[float] = 0.95
    # the speaker cabinet rolls the fizz off above this (Hz)
    cabinet_cutoff: ClassVar[float] = 5000

    amp: Disto
    cabinet: ButLP

    phrase = PluckedString.phrase.replace(default=Hooks.FULL_HOOK)
    sustain = PluckedString.sustain.replace(default=3.5)
    brightness = PluckedString.brightness.replace(default=8000)
    position = PluckedString.position.replace(default=0.12)

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
        amount = value * self.max_drive
        gain = 2 * amount / (1 - amount)
        self.amp.drive = amount
        # `Disto` gains small signals by 1 + gain and saturates near 1: scale
        # the output so a sustaining note keeps its level, and the saturation
        # shows up as a flatter, longer-feeling note instead of a louder one
        self.amp.mul = (1 + gain * self.string_peak) / (1 + gain)

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

    def voice_stage(self, string: PyoObject) -> PyoObject:
        self.amp = Disto(string, drive=0, slope=0.5)
        self.cabinet = ButLP(self.amp, freq=self.cabinet_cutoff)
        return self.cabinet
