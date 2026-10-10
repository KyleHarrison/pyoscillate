# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.keys.celeste
"""Celeste: soft hammers on steel bars over wooden resonators, a pure, bell-like
tone with a faint, glassy ping that rings for seconds with no tremolo.

It is the electric piano's FM struck keyboard (`FmKeys`, see `keys.py`) with
the body kept almost a plain sine and the tine moved to a lower, inharmonic
ratio. A bar's overtones are not harmonics, so the ping is a little
off-pitch and shimmering, where the electric piano's is a high, even bark.
The ping fades in half a second, long enough to ring like a bar, and the
chords are comped high and slow so each note is heard."""

from __future__ import annotations

from typing import ClassVar

from pyoscillate.patches.tonal.keys.keys import FmKeys
from pyoscillate.theory.phrase import Rhythms
from pyoscillate.theory.pitch import Note


class Celeste(FmKeys):
    """Celeste: a pure, bell-like, glassy keyboard that rings over the rack's
    chords, struck high and slow."""

    title = "Celeste"
    summary = (
        "Pure, glassy, bell-like celeste chords ringing over the rack's progression."
    )

    volume = FmKeys.volume.replace(default=0.55)

    # a steel bar's first overtone is not a harmonic: the ping shimmers off the
    # pitch instead of sitting on it
    tine_ratio: ClassVar[float] = 5.4
    # the ping rings a little, then clears to the bar's pure tone
    tine_time: ClassVar[float] = 0.12
    tine_ring: ClassVar[float] = 0.6
    tine_level: ClassVar[float] = 0.35

    phrase = FmKeys.phrase.replace(
        default=Rhythms.QUARTER_PULSE,
        help_text="Picks when in the bar the chords are struck: from sparse, swung stabs to a chord on every beat, "
        "or one chord left to ring.",
    )
    root_freq = FmKeys.root_freq.replace(
        minimum=Note.A3,
        maximum=Note.E5,
        default=Note.A4,
        help_text="Moves the chords up or down; low is a warm, dark, music-box register, high is a thin, glittering, bell-like one.",
    )
    bark = FmKeys.bark.replace(
        default=1.2,
        help_text="How much each strike pings: low is a soft, felted hammer on a round bar, high is a bright, glassy, metallic ping on hard notes that fades as the chord rings.",
    )
    bite = FmKeys.bite.replace(
        default=0.15,
        help_text="The edge on the sustained tone: low is a pure, sine-like bar, high is a harder, brighter, more metallic ring.",
    )
    decay = FmKeys.decay.replace(
        default=2.1,
        help_text="How long each chord rings, in seconds, before it dies away; short is a tight, plinking stab, long lets the chords shimmer into each other.",
    )
    tremolo = FmKeys.tremolo.replace(default=0)
