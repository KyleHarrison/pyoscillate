# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass
"""Reusable bass voice family and the techno bass entry point."""

from __future__ import annotations

from typing import Any

from pyo.lib.filters import MoogLP
from pyo.lib.generators import LFO
from pyo.lib.tableprocess import Osc

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.tonal.bass.base import Bass, BassProfile
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

from .profiles import TECHNO

NOTE_PATTERN = list(TECHNO.pattern)
ACCENT_PATTERN = list(TECHNO.accents)
ROOT_FREQ = notes.Fs2
PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.B0,
        notes.A2,
        1,
        ROOT_FREQ,
        "Register",
        "Moves the bass up or down in pitch; lower digs deeper into the sub range, higher brings it closer to the mid range and easier to pick out melodically.",
        (PyoParamRef(Osc, "freq"),),
        scale="note",
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


VOLUME_DEFAULT = 1.0


class TechnoBass(Bass):
    """The original rolling, swept techno bass: a fixed root note under a
    continuous filter sweep, with no chord-following (see the groove
    styles in `groove.py` for that)."""

    name = "bass"
    title = "Bass"
    summary = "Rolling, resonant bassline that sweeps in tone across the groove."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    root_freq: float
    filter_res: float
    filter_base: float
    filter_range: float

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        return self.build_voice(
            tempo,
            clock,
            TECHNO,
            self.root_freq,
            cutoff=self.filter_base,
            filter_base=self.filter_base,
            filter_range=self.filter_range,
            filter_res=self.filter_res,
        )


__all__ = [
    "ACCENT_PATTERN",
    "NOTE_PATTERN",
    "PARAMETERS",
    "Bass",
    "BassProfile",
    "TechnoBass",
]
