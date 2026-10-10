# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.vocal.whistling
"""Whistling: a near-pure tone high above the voice, with breath in it.

A whistle is not a buzz filtered into a vowel: air streams over the lips and
the mouth's cavity rings with it, so what is heard is almost a sine at the
note's pitch with a narrow band of hiss around it. The tone is a sine (with
`Edge` adding a faint second harmonic for a harder, shriller whistle) and the
breath is noise run through a very sharp resonator tuned to the same pitch
(`Purity` is how sharp). Both are a `Singer` (see `singer.py`), so the pitch,
vibrato, glide and room work as they do for the voices."""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.controls import SigTo
from pyo.lib.filters import ButLP, Reson
from pyo.lib.generators import Sine

from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.vocal.singer import Singer
from pyoscillate.theory.pitch import Note


class Whistling(Singer):
    """Whistled melody: a thin, breathy, near-sine tone with a quick, light
    vibrato that blooms in after the note starts, and a little scoop up into
    each pitch."""

    title = "Whistling"
    summary = "Thin, breathy whistled line over the rack's chord tones."

    # the tone's level, and the trim that brings the resonated breath up to it
    gain: ClassVar[float] = 0.07
    air_trim: ClassVar[float] = 0.1
    # the second harmonic's level against the tone at full Edge
    edge_max: ClassVar[float] = 0.35

    whistle_level: PyoObject
    whistle_tone: Sine
    overtone_pitch: PyoObject
    edge_gain: SigTo
    overtone_level: PyoObject
    overtone: Sine
    air: Reson
    tone_mix: PyoObject
    tone_filter: ButLP
    whistle_bank: Mix

    root_freq = Singer.root_freq.replace(
        minimum=Note.A4,
        maximum=Note.A6,
        default=Note.A5,
        help_text="Moves the whole line up or down; low is a mellow, flute-like whistle, high is a shrill, piercing one.",
    )
    attack = Singer.attack.replace(default=0.04)
    release = Singer.release.replace(default=0.3)
    vibrato = Singer.vibrato.replace(default=12)
    vibrato_speed = Singer.vibrato_speed.replace(default=7.0)
    vibrato_bloom = Singer.vibrato_bloom.replace(default=0.35)
    glide = Singer.glide.replace(default=0.03)
    breath = Singer.breath.replace(
        default=0.4,
        help_text="How much air hisses around the whistle; none is a pure, flute-like tone, a lot is a windy, effortful whistle.",
    )
    reverb_size = Singer.reverb_size.replace(default=0.5)
    reverb_bal = Singer.reverb_bal.replace(default=0.25)

    @Param(
        500,
        9000,
        0.02,
        3500,
        "Brightness",
        "How shrill the whistle is; low is a soft, covered, muffled tone, high is a bright, piercing one.",
        scale="cutoff",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.tone_filter.freq = value

    @Param(
        4,
        80,
        1,
        30,
        "Purity",
        "How sharply the breath rings at the pitch; low is a diffuse, airy hiss around the note, high is a tight, whistly ring.",
        sweep=True,
    )
    def purity(self, value: float) -> None:
        self.air.q = value

    @Param(
        0,
        1,
        0.05,
        0.15,
        "Edge",
        "How much of a harder, shriller overtone rides on the whistle; none is a pure, round tone, high is a thin, sharp, forced whistle.",
        sweep=True,
    )
    def edge(self, value: float) -> None:
        self.edge_gain.value = value * self.edge_max

    def make_source(self) -> PyoObject:
        self.whistle_level = self.voice_gain * self.gain
        self.whistle_tone = Sine(freq=self.held_pitch, mul=self.whistle_level)
        self.overtone_pitch = self.held_pitch * 2
        self.edge_gain = SigTo(value=0, time=self.level_glide)
        self.overtone_level = self.whistle_level * self.edge_gain
        self.overtone = Sine(freq=self.overtone_pitch, mul=self.overtone_level)
        return self.whistle_tone + self.overtone

    def make_tract(self, source: PyoObject, breath: PyoObject) -> PyoObject:
        self.air = Reson(breath, freq=self.held_pitch, q=30, mul=self.air_trim)
        self.tone_mix = source + self.air
        self.tone_filter = ButLP(self.tone_mix, freq=self.brightness)
        self.whistle_bank = Mix(self.tone_filter, voices=1)
        return self.whistle_bank
