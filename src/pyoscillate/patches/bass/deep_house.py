"""16th-note bass voices for the Deep House project."""

from collections.abc import Callable

from ipywidgets import VBox

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.bass import build_bass
from pyoscillate.patches.bass.profiles import DEEP_HOUSE
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

PARAMETERS = (
    SliderSpec(
        "root_freq", 35, 82, 1, 55, "Register", "Moves the bassline up or down in pitch; lower sits deeper and heavier, higher brings it closer to the chords."
    ),
    SliderSpec(
        "cutoff", 180, 2400, 20, 720, "Brightness", "Opens or closes the bass's low-pass filter; higher lets more upper harmonics through for a brighter tone, lower keeps it rounder and darker."
    ),
)
PATTERNS = {name: list(profile.pattern) for name, profile in DEEP_HOUSE.items()}
PROFILES = {
    name: (profile.envelope_decay, profile.resonance) for name, profile in DEEP_HOUSE.items()
}
VOLUME_DEFAULT = 0.62


def build(
    tempo: Tempo, clock: Clock, style: str, root_freq: float = 55, cutoff: float = 720
) -> Patch:
    """Build a 16th-note bassline with a style-specific motion pattern."""
    return build_bass(tempo, clock, DEEP_HOUSE[style], root_freq, cutoff)


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one bass style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
    style: str = "rolling",
) -> VBox:
    """Create controls for one bass style."""
    return patch_widget(
        rack,
        f"bass_{style}",
        make_builder(style),
        PARAMETERS,
        controller=controller,
        volume_default=VOLUME_DEFAULT,
        build_kwargs={"tempo": tempo, "clock": clock},
    )
