"""Musical profiles shared by the project's bass patch families."""

from .base import BassProfile

TECHNO = BassProfile(
    pattern=(0, 0, 0, 0, 0, 0, 12, 0, 0, 0, 7, 0, 0, 0, 0, 0),
    accents=(
        1.0,
        0.6,
        0.6,
        0.6,
        0.9,
        0.6,
        0.6,
        0.6,
        1.0,
        0.6,
        0.6,
        0.6,
        0.9,
        0.6,
        0.6,
        0.7,
    ),
    envelope_decay=0.9,
    resonance=0.75,
    harmonics=(1, 0, 0.4, 0, 0.2, 0, 0.1),
)

GROOVE = {
    "rolling": BassProfile(
        pattern=(0, 0, 7, 0, 0, 12, 7, 0, 0, 0, 3, 7, 0, 10, 7, 0),
        accents=(1.0, 0.72, 0.72, 0.72) * 4,
        envelope_decay=0.88,
        resonance=0.55,
    ),
    "dub": BassProfile(
        pattern=(0, 0, 0, 7, 0, 0, 10, 0, 0, 7, 0, 0, 3, 0, 7, 0),
        accents=(1.0, 0.72, 0.72, 0.72) * 4,
        envelope_decay=0.95,
        resonance=0.78,
    ),
    "muted": BassProfile(
        pattern=(0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 3, 0, 0, 7, 0, 10),
        accents=(1.0, 0.72, 0.72, 0.72) * 4,
        envelope_decay=0.55,
        resonance=0.3,
    ),
}
