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


def _conversation_from_hits(hits: dict[int, int], surprise_step: int) -> BassProfile:
    """Shared builder for a `_conversation`-style profile: `gates` rests
    every step but the ones in `hits`, so the bass reads as held,
    spaced-out notes rather than a constantly rolling line."""
    pattern = tuple(hits.get(step, 0) for step in range(_CONVERSATION_STEPS))
    gates = tuple(step in hits for step in range(_CONVERSATION_STEPS))
    # a soft downbeat accent, a touch more on the offbeat re-entry so it
    # registers as a small surprise rather than blending into the pocket
    accents = tuple(
        0.9 if step == surprise_step else 0.75 for step in range(_CONVERSATION_STEPS)
    )
    return BassProfile(
        pattern=pattern,
        accents=accents,
        envelope_decay=6.0,
        resonance=0.4,
        harmonics=(1.0, 0.15, 0.05, 0.0),
        gates=gates,
    )


def _conversation() -> BassProfile:
    return _conversation_from_hits(_CONVERSATION_HITS, surprise_step=61)


# a second four-bar phrase for the same "conversation" style: the third
# bar now leans on the fifth instead of the root, and the offbeat re-entry
# moves earlier and lands on the minor seventh instead of the root, so the
# phrase reads as a related but distinct sentence rather than a repeat
_CONVERSATION_HITS_B: dict[int, int] = {
    0: 0,
    8: 0,
    16: 0,
    32: 7,
    40: 7,
    45: 10,
    48: 0,
    56: 0,
}


def _conversation_variant_b() -> BassProfile:
    return _conversation_from_hits(_CONVERSATION_HITS_B, surprise_step=45)


# `bars=8` rotation target for `BassConversation.on_evolve` (see rack.py) -
# index 0 is the original phrase, kept first so existing behaviour doesn't
# silently change
CONVERSATION_VARIANTS: tuple[BassProfile, ...] = (
    _conversation(),
    _conversation_variant_b(),
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
    gates=(True,) * 16,
    envelope_decay=0.9,
    resonance=0.75,
    harmonics=(1, 0, 0.4, 0, 0.2, 0, 0.1),
)

GROOVE = {
    "rolling": BassProfile(
        pattern=(0, 0, 7, 0, 0, 12, 7, 0, 0, 0, 3, 7, 0, 10, 7, 0),
        accents=(1.0, 0.72, 0.72, 0.72) * 4,
        gates=(True,) * 16,
        envelope_decay=0.88,
        resonance=0.55,
    ),
    "dub": BassProfile(
        pattern=(0, 0, 0, 7, 0, 0, 10, 0, 0, 7, 0, 0, 3, 0, 7, 0),
        accents=(1.0, 0.72, 0.72, 0.72) * 4,
        gates=(True,) * 16,
        envelope_decay=0.95,
        resonance=0.78,
    ),
    "muted": BassProfile(
        pattern=(0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 3, 0, 0, 7, 0, 10),
        accents=(1.0, 0.72, 0.72, 0.72) * 4,
        gates=(True,) * 16,
        envelope_decay=0.55,
        resonance=0.3,
    ),
    "conversation": CONVERSATION_VARIANTS[0],
    # psytrance's offbeat bass: rests on each beat (where the kick lands) and
    # rolls the three 16ths between kicks - root, root, then an octave
    # bounce on the "a", with a minor-second (b2) lean into the next bar
    "forest": BassProfile(
        pattern=(0, 0, 0, 12) * 3 + (0, 0, 0, 1),
        accents=(1.0, 0.8, 0.95, 0.7) * 4,
        gates=(False, True, True, True) * 4,
        envelope_decay=0.85,
        resonance=0.3,
        harmonics=(1.0, 0.22, 0.1, 0.04),
    ),
}

# a second "muted" pattern for `BassMuted.on_evolve` (see rack.py): the
# same 16th-note pulse, but the fifth/minor-seventh/major-ninth hits fall
# on different steps, so the stabs land in a different spot in the bar
# without changing the style's short, soft envelope or filter resonance
_MUTED_VARIANT_B = BassProfile(
    pattern=(0, 0, 7, 0, 0, 0, 10, 0, 0, 3, 0, 0, 7, 0, 0, 10),
    accents=GROOVE["muted"].accents,
    gates=GROOVE["muted"].gates,
    envelope_decay=GROOVE["muted"].envelope_decay,
    resonance=GROOVE["muted"].resonance,
)

# `bars=8` rotation target for `BassMuted.on_evolve` (see rack.py) - index 0
# is the original pattern, kept first so existing behaviour doesn't
# silently change
MUTED_VARIANTS: tuple[BassProfile, ...] = (
    GROOVE["muted"],
    _MUTED_VARIANT_B,
)

# a four-bar (64-step), steady 8th-note-pulse phrase for `bass.hover.BassHover`
# (see lofi/slowed_reverb's README "Bass" mapping row): every even step
# strikes, odd steps rest, and the semitone offset above the tonic is fixed
# per bar rather than per hit - E (tonic) for bar 1, then F, G, A (the
# tonic's stepwise neighbours) for bars 2-4 before returning to E - so the
# line hovers and slowly steps rather than following a chord
_HOVER_STEPS = 64
_HOVER_BAR_OFFSETS = (0, 1, 3, 5)  # E, F, G, A above the tonic, one per bar


def _hover() -> BassProfile:
    pattern = tuple(_HOVER_BAR_OFFSETS[step // 16] for step in range(_HOVER_STEPS))
    gates = tuple(step % 2 == 0 for step in range(_HOVER_STEPS))
    # a soft downbeat lean, otherwise flat - the pulse should read as steady
    # and breathing, not accented
    accents = tuple(0.95 if step % 16 == 0 else 0.8 for step in range(_HOVER_STEPS))
    return BassProfile(
        pattern=pattern,
        accents=accents,
        envelope_decay=1.8,
        resonance=0.12,
        # near-sine: a trace of the 2nd/3rd/4th harmonic for warmth, nothing
        # that reads as growl or saturation
        harmonics=(1.0, 0.06, 0.03, 0.015),
        gates=gates,
    )


HOVER = _hover()
