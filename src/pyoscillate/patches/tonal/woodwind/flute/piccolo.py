# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.woodwind.flute.piccolo
"""Piccolo: the flute an octave up, a short pipe with a narrow, piping tone.

A piccolo is the same jet over an edge, a half-length pipe that sounds an
octave higher. A high note has few harmonics (a short pipe has less room
for them), so the tone is nearly a sine and the pipe's own resonance, a
whistle-sharp ring, carries it.
"""

from __future__ import annotations

from pyoscillate.patches.tonal.woodwind.flute.flute import JetWind
from pyoscillate.theory.pitch import Note


class Piccolo(JetWind):
    """Piccolo: a bright, piping, nearly pure tone, a quick start with a
    sharper consonant and a flutter when asked."""

    title = "Piccolo"
    summary = "Bright, piping piccolo line over the rack's chord tones."

    root_freq = JetWind.root_freq.replace(
        minimum=Note.C5,
        maximum=Note.C7,
        default=Note.D6,
        help_text="Moves the whole line up or down; low is a clear, flute-like register, high is a shrill, piercing one.",
    )
    overtones = JetWind.overtones.replace(default=0.5)
    attack = JetWind.attack.replace(default=0.05)
    release = JetWind.release.replace(default=0.12)
    vibrato = JetWind.vibrato.replace(default=6)
    vibrato_bloom = JetWind.vibrato_bloom.replace(default=0.4)
    glide = JetWind.glide.replace(default=0.01)
    legato = JetWind.legato.replace(default=0.8)
    bend = JetWind.bend.replace(default=-0.2)
    breath = JetWind.breath.replace(default=0.18)
    air_focus = JetWind.air_focus.replace(default=40)
    brightness = JetWind.brightness.replace(default=7000)
    opening = JetWind.opening.replace(default=0.3)
    tracking = JetWind.tracking.replace(default=0.3)
    tongue = JetWind.tongue.replace(default=0.45)
    tremolo = JetWind.tremolo.replace(default=0.05)
    tremolo_speed = JetWind.tremolo_speed.replace(default=5)
