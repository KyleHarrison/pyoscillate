# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pluck.harp
"""Harps: strings plucked with the fingertips over a large resonating
soundboard (the harp) or a calabash (the kora). Both are `PluckedString` (see
`string.py` for the string itself) through a `Body`; both play open arpeggios
on the chord tones, notes ringing over each other. The harp's open strings
answer the played ones (`Sympathy`); the kora doubles each note an octave
above (`Courses`)."""

from __future__ import annotations

from pyo import PyoObject

from pyoscillate.patches.common import Body
from pyoscillate.patches.tonal.pluck.string import Courses, PluckedString, Sympathy
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase import Hooks
from pyoscillate.theory.pitch import Note


class HarpString(Body, PluckedString):
    """Shared shape of the harps: arpeggiated chord tones through a body."""

    phrase = PluckedString.phrase.replace(default=Hooks.FULL_HOOK)
    root_freq = PluckedString.root_freq.replace(
        minimum=Note.C3, maximum=Note.C5, default=Note.C4
    )

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(string)


class Harp(Sympathy, HarpString):
    """Concert harp: gut and nylon strings plucked with the fingertip, round
    and clear, ringing for seconds over a wide soundboard, the open strings
    humming in answer."""

    title = "Harp"
    summary = "Clear, ringing harp arpeggio over the rack's chord tones."

    body_modes = (Note.G3, Note.G4, Note.D5)
    body_q = (5, 6, 6)
    # the open strings that share a note's partials: the root, fifth and octave
    sympathy_intervals = (Interval.UNISON, Interval.PERFECT_FIFTH, Interval.OCTAVE)
    click_freq = 2200

    sustain = HarpString.sustain.replace(default=4.0)
    brightness = HarpString.brightness.replace(default=5000)
    position = HarpString.position.replace(default=0.25)
    body = HarpString.body.replace(default=0.6)
    # a fingertip, an expressive hand, a long hum from the open strings
    hardness = HarpString.hardness.replace(default=0.4)
    dynamics = HarpString.dynamics.replace(default=0.6)
    looseness = HarpString.looseness.replace(default=0.2)
    pick_noise = HarpString.pick_noise.replace(default=0.05)
    sympathy_level = Sympathy.sympathy_level.replace(default=0.3)
    sympathy_ring = Sympathy.sympathy_ring.replace(default=4.0)

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(self.add_sympathy(string))


class Kora(Courses, HarpString):
    """Kora: a harp-lute whose strings are plucked by thumb and finger over a
    calabash, bright, dry and sparkling, each note doubled an octave above."""

    title = "Kora"
    summary = "Bright, sparkling kora figure over the rack's chord tones."

    # each note sounded with a quieter octave string above it
    courses = ((1.0, 1.0), (2.0, 0.45))
    body_modes = (Note.C3, Note.G3, Note.C4)
    body_q = (6, 8, 8)
    click_freq = 3000

    sustain = HarpString.sustain.replace(default=2.4)
    brightness = HarpString.brightness.replace(default=6500)
    position = HarpString.position.replace(default=0.12)
    body = HarpString.body.replace(default=0.5)
    # thumb and finger on a dry string, with a lively, loose touch
    hardness = HarpString.hardness.replace(default=0.65)
    dynamics = HarpString.dynamics.replace(default=0.5)
    looseness = HarpString.looseness.replace(default=0.25)
    pick_noise = HarpString.pick_noise.replace(default=0.2)
    doubling = Courses.doubling.replace(
        help_text="How loud the octave string above each note is; none is a plain single string, full is a bright, sparkling doubled voice, and the voice's total level stays the same."
    )
