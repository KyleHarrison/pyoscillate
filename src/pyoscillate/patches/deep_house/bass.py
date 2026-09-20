"""16th-note bass voices for the Deep House project."""

from collections.abc import Callable

from ipywidgets import VBox
from pyo.lib.filters import MoogLP
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import SIXTEENTH, Clock
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

PARAMETERS = (
    SliderSpec("root_freq", 35, 82, 1, 55, "Root", "Bass root frequency in Hz."),
    SliderSpec("cutoff", 180, 2400, 20, 720, "Cutoff", "Bass low-pass cutoff."),
)
PATTERNS = {
    "rolling": [0, 0, 7, 0, 0, 12, 7, 0, 0, 0, 3, 7, 0, 10, 7, 0],
    "dub": [0, 0, 0, 7, 0, 0, 10, 0, 0, 7, 0, 0, 3, 0, 7, 0],
    "muted": [0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 3, 0, 0, 7, 0, 10],
}
PROFILES = {"rolling": (0.88, 0.55), "dub": (0.95, 0.78), "muted": (0.55, 0.3)}
VOLUME_DEFAULT = 0.62


def build(
    tempo: Tempo, clock: Clock, style: str, root_freq: float = 55, cutoff: float = 720
) -> Patch:
    """Build a 16th-note bassline with a style-specific motion pattern."""
    decay, resonance = PROFILES[style]
    trigger = Trig()
    envelope = TrigEnv(
        trigger, CosTable([(0, 0), (80, 1), (2100, 0.5), (8191, 0)]), dur=tempo.sixteenth * decay
    )
    oscillator = Osc(HarmTable([1, 0.32, 0.18, 0.1]), freq=root_freq, mul=envelope)
    voice = MoogLP(oscillator, freq=cutoff, res=resonance)
    state = {"step": 0, "root": root_freq}

    def next_step() -> None:
        step = state["step"] % 16
        oscillator.freq = state["root"] * 2 ** (PATTERNS[style][step] / 12)
        envelope.mul = 1.0 if step % 4 == 0 else 0.72
        trigger.play()
        state["step"] += 1

    return Patch(
        sequencer=clock.subscribe(SIXTEENTH, next_step),
        voice=voice,
        controls={
            "root_freq": lambda value: state.update(root=value),
            "cutoff": lambda value: setattr(voice, "freq", value),
        },
    )


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