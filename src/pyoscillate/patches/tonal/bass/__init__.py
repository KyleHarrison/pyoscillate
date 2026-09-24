"""Reusable bass voice family and the legacy techno bass entry point."""

from __future__ import annotations

from pyo.lib.filters import MoogLP
from pyo.lib.generators import LFO
from pyo.lib.tableprocess import Osc

from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

from .core import BassProfile, build_bass
from .profiles import TECHNO

NOTE_PATTERN = list(TECHNO.pattern)
ACCENT_PATTERN = list(TECHNO.accents)
ROOT_FREQ = notes.Fs2
PARAMETERS = (
    SliderSpec(
        "root_freq",
        30,
        110,
        1,
        ROOT_FREQ,
        "Register",
        "Moves the bass up or down in pitch; lower digs deeper into the sub range, higher brings it closer to the mid range and easier to pick out melodically.",
        (PyoParamRef(Osc, "freq"),),
    ),
    SliderSpec(
        "filter_res",
        0,
        1,
        0.05,
        0.75,
        "Growl",
        "Adds resonant emphasis around the filter cutoff; higher makes the bass squelchier and more vocal, lower keeps it smoother and rounder.",
        (PyoParamRef(MoogLP, "res"),),
    ),
    SliderSpec(
        "filter_base",
        200,
        2000,
        10,
        1380,
        "Brightness",
        "Sets the average tone of the bass filter sweep; higher opens it up and brightens it, lower keeps it duller and more closed.",
        (PyoParamRef(LFO, "add"),),
    ),
    SliderSpec(
        "filter_range",
        0,
        1000,
        10,
        400,
        "Sweep depth",
        "Controls how far the filter sweeps each cycle; wider ranges create a more dramatic wah-like motion, narrower keeps the tone more static.",
        (PyoParamRef(LFO, "mul"),),
    ),
)


def build(
    tempo: Tempo,
    clock,
    root_freq: float = ROOT_FREQ,
    filter_res: float = 0.75,
    filter_base: float = 1380,
    filter_range: float = 400,
):
    """Build the original rolling, swept techno bass."""
    return build_bass(
        tempo,
        clock,
        TECHNO,
        root_freq,
        cutoff=filter_base,
        filter_base=filter_base,
        filter_range=filter_range,
        filter_res=filter_res,
    )


__all__ = [
    "ACCENT_PATTERN",
    "NOTE_PATTERN",
    "PARAMETERS",
    "BassProfile",
    "build",
    "build_bass",
]
