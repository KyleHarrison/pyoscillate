# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pluck.folk
"""Folk string instruments: a banjo's hard-picked string over a drum head, a
mandolin's paired courses, a lute's soft double strings and ringing bass
courses, a dulcimer's struck, shimmering pairs. All are `PluckedString` (see
`string.py` for the string itself) through a hollow `Body`; what separates
them is how hard and where the string is struck, how the hand plays it (touch,
mute, looseness), how many strings sound for each note and how far apart they
sit, which strings ring unplayed, and which resonances the body adds."""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.filters import Reson

from pyoscillate.patches.common import Body
from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.pluck.string import Courses, PluckedString, Sympathy
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase import Hooks
from pyoscillate.theory.pitch import Note


class FolkString(Body, PluckedString):
    """Shared shape of the folk instruments: the string goes straight through
    its body."""

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(string)


class PairedString(Courses, FolkString):
    """A folk instrument whose notes sound on a pair of strings, with Spread
    and Doubling to set how the pair sits."""


class SympatheticFolk(Sympathy, PairedString):
    """A paired folk instrument with strings that ring unplayed."""

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(self.add_sympathy(string))


class Banjo(FolkString):
    """Bright, twangy banjo: a hard pick close to the bridge on a single
    string, over a taut drum head that rings in the upper middle."""

    title = "Banjo"
    summary = "Bright, twangy banjo plinking out the rack's chord tones."

    # the head's loudest resonances, tight and high
    body_modes = (Note.G4, Note.D5, Note.G5)
    body_q = (4, 5, 6)
    # the nasal band the head and bridge push forward (Hz), how sharp it is,
    # and a trim so Twang at 1 adds about as much as the string
    twang_freq: ClassVar[float] = 2400
    twang_q: ClassVar[float] = 3
    twang_trim: ClassVar[float] = 0.4
    click_freq = 3500

    twang_band: Reson
    twang_voiced: PyoObject

    phrase = FolkString.phrase.replace(default=Hooks.FULL_HOOK)
    root_freq = FolkString.root_freq.replace(
        minimum=Note.A2, maximum=Note.A4, default=Note.A3
    )
    sustain = FolkString.sustain.replace(default=0.8)
    brightness = FolkString.brightness.replace(default=9000)
    position = FolkString.position.replace(default=0.07)
    body = FolkString.body.replace(default=0.7)
    # a hard pick and a loose, rolling feel
    hardness = FolkString.hardness.replace(default=0.75)
    dynamics = FolkString.dynamics.replace(default=0.5)
    looseness = FolkString.looseness.replace(default=0.3)
    pick_noise = FolkString.pick_noise.replace(default=0.5)

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Twang",
        "How much the nasal, metallic bite of the head and bridge comes forward; none is a plain, round string, high is the sharp, ringing twang of a bluegrass banjo.",
        sweep=True,
    )
    def twang(self, value: float) -> None:
        self.twang_band.mul = value * self.twang_trim

    def voice_stage(self, string: PyoObject) -> PyoObject:
        self.twang_band = Reson(string, freq=self.twang_freq, q=self.twang_q)
        self.twang_voiced = string + self.twang_band
        return self.add_body(self.twang_voiced)


class Mandolin(PairedString):
    """Mandolin: each note is a pair of unison steel strings, slightly apart,
    picked hard and bright with a short ring, over a small, high body."""

    title = "Mandolin"
    summary = "Bright, shimmering mandolin pairs picking the rack's chord tones."

    # unison courses, a few cents apart: the beating is the mandolin's shimmer
    courses = ((1.0, 1.0), (1.0, 1.0))
    body_modes = (Note.D4, Note.A4, Note.E5)
    body_q = (6, 8, 8)
    click_freq = 3000

    phrase = FolkString.phrase.replace(default=Hooks.FULL_HOOK)
    root_freq = FolkString.root_freq.replace(
        minimum=Note.E3, maximum=Note.E4, default=Note.A3
    )
    sustain = FolkString.sustain.replace(default=1.4)
    brightness = FolkString.brightness.replace(default=7000)
    position = FolkString.position.replace(default=0.1)
    body = FolkString.body.replace(default=0.5)
    # a hard, even pick with a tight shimmer and little give in the hand
    hardness = FolkString.hardness.replace(default=0.65)
    dynamics = FolkString.dynamics.replace(default=0.4)
    looseness = FolkString.looseness.replace(default=0.15)
    pick_noise = FolkString.pick_noise.replace(default=0.35)
    spread = PairedString.spread.replace(default=6)


