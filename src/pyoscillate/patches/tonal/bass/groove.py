# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.groove style=rolling
#   style: rolling | dub | muted
"""16th-note groove bass voices with a fixed low-pass."""

from collections.abc import Callable

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.tonal.bass import build_bass
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
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
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


def build(
    tempo: Tempo,
    clock: Clock,
    style: str,
    octave: float = 0,
    cutoff: float = 720,
    rate: float = 0,
    harmony: Harmony | None = None,
) -> Patch:
    """Build a 16th-note bassline with a style-specific motion pattern.

    The pattern is written as root, fifth, octave, minor third and minor
    seventh, which are all tones of the rack's minor-seventh chords, so
    re-rooting it on each chord keeps every note consonant."""
    return build_bass(
        tempo,
        clock,
        GROOVE[style],
        REGISTER_CENTRE,
        cutoff,
        rate,
        harmony=harmony or FALLBACK_HARMONY,
        octave=octave,
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one bass style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)
