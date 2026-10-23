# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.woodwind.reed.bagpipes
"""Bagpipes: a chanter that never stops, over a drone that never changes.

The player blows a bag, and the bag's pressure, not the lungs, drives the
reeds, so the chanter's conical double reed is never tongued and never lets
go: every note is slurred into the next (full Legato, no Tongue, no vibrato),
and the bag's slow bleed gives each note its long release. Under it a drone
pipe, a cylinder with a reed (odd harmonics only), sounds one fixed note from
the first note on, and stays sounding.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.controls import Adsr, SigTo
from pyo.lib.generators import Sine

from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.woodwind.reed.reed import ReedWind
from pyoscillate.theory.pitch import Note


class Bagpipes(ReedWind):
    """Bagpipes: a bright, nasal, never-tongued chanter slurring from note to
    note over a steady drone a register below."""

    title = "Bagpipes"
    summary = "A slurred, nasal chanter line over a steady drone."

    # the drone sounds this multiple of the Register, as odd harmonics (a
    # cylinder), each 1/n of the one below, at this level against the chanter
    drone_ratio: ClassVar[float] = 0.5
    drone_partials: ClassVar[int] = 4
    drone_level: ClassVar[float] = 0.5
    # seconds the drone takes to fill in when it starts
    drone_attack: ClassVar[float] = 0.4

    drone_root: SigTo
    drone_amount: SigTo
    drone_env: Adsr
    drone_pitches: list[PyoObject]
    drone_gains: list[PyoObject]
    drone_tones: list[Sine]
    drone_mix: Mix
    drone_sum: PyoObject
    _drone_on: bool

    root_freq = ReedWind.root_freq.replace(
        minimum=Note.C3,
        maximum=Note.C5,
        default=Note.A3,
        help_text="Moves the whole line, and the drone with it, up or down; low is a deep, droning field pipe, high is a skirling, piercing one.",
    )
    cone = ReedWind.cone.replace(default=0.9)
    edge = ReedWind.edge.replace(default=0.9)
    nasal = ReedWind.nasal.replace(default=0.35)
    attack = ReedWind.attack.replace(default=0.02)
    release = ReedWind.release.replace(default=0.85)
    vibrato = ReedWind.vibrato.replace(default=0)
    glide = ReedWind.glide.replace(default=0.04)
    legato = ReedWind.legato.replace(default=1.0)
    bend = ReedWind.bend.replace(default=0)
    breath = ReedWind.breath.replace(default=0.08)
    unsteadiness = ReedWind.unsteadiness.replace(default=0.05)
    brightness = ReedWind.brightness.replace(default=9000)
    opening = ReedWind.opening.replace(default=0)
    tracking = ReedWind.tracking.replace(default=0.2)
    tongue = ReedWind.tongue.replace(default=0)
    tremolo = ReedWind.tremolo.replace(default=0)
    reverb_bal = ReedWind.reverb_bal.replace(default=0.2)

    drone = Param(
        0,
        1,
        0.05,
        0.6,
        "Drone",
        "How loud the drone pipe sounds under the line; none is the chanter alone, a lot is a thick, humming carpet of one steady note.",
        sweep=True,
    )

    def make_source(self) -> PyoObject:
        self._drone_on = False
        return super().make_source()

    def voice_stage(self, signal: PyoObject) -> PyoObject:
        cls = type(self)
        # the drone: odd harmonics of one note, fixed to the Register, filled
        # in on the first note and never lifted
        self.drone_root = self.live(cls.root_freq)
        self.drone_amount = self.live(cls.drone)
        self.drone_env = Adsr(
            attack=self.drone_attack, decay=0, sustain=1, release=self.release
        )
        self.drone_pitches = [
            self.drone_root * (self.drone_ratio * number)
            for number in range(1, 2 * self.drone_partials, 2)
        ]
        self.drone_gains = [
            self.drone_env
            * self.drone_amount
            * (self.tone_level * self.drone_level / number)
            for number in range(1, 2 * self.drone_partials, 2)
        ]
        self.drone_tones = [
            Sine(freq=pitch, mul=gain)
            for pitch, gain in zip(self.drone_pitches, self.drone_gains, strict=True)
        ]
        self.drone_mix = Mix(self.drone_tones, voices=1)
        self.drone_sum = signal + self.drone_mix
        self.retain(*self.drone_pitches, *self.drone_gains, *self.drone_tones)
        return super().voice_stage(self.drone_sum)

    def on_attack(self) -> None:
        if not self._drone_on:
            self.drone_env.play()
            self._drone_on = True
        super().on_attack()
