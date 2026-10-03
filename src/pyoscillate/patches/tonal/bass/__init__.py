# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass
"""Reusable bass voice family and the techno bass entry point."""

from __future__ import annotations

from pyo.lib.generators import LFO

from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.tonal.bass.base import BASE_DIVISION, AccentBass, BassProfile
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

from .profiles import TECHNO


class TechnoBass(AccentBass):
    """The original rolling, swept techno bass: a fixed root note under a
    continuous filter sweep, with no chord-following (see the groove
    styles in `groove.py` for that)."""

    name = "bass"
    title = "Bass"
    summary = "Rolling, resonant bassline that sweeps in tone across the groove."
    volume = Patch.volume.replace(default=1.0)
    profile = TECHNO

    # the sweeping cutoff's own modulator, assigned by `cutoff_source()`
    cutoff_lfo: LFO

    # read live off `self.root_freq` by `current_root`'s trigger-time
    # callback - no control body needed, see `patches/AGENTS.md`'s note on a
    # parameter only read by a sequencer callback
    root_freq = Param(
        notes.B0,
        notes.A2,
        1,
        notes.Fs2,
        "Register",
        "Moves the bass up or down in pitch; lower digs deeper into the sub range, higher brings "
        "it closer to the mid range and easier to pick out melodically.",
        scale="note",
    )

    @Param(
        0,
        1,
        0.05,
        0.75,
        "Growl",
        "Adds resonant emphasis around the filter cutoff; higher makes the bass squelchier and "
        "more vocal, lower keeps it smoother and rounder.",
        sweep=True,
    )
    def filter_res(self, value: float) -> None:
        self.filtered.res = value

    @Param(
        200,
        2000,
        10,
        1380,
        "Brightness",
        "Sets the average tone of the bass filter sweep; higher opens it up and brightens it, "
        "lower keeps it duller and more closed.",
        sweep=True,
    )
    def filter_base(self, value: float) -> None:
        self.cutoff_lfo.add = value

    @Param(
        0,
        1000,
        10,
        400,
        "Sweep depth",
        "Controls how far the filter sweeps each cycle; wider ranges create a more dramatic "
        "wah-like motion, narrower keeps the tone more static.",
        sweep=True,
    )
    def filter_range(self, value: float) -> None:
        self.cutoff_lfo.mul = value

    rate = rate_param(
        BASE_DIVISION,
        "Halves or doubles the bass pattern speed for each step away from its 16th-note grid.",
    )

    def current_root(self) -> float:
        return self.root_freq

    def cutoff_source(self, tempo: Tempo) -> LFO:
        # neutral depth/centre: `filter_base`/`filter_range` controls set the real ones
        self.cutoff_lfo = LFO(freq=1 / tempo.bar, type=0, mul=0, add=0)
        return self.cutoff_lfo


__all__ = ["Bass", "BassProfile", "TechnoBass"]
