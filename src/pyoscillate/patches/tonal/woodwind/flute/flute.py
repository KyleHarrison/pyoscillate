# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.woodwind.flute.flute
"""Flutes: an air jet across an edge, ringing a pipe.

A flute has no reed. The player's breath is a jet that splits on the embouchure
edge and sets the air in the pipe sounding, so the tone is the pipe's own
resonance: nearly a sine at the note's pitch, with a few weak overtones that
fall away fast, and a band of jet noise ringing around the pitch (the breath).
`JetWind` is that source for the whole family (flute, piccolo, whistle):
`Overtones` sets how many partials ride on the fundamental, from a pure,
hollow sine to a fuller, reedier tone, and the partials are normalised, so it
changes the colour without changing the loudness. `Flutter` is the flutter
tongue, a fast roll of the breath. Everything else a wind has (the pipe's
low-pass, tonguing, breath pulse, scoop) is `Wind`'s (see `wind.py`).
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.controls import SigTo
from pyo.lib.generators import Sine

from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.woodwind.flute.flute_phrases import FlutePhrases
from pyoscillate.patches.tonal.woodwind.wind import Wind
from pyoscillate.theory.pitch import Note


class JetWind(Wind):
    """A jet-driven pipe: a near-sine with a few falling overtones. A style
    sets the register, the breath and how the note is articulated."""

    # how many partials the tone can carry (the fundamental and its harmonics)
    partials: ClassVar[int] = 4

    partial_pitches: list[PyoObject]
    partial_levels: list[SigTo]
    partial_gains: list[PyoObject]
    partial_tones: list[Sine]
    flutter_depth: SigTo
    flutter_rate: SigTo
    flutter_half: PyoObject
    flutter_lfo: Sine
    flutter_gain: PyoObject
    fluttered: PyoObject

    flutter = Param(
        0,
        1,
        0.05,
        0,
        "Flutter",
        "A fast roll of the breath, the flutter tongue; none is a smooth note, a little is a shimmering edge, a lot is a rattling, growling roll.",
        sweep=True,
    )
    flutter_speed = Param(
        12,
        40,
        0.5,
        24,
        "Flutter speed",
        "How fast the breath rolls, in cycles a second; slow is a coarse, rolling rattle, fast is a fine, buzzing shimmer.",
        sweep=True,
        advanced=True,
    )

    @Param(
        0,
        1,
        0.05,
        0.35,
        "Overtones",
        "How many harmonics ride on the note; none is a pure, hollow, sine-like tone, a lot is a fuller, reedier, more pulse-like one. The loudness stays put.",
        sweep=True,
    )
    def overtones(self, value: float) -> None:
        weights = [value**index for index in range(self.partials)]
        norm = sum(weight**2 for weight in weights) ** 0.5
        for level, weight in zip(self.partial_levels, weights, strict=True):
            level.value = weight / norm

    def make_source(self) -> PyoObject:
        self.partial_pitches = [
            self.held_pitch * (index + 1) for index in range(self.partials)
        ]
        self.partial_levels = [
            SigTo(value=0, time=self.level_glide) for _ in range(self.partials)
        ]
        self.partial_gains = [
            self.voice_gain * (level * self.tone_level) for level in self.partial_levels
        ]
        self.partial_tones = [
            Sine(freq=pitch, mul=gain)
            for pitch, gain in zip(
                self.partial_pitches, self.partial_gains, strict=True
            )
        ]
        self.retain(
            *self.partial_pitches,
            *self.partial_levels,
            *self.partial_gains,
            *self.partial_tones,
        )
        return Mix(self.partial_tones, voices=1)

    def voice_stage(self, signal: PyoObject) -> PyoObject:
        cls = type(self)
        # the flutter tongue rolls the level between full and 1 - Flutter
        self.flutter_depth = self.live(cls.flutter)
        self.flutter_rate = self.live(cls.flutter_speed)
        self.flutter_half = self.flutter_depth * 0.5
        self.flutter_lfo = Sine(
            freq=self.flutter_rate, mul=self.flutter_half, add=self.flutter_half
        )
        self.flutter_gain = 1 - self.flutter_lfo
        self.fluttered = signal * self.flutter_gain
        return super().voice_stage(self.fluttered)


class Flute(JetWind):
    """Concert flute: a soft, breathy, nearly pure tone with a light vibrato
    that blooms in, a gentle consonant on each tongued note and a little scoop
    up into it."""

    title = "Flute"
    summary = "Soft, breathy concert flute line over the rack's chord tones."

    # tuned to the tune the flute carries, Hillside (`flute_phrases.py`): a
    # pastoral D-major folk melody at about 100 BPM, so a sixteenth is 0.15 s.
    # The register sits the line on the D above middle C's octave (D5); the
    # attack and release are quick enough for the sixteenth-note turns, the
    # legato is lyrical, the vibrato is light and blooms only on held notes,
    # and the room is open and a little damp, like a hillside, not a hall
    root_freq = JetWind.root_freq.replace(
        minimum=Note.C4,
        maximum=Note.C6,
        default=Note.D5,
        help_text="Moves the whole line up or down; low is a dark, breathy, intimate register, high is a bright, brilliant, piping one.",
    )
    # the shared wind lines, and the flute's own tunes (`flute_phrases.py`, beside it)
    phrase = JetWind.phrase.replace(catalog=FlutePhrases)
    attack = JetWind.attack.replace(default=0.05)
    release = JetWind.release.replace(default=0.16)
    vibrato = JetWind.vibrato.replace(default=8)
    vibrato_bloom = JetWind.vibrato_bloom.replace(default=0.5)
    glide = JetWind.glide.replace(default=0.015)
    legato = JetWind.legato.replace(default=0.9)
    bend = JetWind.bend.replace(default=-0.15)
    breath = JetWind.breath.replace(default=0.28)
    unsteadiness = JetWind.unsteadiness.replace(default=0.2)
    brightness = JetWind.brightness.replace(default=3800)
    opening = JetWind.opening.replace(default=0.4)
    tongue = JetWind.tongue.replace(default=0.25)
    tremolo = JetWind.tremolo.replace(default=0.08)
    reverb_size = JetWind.reverb_size.replace(default=0.55)
    reverb_bal = JetWind.reverb_bal.replace(default=0.3)
