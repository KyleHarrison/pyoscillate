# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pluck.folk
"""Folk string instruments: a banjo's hard-picked string over a drum head, a
mandolin's paired courses, a lute's soft double strings, a dulcimer's struck,
shimmering pairs. All are `PluckedString` (see `string.py` for the string
itself) through a hollow `Body`; what separates them is how hard and where the
string is struck, how many strings sound for each note, how long they ring and
which resonances the body adds."""

from __future__ import annotations

from pyo import PyoObject

from pyoscillate.patches.common import Body
from pyoscillate.patches.tonal.pluck.string import PluckedString
from pyoscillate.theory.phrase import Hooks
from pyoscillate.theory.pitch import Note


class FolkString(Body, PluckedString):
    """Shared shape of the folk instruments: the string goes straight through
    its body."""

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(string)


class Banjo(FolkString):
    """Bright, twangy banjo: a hard pick close to the bridge on a single
    string, over a taut drum head that rings in the upper middle."""

    title = "Banjo"
    summary = "Bright, twangy banjo plinking out the rack's chord tones."

    # a hard pick: short, clicky strike
    pluck_time = 0.0015
    # the head's loudest resonances, tight and high
    body_modes = (Note.G4, Note.D5, Note.G5)
    body_q = (4, 5, 6)

    phrase = FolkString.phrase.replace(default=Hooks.FULL_HOOK)
    root_freq = FolkString.root_freq.replace(
        minimum=Note.A2, maximum=Note.A4, default=Note.A3
    )
    sustain = FolkString.sustain.replace(default=0.8)
    brightness = FolkString.brightness.replace(default=9000)
    position = FolkString.position.replace(default=0.07)
    body = FolkString.body.replace(default=0.7)


class Mandolin(FolkString):
    """Mandolin: each note is a pair of unison steel strings, slightly apart,
    picked hard and bright with a short ring, over a small, high body."""

    title = "Mandolin"
    summary = "Bright, shimmering mandolin pairs picking the rack's chord tones."

    pluck_time = 0.002
    # unison courses, a few cents apart: the beating is the mandolin's shimmer
    courses = ((1.0, 1.0), (Note.semitone_ratio(0.06), 1.0))
    body_modes = (Note.D4, Note.A4, Note.E5)
    body_q = (6, 8, 8)

    phrase = FolkString.phrase.replace(default=Hooks.FULL_HOOK)
    root_freq = FolkString.root_freq.replace(
        minimum=Note.E3, maximum=Note.E4, default=Note.A3
    )
    sustain = FolkString.sustain.replace(default=1.4)
    brightness = FolkString.brightness.replace(default=7000)
    position = FolkString.position.replace(default=0.1)
    body = FolkString.body.replace(default=0.5)


class Mandocello(FolkString):
    """Mandocello: a mandolin tuned an octave lower, in cello range, with
    heavier paired strings that ring warmer and longer."""

    title = "Mandocello"
    summary = "Warm, round mandocello pairs sounding the rack's chord tones low."

    pluck_time = 0.004
    courses = ((1.0, 1.0), (Note.semitone_ratio(0.05), 1.0))
    body_modes = (Note.A2, Note.D3, Note.A3)
    body_q = (6, 7, 8)

    root_freq = FolkString.root_freq.replace(
        minimum=Note.C2, maximum=Note.C4, default=Note.A2
    )
    sustain = FolkString.sustain.replace(default=1.8)
    brightness = FolkString.brightness.replace(default=4000)
    position = FolkString.position.replace(default=0.15)
    body = FolkString.body.replace(default=0.6)


class Lute(FolkString):
    """Renaissance lute: soft gut double courses plucked with the fingertip
    over a deep round bowl, warm and quick to fade."""

    title = "Lute"
    summary = "Soft, warm lute courses outlining the rack's chords."

    # a fingertip: slower, softer strike
    pluck_time = 0.005
    # double courses, the second a touch quieter and a few cents off
    courses = ((1.0, 1.0), (Note.semitone_ratio(0.04), 0.8))
    body_modes = (Note.C3, Note.G3, Note.D4)
    body_q = (5, 6, 6)

    root_freq = FolkString.root_freq.replace(default=Note.G3)
    sustain = FolkString.sustain.replace(default=1.4)
    brightness = FolkString.brightness.replace(default=3200)
    position = FolkString.position.replace(default=0.22)
    body = FolkString.body.replace(default=0.7)


class Dulcimer(FolkString):
    """Hammered dulcimer: soft hammers strike pairs of strings, a few cents
    apart, that ring a long time and shimmer against each other."""

    title = "Dulcimer"
    summary = "Shimmering hammered dulcimer ringing out the rack's chord tones."

    # a felt hammer: a longer, softer strike than a pick
    pluck_time = 0.006
    # a wider detune than a mandolin's: a slow shimmer, not a vibrato
    courses = ((1.0, 1.0), (Note.semitone_ratio(0.12), 1.0))
    body_modes = (Note.G2, Note.D3, Note.D4)
    body_q = (5, 6, 6)

    phrase = FolkString.phrase.replace(default=Hooks.FULL_HOOK)
    root_freq = FolkString.root_freq.replace(
        minimum=Note.A2, maximum=Note.A4, default=Note.A3
    )
    sustain = FolkString.sustain.replace(default=4.0)
    brightness = FolkString.brightness.replace(default=3500)
    position = FolkString.position.replace(default=0.14)
    body = FolkString.body.replace(default=0.6)
