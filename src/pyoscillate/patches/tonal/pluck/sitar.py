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

from pyo import PyoObject
from pyo.lib.effects import Disto
from pyo.lib.filters import ButLP

from pyoscillate.patches.common import Body
from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.pluck.string import PluckedString, Sympathy
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase import Hooks
from pyoscillate.theory.pitch import Note


class Sitar(Sympathy, Body, PluckedString):
    """Buzzing sitar string with sympathetic strings, over a gourd."""

    title = "Sitar"
    summary = "Buzzing, resonant sitar line over the rack's chord tones."

    body_modes = (Note.G2, Note.D3, Note.A3)
    body_q = (6, 6, 8)
    # the sympathetic strings tuned to the chord's root and fifth
    sympathy_intervals = (Interval.UNISON, Interval.PERFECT_FIFTH)
    click_freq = 3000

    buzz: Disto
    buzz_tone: ButLP

    phrase = PluckedString.phrase.replace(default=Hooks.FULL_HOOK)
    sustain = PluckedString.sustain.replace(default=2.2)
    brightness = PluckedString.brightness.replace(default=7000)
    position = PluckedString.position.replace(default=0.08)
    body = Body.body.replace(default=0.5)
    # a plectrum on a wire, a dynamic hand, and a meend: each note scoops up
    # into its pitch from a semitone below
    hardness = PluckedString.hardness.replace(default=0.75)
    dynamics = PluckedString.dynamics.replace(default=0.5)
    looseness = PluckedString.looseness.replace(default=0.25)
    pick_noise = PluckedString.pick_noise.replace(default=0.3)
    bend = PluckedString.bend.replace(
        default=-1,
        help_text="Slides each note into its pitch from this many semitones away, the sitar's meend; negative swoops up from below, positive drops down from above, zero is a clean attack.",
    )
    sympathy_level = Sympathy.sympathy_level.replace(default=0.5)

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
        self.saturate(self.buzz, value)

    def voice_stage(self, string: PyoObject) -> PyoObject:
        self.buzz = Disto(string, drive=0, slope=0.3)
        self.buzz_tone = ButLP(self.buzz, freq=self.brightness)
        return self.add_body(self.add_sympathy(self.buzz_tone))
