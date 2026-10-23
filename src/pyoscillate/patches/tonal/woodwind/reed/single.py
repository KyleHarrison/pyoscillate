# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.woodwind.reed.single
"""Single reeds: the clarinet family, a reed on a straight tube.

A clarinet is a closed cylinder, so its tone is the square wave's: odd
harmonics only, hollow and woody, with the next note up the register a twelfth
away, not an octave. `Bore` starts at none; raise it and the even harmonics
come back, towards a saxophone's cone.
"""

from __future__ import annotations

from pyoscillate.patches.tonal.woodwind.reed.reed import ReedWind
from pyoscillate.theory.pitch import Note


class SingleReed(ReedWind):
    """A single reed on a cylindrical bore: a hollow odd-harmonic tone, almost
    no vibrato, a clear tongued start and a slow swell as the note opens. A
    style sets the register, the register's colour and the speaking time."""

    cone = ReedWind.cone.replace(default=0.1)
    edge = ReedWind.edge.replace(default=0.62)
    vibrato_bloom = ReedWind.vibrato_bloom.replace(default=0.5)
    legato = ReedWind.legato.replace(default=0.9)
    bend = ReedWind.bend.replace(default=0)
    unsteadiness = ReedWind.unsteadiness.replace(default=0.1)
    tracking = ReedWind.tracking.replace(default=0.6)
    tremolo = ReedWind.tremolo.replace(default=0.05)


class Clarinet(SingleReed):
    """Clarinet: a hollow, woody, odd-harmonic tone with a clear tongued start
    and a slight swell as the note opens."""

    title = "Clarinet"
    summary = "Hollow, woody clarinet line over the rack's chord tones."

    root_freq = SingleReed.root_freq.replace(
        minimum=Note.C3,
        maximum=Note.C6,
        default=Note.D4,
        help_text="Moves the whole line up or down; low is a dark, woody chalumeau, high is a thin, bright clarion register.",
    )
    cone = SingleReed.cone.replace(default=0.05)
    edge = SingleReed.edge.replace(default=0.65)
    attack = SingleReed.attack.replace(default=0.08)
    release = SingleReed.release.replace(default=0.32)
    vibrato = SingleReed.vibrato.replace(default=3)
    breath = SingleReed.breath.replace(default=0.12)
    brightness = SingleReed.brightness.replace(default=5000)
    opening = SingleReed.opening.replace(default=0.55)
    tongue = SingleReed.tongue.replace(default=0.4)


class ClarinetBass(SingleReed):
    """Bass clarinet: the clarinet an octave down, with a little of the even
    harmonics back, a slower speaking start and a darker pipe."""

    title = "Bass Clarinet"
    summary = "Deep, hollow bass clarinet line over the rack's chord tones."

    root_freq = SingleReed.root_freq.replace(
        minimum=Note.C2,
        maximum=Note.C5,
        default=Note.D3,
        help_text="Moves the whole line up or down; low is a dark, rumbling register, high is a woody, singing one.",
    )
    cone = SingleReed.cone.replace(default=0.15)
    edge = SingleReed.edge.replace(default=0.6)
    attack = SingleReed.attack.replace(default=0.09)
    release = SingleReed.release.replace(default=0.23)
    vibrato = SingleReed.vibrato.replace(default=5)
    breath = SingleReed.breath.replace(default=0.14)
    brightness = SingleReed.brightness.replace(default=3200)
    opening = SingleReed.opening.replace(default=0.65)
    tongue = SingleReed.tongue.replace(default=0.35)
