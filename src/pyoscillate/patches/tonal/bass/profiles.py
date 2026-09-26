"""Musical profiles shared by the project's bass patch families."""

from .base import BassProfile

# a four-bar (64-step) phrase, step -> semitones above the chord root, for
# `_conversation()`: mostly root hits on beats one and three, a bar that
# drops to a single hit, a fifth substituted on the third bar's second hit,
# and a syncopated offbeat re-entry near the end of the fourth bar - see
# lofi/README.md's bass ascii diagram, which this follows one-for-one.
_CONVERSATION_HITS: dict[int, int] = {
    0: 0,
    8: 0,
    16: 0,
    32: 0,
    40: 7,
    48: 0,
    61: 0,
}
_CONVERSATION_STEPS = 64


def _conversation() -> BassProfile:
    """Sparse, four-bar bass phrase: `gates` rests every step but the ones
    in `_CONVERSATION_HITS`, so the bass reads as held, spaced-out notes
    rather than a constantly rolling line."""
    pattern = tuple(_CONVERSATION_HITS.get(step, 0) for step in range(_CONVERSATION_STEPS))
    gates = tuple(step in _CONVERSATION_HITS for step in range(_CONVERSATION_STEPS))
    # a soft downbeat accent, a touch more on the offbeat re-entry so it
    # registers as a small surprise rather than blending into the pocket
    accents = tuple(0.9 if step == 61 else 0.75 for step in range(_CONVERSATION_STEPS))
    return BassProfile(
        pattern=pattern,
        accents=accents,
        envelope_decay=6.0,
        resonance=0.4,
        harmonics=(1.0, 0.15, 0.05, 0.0),
        gates=gates,
    )


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
    "conversation": _conversation(),
}
