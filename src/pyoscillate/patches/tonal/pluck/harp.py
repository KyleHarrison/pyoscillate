# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pluck.harp
"""Harps: strings plucked with the fingertips over a large resonating
soundboard (the harp) or a calabash (the kora). Both are `PluckedString` (see
`string.py` for the string itself) through a `Body`; both play open arpeggios
on the chord tones, notes ringing over each other."""

from __future__ import annotations

from pyo import PyoObject

from pyoscillate.patches.common import Body
from pyoscillate.patches.tonal.pluck.string import PluckedString
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


class Harp(HarpString):
    """Concert harp: gut and nylon strings plucked with the fingertip, round
    and clear, ringing for seconds over a wide soundboard."""

    title = "Harp"
    summary = "Clear, ringing harp arpeggio over the rack's chord tones."

    pluck_time = 0.004
    body_modes = (Note.G3, Note.G4, Note.D5)
    body_q = (5, 6, 6)

    sustain = HarpString.sustain.replace(default=4.0)
    brightness = HarpString.brightness.replace(default=5000)
    position = HarpString.position.replace(default=0.25)
    body = HarpString.body.replace(default=0.6)


class Kora(HarpString):
    """Kora: a harp-lute whose strings are plucked by thumb and finger over a
    calabash, bright, dry and sparkling, each note doubled an octave above."""

    title = "Kora"
    summary = "Bright, sparkling kora figure over the rack's chord tones."

    pluck_time = 0.002
    # each note sounded with a quieter octave string above it
    courses = ((1.0, 1.0), (2.0, 0.45))
    body_modes = (Note.C3, Note.G3, Note.C4)
    body_q = (6, 8, 8)

    sustain = HarpString.sustain.replace(default=2.4)
    brightness = HarpString.brightness.replace(default=6500)
    position = HarpString.position.replace(default=0.12)
    body = HarpString.body.replace(default=0.5)
