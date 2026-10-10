# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.keys.accordion
"""Accordion: free reeds blown by the bellows, in the ranks a player switches in.

A free reed is a thin tongue that swings through a slot as air passes: its
tone is a buzzing, harmonically rich wave, here a sawtooth whose sharpness is
the reed's edge. The accordion's registers are ranks of reeds (`RankedKeys`,
see `sustained.py`): a bassoon rank an octave below, a clarinet rank at pitch,
a second 8' rank tuned a few cents the other way (the musette, whose beating
is the accordion's own wet shimmer), and a piccolo rank an octave above. The
registers are mixed by their levels.

The reeds' chamber rolls off the highs (Brightness), the bellows shake
(a fast tremolo of the level, the player pumping the bellows) and a burst of
air chiffs on the front of each note while the reed speaks. Attack is how
quickly the bellows get a reed going.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.controls import Adsr, SigTo
from pyo.lib.filters import ButLP, Reson
from pyo.lib.generators import LFO, Noise, Sine

from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.keys.sustained import RankedKeys
from pyoscillate.theory.phrase import Rhythms
from pyoscillate.theory.pitch import Note


class Accordion(RankedKeys):
    """Accordion: reed ranks (bassoon, clarinet, musette, piccolo) through a
    reed chamber, with bellows shake and a puff of air on each note,
    holding the rack's chord or a line of its tones."""

    title = "Accordion"
    summary = "Reedy, shimmering musette accordion holding the rack's chords."

    volume = RankedKeys.volume.replace(default=0.7)
    # 16' bassoon, 8' clarinet, 8' musette, 4' piccolo
    ranks = (0.5, 1.0, 1.0, 2.0)
    gain = 0.035
    # the musette's two 8' ranks sit this far either side of the note, so
    # Musette tuning is the whole width of the beating
    musette_ranks: ClassVar[tuple[int, int]] = (1, 2)
    # the bellows shake's deepest swing (a fraction of the level, each way)
    shake_max: ClassVar[float] = 0.4
    # the chiff's band (Hz), sharpness, length (s) and level at full Chiff as a
    # multiple of one rank's
    chiff_freq: ClassVar[float] = 2200.0
    chiff_q: ClassVar[float] = 1.5
    chiff_decay: ClassVar[float] = 0.06
    chiff_boost: ClassVar[float] = 4.0

    reeds: list[LFO]
    chamber: ButLP
    shake_depth: SigTo
    shake_lfo: Sine
    shake_swing: PyoObject
    shake_gain: PyoObject
    chiff_noise: Noise
    chiff_band: Reson
    chiff_env: Adsr
    chiff_level: SigTo
    chiff_amp: PyoObject
    chiffing: PyoObject
    puffed: PyoObject
    shaken: PyoObject

    phrase = RankedKeys.phrase.replace(default=Rhythms.QUARTER_PULSE)
    root_freq = RankedKeys.root_freq.replace(
        help_text="Moves the whole chord up or down; low is a deep, bassoon-like register, high is a bright, singing right-hand one.",
    )
    attack = RankedKeys.attack.replace(
        default=0.12,
        help_text="How quickly the bellows get each reed speaking; short is a sharp, immediate note, long is a gentle, breathing swell.",
    )
    release = RankedKeys.release.replace(default=0.15)
    legato = RankedKeys.legato.replace(default=0.6)

    @Param(
        0,
        1,
        0.05,
        0,
        "Bassoon 16'",
        "The rank of reeds an octave below; adds a deep, buzzing, hollow weight under the chord.",
        sweep=True,
    )
    def bassoon(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        1,
        0.05,
        1.0,
        "Clarinet 8'",
        "The rank of reeds at pitch, in tune; the plain, reedy centre of the accordion's voice.",
        sweep=True,
    )
    def clarinet(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        1,
        0.05,
        0.8,
        "Musette 8'",
        "The second rank at pitch, tuned against the first; brings in the beating, wet, shimmering voice of a musette accordion.",
        sweep=True,
    )
    def musette(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        1,
        0.05,
        0.4,
        "Piccolo 4'",
        "The rank of reeds an octave above; adds a bright, thin, piping top.",
        sweep=True,
    )
    def piccolo(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        30,
        0.5,
        14,
        "Musette tuning",
        "How far apart the two 8' ranks are tuned, in cents; none locks them into one plain reed, a little is a slow, warm shimmer, a lot is the fast, wobbling wetness of a cheap, out-of-tune squeezebox.",
        sweep=True,
    )
    def musette_tuning(self, value: float) -> None:
        for rank, side in zip(self.musette_ranks, (-1, 1), strict=True):
            self.rank_ratios[rank].value = Note.semitone_ratio(side * value / 200)

    @Param(
        0.3,
        1,
        0.05,
        0.8,
        "Reed edge",
        "How sharp the reeds' buzz is; low is a rounder, mellower reed, high is a buzzy, nasal, biting one.",
        sweep=True,
    )
    def reed_edge(self, value: float) -> None:
        for reed in self.reeds:
            reed.sharp = value

    @Param(
        800,
        12000,
        0.02,
        5000,
        "Brightness",
        "How much of the reeds' top end gets out of the reed chamber; low is a muffled, distant squeezebox, high is a bright, close, cutting one.",
        scale="cutoff",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.chamber.freq = value

    @Param(
        0,
        1,
        0.05,
        0.2,
        "Bellows shake",
        "How deeply the player shakes the bellows, pulsing the level; none is a steady note, a little is a living, breathing sound, a lot is the fluttering tremolo of a folk player.",
        sweep=True,
    )
    def shake(self, value: float) -> None:
        self.shake_depth.value = value * self.shake_max

    @Param(
        3,
        16,
        0.5,
        10,
        "Shake speed",
        "How fast the bellows are shaken, in cycles a second; slow is a heaving swell, fast is a nervous, fluttering vibrato.",
        sweep=True,
        advanced=True,
    )
    def shake_speed(self, value: float) -> None:
        self.shake_lfo.freq = value

    @Param(
        0,
        1,
        0.05,
        0.3,
        "Chiff",
        "The puff of air on the front of each note as the reeds start to speak; none is a smooth entry, high is a breathy, pushing attack.",
        sweep=True,
    )
    def chiff(self, value: float) -> None:
        self.chiff_level.value = value * self.gain * self.chiff_boost

    def rank_values(self) -> list[float]:
        return [self.bassoon, self.clarinet, self.musette, self.piccolo]

    def rank_tone(self, freq: PyoObject, level: PyoObject) -> PyoObject:
        reed = LFO(freq=freq, sharp=0.8, type=0, mul=level)
        self.reeds.append(reed)
        return reed

    def make_tone(self) -> PyoObject:
        self.reeds = []
        return super().make_tone()

    def voice_stage(self, signal: PyoObject) -> PyoObject:
        self.chamber = ButLP(signal, freq=self.brightness)

        # the air that is let through as the reed starts to speak
        self.chiff_noise = Noise()
        self.chiff_band = Reson(self.chiff_noise, freq=self.chiff_freq, q=self.chiff_q)
        self.chiff_env = Adsr(
            attack=0.003,
            decay=self.chiff_decay,
            sustain=0,
            release=0.02,
            dur=0.003 + self.chiff_decay + 0.02,
        )
        self.chiff_level = SigTo(value=0, time=0.05)
        self.chiff_amp = self.chiff_env * self.chiff_level
        self.chiffing = self.chiff_band * self.chiff_amp
        self.puffed = self.chamber + self.chiffing

        # the bellows shaken: the level swings between 1 - 2 depth and 1
        self.shake_depth = SigTo(value=0, time=0.05)
        self.shake_lfo = Sine(freq=10, mul=self.shake_depth)
        self.shake_swing = self.shake_lfo - self.shake_depth
        self.shake_gain = self.shake_swing + 1
        self.shaken = self.puffed * self.shake_gain
        return self.shaken

    def on_note(self, notes: list[float], bar_index: int) -> None:
        self.chiff_env.play()
