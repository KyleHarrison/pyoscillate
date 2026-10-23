# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.woodwind.lip.natural
"""Natural lip winds: pipes and shells with no valves and no holes.

One note at a time, the pitch is the lips' and the pipe's shape is a mood: a
conch is a short, soft spiral that hums and swells, a didgeridoo is a long
hollow log that drones and talks.
"""

from __future__ import annotations

from pyoscillate.patches.tonal.woodwind.lip.lip import LipWind
from pyoscillate.theory.pitch import Note


class ConchShell(LipWind):
    """Conch shell: a soft, hooting blow with a slow swell, a veiled, hollow
    tone and a deep, resonant cave of a room."""

    title = "Conch Shell"
    summary = "Soft, hooting conch shell line over the rack's chord tones."

    mouth_low = 300.0
    mouth_high = 1200.0
    root_freq = LipWind.root_freq.replace(
        minimum=Note.C3,
        maximum=Note.C5,
        default=Note.G3,
        help_text="Moves the whole line up or down; low is a deep, far-off call, high is a thin, close hoot.",
    )
    buzz = LipWind.buzz.replace(default=0.35)
    mouth = LipWind.mouth.replace(default=0.25)
    mouth_speed = LipWind.mouth_speed.replace(default=0.6)
    attack = LipWind.attack.replace(default=0.11)
    release = LipWind.release.replace(default=0.13)
    vibrato = LipWind.vibrato.replace(default=0)
    glide = LipWind.glide.replace(default=0.012)
    legato = LipWind.legato.replace(default=0.9)
    bend = LipWind.bend.replace(default=-0.3)
    breath = LipWind.breath.replace(default=0.3)
    brightness = LipWind.brightness.replace(default=1000)
    opening = LipWind.opening.replace(default=0.55)
    tracking = LipWind.tracking.replace(default=0.3)
    tongue = LipWind.tongue.replace(default=0.15)
    tremolo = LipWind.tremolo.replace(default=0.05)
    tremolo_speed = LipWind.tremolo_speed.replace(default=2)
    reverb_size = LipWind.reverb_size.replace(default=0.7)
    reverb_bal = LipWind.reverb_bal.replace(default=0.35)


class Didgeridoo(LipWind):
    """Didgeridoo: a deep, droning buzz that never lets go, a vowel-like
    resonance rolling over it, and a rasping edge on the low harmonics."""

    title = "Didgeridoo"
    summary = "Deep, droning, talking didgeridoo line over the rack's chord tones."

    mouth_low = 300.0
    mouth_high = 1600.0
    mouth_q = 8.0
    root_freq = LipWind.root_freq.replace(
        minimum=Note.C1,
        maximum=Note.C3,
        default=Note.D2,
        help_text="Moves the whole line up or down; low is a deep, chest-shaking drone, high is a short, hooting pipe.",
    )
    buzz = LipWind.buzz.replace(default=0.6)
    mouth = LipWind.mouth.replace(default=0.8)
    mouth_speed = LipWind.mouth_speed.replace(default=1)
    attack = LipWind.attack.replace(default=0.03)
    release = LipWind.release.replace(default=0.5)
    vibrato = LipWind.vibrato.replace(default=0)
    glide = LipWind.glide.replace(default=0.1)
    legato = LipWind.legato.replace(default=1.0)
    bend = LipWind.bend.replace(default=0)
    breath = LipWind.breath.replace(default=0.3)
    unsteadiness = LipWind.unsteadiness.replace(default=0.1)
    brightness = LipWind.brightness.replace(default=2500)
    opening = LipWind.opening.replace(default=0.2)
    tracking = LipWind.tracking.replace(default=0.3)
    tongue = LipWind.tongue.replace(default=0.1)
    tremolo = LipWind.tremolo.replace(default=0)
