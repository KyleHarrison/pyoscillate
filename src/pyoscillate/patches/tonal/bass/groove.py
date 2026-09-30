# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.groove style=rolling
#   style: rolling | dub | muted
"""16th-note groove bass voices with a fixed low-pass."""

from __future__ import annotations

from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.tonal.bass.base import BASE_DIVISION, Bass
from pyoscillate.patches.tonal.bass.profiles import (
    CONVERSATION_VARIANTS,
    GROOVE,
    MUTED_VARIANTS,
)


class GrooveBass(Bass):
    """16th-note bassline with a style-specific motion pattern, following
    the rack's chord. Style variants subclass this and fix `profile`; the
    graph itself is identical across styles (see `Bass.build`).

    The pattern is written as root, fifth, octave, minor third and minor
    seventh, which are all tones of the rack's minor-seventh chords, so
    re-rooting it on each chord keeps every note consonant."""

    volume = Patch.volume.replace(default=0.62)

    @Param(
        180,
        2400,
        20,
        720,
        "Brightness",
        "Opens or closes the bass's low-pass filter; higher lets more upper harmonics through for "
        "a brighter tone, lower keeps it rounder and darker.",
    )
    def cutoff(self, value: float) -> None:
        self.filtered.freq = value

    rate = rate_param(
        BASE_DIVISION,
        "Halves or doubles the bass pattern speed for each step away from its 16th-note grid.",
    )

    def current_root(self) -> float:
        return self.chord_root()


class BassRolling(GrooveBass):
    """Constantly moving, rolling low-end groove."""

    title = "Bass - Rolling"
    profile = GROOVE["rolling"]


class BassDub(GrooveBass):
    """Sparser, more resonant dub-style bass hits."""

    title = "Bass - Dub"
    profile = GROOVE["dub"]


class BassMuted(GrooveBass):
    """Short, muted bass stabs that stay soft and out of the way."""

    title = "Bass - Muted"
    profile = GROOVE["muted"]

    def on_evolve(self, index: int) -> None:
        """Rotate which of `profiles.MUTED_VARIANTS` is stabbing; called
        rarely (tens of bars) by a rack-level `GroupController`, never by
        the clock directly - see `Keys.on_evolve`. The variants share this
        style's envelope/resonance, so swapping `_profile` live is safe:
        `next_step()` only reads `pattern`/`accents`/`gates` per step."""
        self._profile = MUTED_VARIANTS[index % len(MUTED_VARIANTS)]


class BassConversation(GrooveBass):
    """Sparse, four-bar phrase of held root/fifth notes with a rare
    syncopated re-entry, rather than a bassline that plays every step - see
    `profiles._conversation()`."""

    title = "Bass - Conversation"
    summary = "Sparse, held root/fifth notes over a four-bar phrase, with an occasional offbeat re-entry."
    profile = GROOVE["conversation"]

    def on_evolve(self, index: int) -> None:
        """Rotate which of `profiles.CONVERSATION_VARIANTS` is phrasing;
        same rationale as `BassMuted.on_evolve`."""
        self._profile = CONVERSATION_VARIANTS[index % len(CONVERSATION_VARIANTS)]
