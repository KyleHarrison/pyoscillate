# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass
"""Reusable bass voice family and the techno bass entry point."""

from __future__ import annotations

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.bass.base import Bass, BassProfile
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

from .profiles import TECHNO


class TechnoBass(Bass):
    """The original rolling, swept techno bass: a fixed root note under a
    continuous filter sweep, with no chord-following (see the groove
    styles in `groove.py` for that)."""

    name = "bass"
    title = "Bass"
    summary = "Rolling, resonant bassline that sweeps in tone across the groove."
    volume_default = 1.0

    # read live off `self.root_freq` by `Bass.note_root`'s trigger-time
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
    )
    def filter_range(self, value: float) -> None:
        self.cutoff_lfo.mul = value

    def build(self, tempo: Tempo, clock: Clock) -> Patch:
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


__all__ = ["Bass", "BassProfile", "TechnoBass"]
