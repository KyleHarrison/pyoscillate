# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pluck.sitar
"""Sitar: a wire plucked hard over a curved, flat-topped bridge that makes it
buzz, with sympathetic strings that ring in answer.

It is a `PluckedString` (see `string.py` for the string itself) with two things
after it. The jawari bridge lets the string graze the bridge as it moves, which
adds a harmonic bloom that grows as the note dies and the string swings less:
a waveshaper after the string does the same, because it gains a quiet signal
more than a loud one. The sympathetic strings are two more waveguides, tuned to
the chord's root and fifth and retuned on every note, fed by the buzzing string:
they ring only where the played note shares a partial with them.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Sig
from pyo.lib.effects import Disto, Waveguide
from pyo.lib.filters import ButLP

from pyoscillate.patches.common import Body
from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.pluck.string import PluckedString
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase import Hooks
from pyoscillate.theory.pitch import Note


class Sitar(Body, PluckedString):
    """Buzzing sitar string with sympathetic strings, over a gourd."""

    title = "Sitar"
    summary = "Buzzing, resonant sitar line over the rack's chord tones."

    # a plectrum on a wire: a sharp, brief strike
    pluck_time = 0.0015
    body_modes = (Note.G2, Note.D3, Note.A3)
    body_q = (6, 6, 8)
    # `Disto` divides by 1 - drive, so full drive would be infinite gain
    max_drive: ClassVar[float] = 0.95
    # the level the string sustains at: Buzz rescales the waveshaper so a note
    # at this level keeps its loudness, and only its tail blooms
    string_peak: ClassVar[float] = 0.05
    # seconds the sympathetic strings take to fade
    sympathy_sustain: ClassVar[float] = 2.0
    # trims the sympathetic strings (a resonator gains a steady tone heavily)
    # so Sympathy at 1 adds about as much as the played string
    sympathy_trim: ClassVar[float] = 0.01

    buzz: Disto
    buzz_tone: ButLP
    sympathy_freqs: list[Sig]
    sympathy: Waveguide

    phrase = PluckedString.phrase.replace(default=Hooks.FULL_HOOK)
    sustain = PluckedString.sustain.replace(default=2.2)
    brightness = PluckedString.brightness.replace(default=7000)
    position = PluckedString.position.replace(default=0.08)
    body = Body.body.replace(default=0.5)

    @Param(
        0,
        1,
        0.05,
        0.7,
        "Buzz",
        "How much the string grazes the bridge; low is a clean, plain string, high is the bright, singing buzz of a sitar that blooms as each note fades.",
        sweep=True,
    )
    def buzz_amount(self, value: float) -> None:
        amount = value * self.max_drive
        gain = 2 * amount / (1 - amount)
        self.buzz.drive = amount
        self.buzz.mul = (1 + gain * self.string_peak) / (1 + gain)

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Sympathy",
        "How much the unplayed strings ring in answer to the note; low is a dry, single string, high is a shimmering halo around the chord's root and fifth.",
        sweep=True,
    )
    def sympathy_level(self, value: float) -> None:
        self.sympathy.mul = value * self.sympathy_trim

    def voice_stage(self, string: PyoObject) -> PyoObject:
        self.buzz = Disto(string, drive=0, slope=0.3)
        self.buzz_tone = ButLP(self.buzz, freq=self.brightness)
        root = self.root_at(0)
        self.sympathy_freqs = [
            Sig(root),
            Sig(Note.transpose(root, Interval.PERFECT_FIFTH)),
        ]
        self.sympathy = Waveguide(
            self.buzz_tone,
            freq=self.sympathy_freqs,
            dur=self.sympathy_sustain,
            minfreq=self.lowest_freq,
        )
        return self.add_body(self.buzz_tone + self.sympathy.mix(1))

    def on_strike(self, string: int, note: float, bar_index: int) -> None:
        root = self.root_at(bar_index)
        self.sympathy_freqs[0].value = root
        self.sympathy_freqs[1].value = Note.transpose(root, Interval.PERFECT_FIFTH)
