# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.woodwind.reed.double
"""Double reeds: the oboe and bassoon families, two blades on a cone.

A double reed drives a conical bore, which keeps the whole harmonic series
(the sawtooth's, not the clarinet's square), so the tone is full and nasal, and
the bell and blades add a fixed resonance (`Nasal`) that gives each instrument
its pinched, reedy colour whatever note it plays.
"""

from __future__ import annotations

from pyoscillate.patches.tonal.woodwind.reed.reed import ReedWind
from pyoscillate.theory.pitch import Note


class DoubleReed(ReedWind):
    """A conical double-reed pipe: the whole harmonic series, a fixed nasal
    ring, a clear tongue. A style sets the register, the reed and the colour."""

    cone = ReedWind.cone.replace(default=1.0)
    nasal = ReedWind.nasal.replace(default=0.5)
    bend = ReedWind.bend.replace(default=0)
    tongue = ReedWind.tongue.replace(default=0.4)
    tracking = ReedWind.tracking.replace(default=0.5)
    legato = ReedWind.legato.replace(default=0.9)


class Oboe(DoubleReed):
    """Oboe: a bright, plaintive, nasal tone with a very light vibrato that
    blooms in, a narrow reed's thin edge and a quick, clean start."""

    title = "Oboe"
    summary = "Bright, plaintive oboe line over the rack's chord tones."

    nasal_freq = 1300.0
    root_freq = DoubleReed.root_freq.replace(
        minimum=Note.C4,
        maximum=Note.C7,
        default=Note.A4,
        help_text="Moves the whole line up or down; low is a dark, reedy, sad register, high is a thin, piercing one.",
    )
    edge = DoubleReed.edge.replace(default=0.75)
    nasal = DoubleReed.nasal.replace(default=0.55)
    attack = DoubleReed.attack.replace(default=0.07)
    release = DoubleReed.release.replace(default=0.14)
    vibrato = DoubleReed.vibrato.replace(default=4)
    vibrato_bloom = DoubleReed.vibrato_bloom.replace(default=0.5)
    breath = DoubleReed.breath.replace(default=0.1)
    unsteadiness = DoubleReed.unsteadiness.replace(default=0.1)
    brightness = DoubleReed.brightness.replace(default=5500)
    opening = DoubleReed.opening.replace(default=0.55)
    tremolo = DoubleReed.tremolo.replace(default=0.04)


class EnglishHorn(DoubleReed):
    """English horn (cor anglais): the oboe's fifth lower, rounder and darker
    behind a bulb bell, with a mournful, veiled tone."""

    title = "English Horn"
    summary = "Dark, mournful English horn line over the rack's chord tones."

    nasal_freq = 900.0
    root_freq = DoubleReed.root_freq.replace(
        minimum=Note.C3,
        maximum=Note.C6,
        default=Note.D4,
        help_text="Moves the whole line up or down; low is a dark, hollow, mournful register, high is a veiled, plaintive one.",
    )
    edge = DoubleReed.edge.replace(default=0.6)
    nasal = DoubleReed.nasal.replace(default=0.45)
    attack = DoubleReed.attack.replace(default=0.08)
    release = DoubleReed.release.replace(default=0.37)
    vibrato = DoubleReed.vibrato.replace(default=6)
    vibrato_bloom = DoubleReed.vibrato_bloom.replace(default=0.5)
    breath = DoubleReed.breath.replace(default=0.14)
    unsteadiness = DoubleReed.unsteadiness.replace(default=0.12)
    brightness = DoubleReed.brightness.replace(default=3400)
    opening = DoubleReed.opening.replace(default=0.6)
    tremolo = DoubleReed.tremolo.replace(default=0.05)


class Bassoon(DoubleReed):
    """Bassoon: the orchestra's tenor and bass double reed, a warm, woody,
    slightly comic voice that speaks with a little tongue and a gentle
    breath pulse."""

    title = "Bassoon"
    summary = "Warm, woody bassoon line over the rack's chord tones."

    nasal_freq = 500.0
    root_freq = DoubleReed.root_freq.replace(
        minimum=Note.C2,
        maximum=Note.C5,
        default=Note.D3,
        help_text="Moves the whole line up or down; low is a dark, buzzing bass, high is a reedy, strained tenor.",
    )
    edge = DoubleReed.edge.replace(default=0.7)
    nasal = DoubleReed.nasal.replace(default=0.5)
    attack = DoubleReed.attack.replace(default=0.06)
    release = DoubleReed.release.replace(default=0.5)
    vibrato = DoubleReed.vibrato.replace(default=3)
    breath = DoubleReed.breath.replace(default=0.15)
    brightness = DoubleReed.brightness.replace(default=2800)
    opening = DoubleReed.opening.replace(default=0.6)
    tremolo = DoubleReed.tremolo.replace(default=0.05)
    tremolo_speed = DoubleReed.tremolo_speed.replace(default=7.5)


class Contrabassoon(DoubleReed):
    """Contrabassoon: the bassoon an octave lower, a growling, slow-speaking
    rumble under the band."""

    title = "Contrabassoon"
    summary = "Growling, rumbling contrabassoon line over the rack's chord tones."

    nasal_freq = 300.0
    root_freq = DoubleReed.root_freq.replace(
        minimum=Note.C1,
        maximum=Note.C4,
        default=Note.D2,
        help_text="Moves the whole line up or down; low is a felt more than heard rumble, high is a thick, buzzing growl.",
    )
    edge = DoubleReed.edge.replace(default=0.6)
    nasal = DoubleReed.nasal.replace(default=0.4)
    attack = DoubleReed.attack.replace(default=0.09)
    release = DoubleReed.release.replace(default=0.29)
    vibrato = DoubleReed.vibrato.replace(default=3)
    breath = DoubleReed.breath.replace(default=0.2)
    brightness = DoubleReed.brightness.replace(default=1800)
    opening = DoubleReed.opening.replace(default=0.6)
    tongue = DoubleReed.tongue.replace(default=0.45)
    tremolo = DoubleReed.tremolo.replace(default=0.05)
    tremolo_speed = DoubleReed.tremolo_speed.replace(default=7.5)