class Mandocello(PairedString):
    """Mandocello: a mandolin tuned an octave lower, in cello range, with
    heavier paired strings that ring warmer and longer."""

    title = "Mandocello"
    summary = "Warm, round mandocello pairs sounding the rack's chord tones low."

    courses = ((1.0, 1.0), (1.0, 1.0))
    body_modes = (Note.A2, Note.D3, Note.A3)
    body_q = (6, 7, 8)
    click_freq = 1800

    root_freq = FolkString.root_freq.replace(
        minimum=Note.C2, maximum=Note.C4, default=Note.A2
    )
    sustain = FolkString.sustain.replace(default=1.8)
    brightness = FolkString.brightness.replace(default=4000)
    position = FolkString.position.replace(default=0.15)
    body = FolkString.body.replace(default=0.6)
    # a heavier, rounder pick and a slow, wide beat
    hardness = FolkString.hardness.replace(default=0.4)
    dynamics = FolkString.dynamics.replace(default=0.55)
    looseness = FolkString.looseness.replace(default=0.2)
    pick_noise = FolkString.pick_noise.replace(default=0.2)
    vibrato = FolkString.vibrato.replace(default=8)
    spread = PairedString.spread.replace(default=5)


class Lute(SympatheticFolk):
    """Renaissance lute: soft gut double courses plucked with the fingertip
    over a deep round bowl, warm and quick to fade, with bass courses that
    ring on in answer."""

    title = "Lute"
    summary = "Soft, warm lute courses outlining the rack's chords."

    # double courses, the second a touch quieter and a few cents off
    courses = ((1.0, 1.0), (1.0, 0.8))
    body_modes = (Note.C3, Note.G3, Note.D4)
    body_q = (5, 6, 6)
    # the open bass courses: an octave under the root, the root and the fifth
    sympathy_intervals = (-Interval.OCTAVE, Interval.UNISON, Interval.PERFECT_FIFTH)
    click_freq = 1500

    root_freq = FolkString.root_freq.replace(default=Note.G3)
    sustain = FolkString.sustain.replace(default=1.4)
    brightness = FolkString.brightness.replace(default=3200)
    position = FolkString.position.replace(default=0.22)
    body = FolkString.body.replace(default=0.7)
    # a soft fingertip, an expressive touch and an unhurried hand
    hardness = FolkString.hardness.replace(default=0.3)
    dynamics = FolkString.dynamics.replace(default=0.65)
    looseness = FolkString.looseness.replace(default=0.35)
    pick_noise = FolkString.pick_noise.replace(default=0.15)
    spread = SympatheticFolk.spread.replace(default=4)
    sympathy_level = SympatheticFolk.sympathy_level.replace(default=0.3)
    sympathy_ring = SympatheticFolk.sympathy_ring.replace(default=2.5)


class Dulcimer(SympatheticFolk):
    """Hammered dulcimer: soft hammers strike pairs of strings, a few cents
    apart, that ring a long time and shimmer against each other, while the
    unstruck strings around them hum."""

    title = "Dulcimer"
    summary = "Shimmering hammered dulcimer ringing out the rack's chord tones."

    # a wider detune than a mandolin's: a slow shimmer, not a vibrato
    courses = ((1.0, 1.0), (1.0, 1.0))
    body_modes = (Note.G2, Note.D3, Note.D4)
    body_q = (5, 6, 6)
    # the strings the hammers pass over: the root, fifth and octave
    sympathy_intervals = (Interval.UNISON, Interval.PERFECT_FIFTH, Interval.OCTAVE)
    click_freq = 2000

    phrase = FolkString.phrase.replace(default=Hooks.FULL_HOOK)
    root_freq = FolkString.root_freq.replace(
        minimum=Note.A2, maximum=Note.A4, default=Note.A3
    )
    sustain = FolkString.sustain.replace(default=4.0)
    brightness = FolkString.brightness.replace(default=3500)
    position = FolkString.position.replace(default=0.14)
    body = FolkString.body.replace(default=0.6)
    # felt hammers, an even touch and a steady, practised hand
    hardness = FolkString.hardness.replace(default=0.25)
    dynamics = FolkString.dynamics.replace(default=0.35)
    looseness = FolkString.looseness.replace(default=0.2)
    pick_noise = FolkString.pick_noise.replace(default=0.1)
    spread = SympatheticFolk.spread.replace(default=12)
    sympathy_level = SympatheticFolk.sympathy_level.replace(default=0.35)
    sympathy_ring = SympatheticFolk.sympathy_ring.replace(default=4.0)
