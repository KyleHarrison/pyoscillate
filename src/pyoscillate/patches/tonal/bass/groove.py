"""16th-note groove bass voices with a fixed low-pass."""

from typing import Any, ClassVar

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec, rate_slider
from pyoscillate.patches.tonal.bass.base import Bass
from pyoscillate.patches.tonal.bass.profiles import GROOVE
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "octave",
        0,
        1,
        1,
        0,
        "Register",
        "Lifts the bassline up an octave; low sits deep and heavy under the kick, high brings it "
        "closer to the chords. The notes always follow the rack's key and chord changes.",
    ),
    SliderSpec(
        "cutoff",
        180,
        2400,
        20,
        720,
        "Brightness",
        "Opens or closes the bass's low-pass filter; higher lets more upper harmonics through for a brighter tone, lower keeps it rounder and darker.",
    ),
    rate_slider(
        BASE_DIVISION,
        "Halves or doubles the bass pattern speed for each step away from its 16th-note grid.",
    ),
)
PATTERNS = {name: list(profile.pattern) for name, profile in GROOVE.items()}
PROFILES = {
    name: (profile.envelope_decay, profile.resonance)
    for name, profile in GROOVE.items()
}
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

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    needs_harmony: ClassVar[bool] = True

    style: ClassVar[str]

    octave: float
    cutoff: float
    rate: float

    def build(self, tempo: Tempo, clock: Clock, harmony: Harmony | None = None, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        return self.build_voice(
            tempo,
            clock,
            GROOVE[self.style],
            REGISTER_CENTRE,
            self.cutoff,
            self.rate,
            harmony=harmony or FALLBACK_HARMONY,
            octave=self.octave,
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
