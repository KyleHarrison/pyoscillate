"""Timbre profiles shared by the project's bass patch families. The notes a
bass plays are `BassLines` phrases (`theory/phrase/bass.py`), chosen from each
voice's Pattern dropdown."""

from .base import BassProfile

TECHNO = BassProfile(
    envelope_decay=0.9,
    resonance=0.75,
    harmonics=(1, 0, 0.4, 0, 0.2, 0, 0.1),
)

GROOVE = {
    "rolling": BassProfile(envelope_decay=0.88, resonance=0.55),
    "dub": BassProfile(envelope_decay=0.95, resonance=0.78),
    "muted": BassProfile(envelope_decay=0.55, resonance=0.3),
    # held, spaced-out notes ring into the gaps instead of a constantly
    # rolling line, so the decay is long and the filter calm
    "conversation": BassProfile(
        envelope_decay=6.0,
        resonance=0.4,
        harmonics=(1.0, 0.15, 0.05, 0.0),
    ),
    # psytrance's offbeat bass
    "forest": BassProfile(
        envelope_decay=0.85,
        resonance=0.3,
        harmonics=(1.0, 0.22, 0.1, 0.04),
    ),
}

# a steady, breathing pulse: slow decay, a near-sine tone with a trace of the
# 2nd/3rd/4th harmonic for warmth, nothing that reads as growl or saturation
HOVER = BassProfile(
    envelope_decay=1.8,
    resonance=0.12,
    harmonics=(1.0, 0.06, 0.03, 0.015),
)
