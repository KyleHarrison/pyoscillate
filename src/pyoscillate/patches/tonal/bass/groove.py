# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.groove style=rolling
#   style: rolling | dub | muted
"""16th-note groove bass voices with a fixed low-pass."""

from __future__ import annotations

from typing import ClassVar

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.tonal.bass.base import Bass
from pyoscillate.patches.tonal.bass.profiles import GROOVE
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH
VOLUME_DEFAULT = 0.62
# every chord root snaps to the octave nearest this
REGISTER_CENTRE = notes.A1
# a static key of A - used only outside a rack that shares its own `Harmony`
FALLBACK_HARMONY = Harmony()


class GrooveBass(Bass):
    """16th-note bassline with a style-specific motion pattern, following
    the rack's chord. Style variants subclass this and fix `style`; the
    graph itself is identical across styles (see `Bass.build_voice`).

    The pattern is written as root, fifth, octave, minor third and minor
    seventh, which are all tones of the rack's minor-seventh chords, so
    re-rooting it on each chord keeps every note consonant."""

    volume_default = VOLUME_DEFAULT
    needs_harmony: ClassVar[bool] = True

    style: ClassVar[str]

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

    def build(self, tempo: Tempo, clock: Clock, harmony: Harmony | None = None) -> Patch:
        self._reset()
        return self.build_voice(
            tempo,
            clock,
            GROOVE[self.style],
            REGISTER_CENTRE,
            self.cutoff,
            self.rate,
            harmony=harmony or FALLBACK_HARMONY,
        )


class BassRolling(GrooveBass):
    """Constantly moving, rolling low-end groove."""

    title = "Bass - Rolling"
    style = "rolling"


class BassDub(GrooveBass):
    """Sparser, more resonant dub-style bass hits."""

    title = "Bass - Dub"
    style = "dub"


class BassMuted(GrooveBass):
    """Short, muted bass stabs that stay soft and out of the way."""

    title = "Bass - Muted"
    style = "muted"


class BassConversation(GrooveBass):
    """Sparse, four-bar phrase of held root/fifth notes with a rare
    syncopated re-entry, rather than a bassline that plays every step - see
    `profiles._conversation()`."""

    title = "Bass - Conversation"
    summary = "Sparse, held root/fifth notes over a four-bar phrase, with an occasional offbeat re-entry."
    style = "conversation"
