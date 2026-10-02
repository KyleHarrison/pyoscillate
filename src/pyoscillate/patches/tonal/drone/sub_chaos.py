# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.sub_chaos
"""Chaotic sub drift: a near-static low fundamental whose pitch wanders
unpredictably within a narrow range, for an organic, unstable rumble.

This is the drone family's "micro-pitch" style - the centre itself moves,
but kept narrow enough that it never reads as a note change, just a subtly
living, breathing low end.
"""

from __future__ import annotations

from pyo.lib.controls import SigTo
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Rossler
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice, Gate
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes

# mostly fundamental with a touch of 2nd/3rd harmonic - rounded, sub-heavy tone
SUB_HARMONICS = [1, 0.15, 0.05]


class BassChaos(Gate, ContinuousVoice):
    """Chaotic sub drift: a near-static low fundamental whose pitch wanders unpredictably within a narrow range, for an organic, unstable rumble.

    Unlike `BassDrone`'s level-only swell, the movement here is in the
    pitch itself - kept narrow enough that it never reads as a clear note
    change, just a subtly living, breathing low end.
    """

    title = "Bass - chaotic sub drift"
    summary = "Living, unstable sub rumble whose pitch subtly wanders."
    volume = Patch.volume.replace(default=0.8)

    # the graph, assigned by build(); finish() retains every one of them
    root_freq_sig: SigTo
    chaos_speed_sig: SigTo
    chaos_amount_sig: SigTo
    drift_range_sig: SigTo
    filter_base_sig: SigTo
    filter_res_sig: SigTo
    pitch_chaos: Rossler
    sub_table: HarmTable
    sub_osc: Osc
    output: MoogLP

    @Param(
        notes.E0,
        notes.E2,
        1,
        notes.E1,
        "Register",
        "Sets the center pitch the sub wanders around.",
        scale="note",
    )
    def root_freq(self, value: float) -> None:
        self.root_freq_sig.value = value

    @Param(
        0.01,
        0.3,
        0.01,
        0.03,
        "Drift speed",
        "How quickly the pitch wanders; slower feels like a slow-breathing organism, faster feels more "
        "agitated and unstable.",
        sweep=True,
    )
    def chaos_speed(self, value: float) -> None:
        self.chaos_speed_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Instability",
        "How unpredictable the pitch wander is; higher feels more restless and alive, lower stays closer "
        "to a steady drone.",
        sweep=True,
    )
    def chaos_amount(self, value: float) -> None:
        self.chaos_amount_sig.value = value

    @Param(
        0,
        15,
        0.5,
        3.0,
        "Wander range",
        "How far the pitch strays from center; wider feels more organic and unsettled, narrower keeps it "
        "closer to a fixed note.",
        sweep=True,
    )
    def drift_range(self, value: float) -> None:
        self.drift_range_sig.value = value

    @Param(
        60,
        500,
        10,
        180,
        "Brightness",
        "Darkens or brightens the low end; lower keeps it duller and rounder, higher lets a bit more "
        "presence through.",
        sweep=True,
    )
    def filter_base(self, value: float) -> None:
        self.filter_base_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.2,
        "Resonance",
        "Adds emphasis around the cutoff for a more colored, slightly whistling low end; kept low here "
        "for a smooth, uncolored rumble.",
        sweep=True,
    )
    def filter_res(self, value: float) -> None:
        self.filter_res_sig.value = value

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()
        self.root_freq_sig = self.live(type(self).root_freq)
        self.chaos_speed_sig = self.live(type(self).chaos_speed)
        self.chaos_amount_sig = self.live(type(self).chaos_amount)
        self.drift_range_sig = self.live(type(self).drift_range)
        self.filter_base_sig = self.live(type(self).filter_base)
        self.filter_res_sig = self.live(type(self).filter_res)

        self.pitch_chaos = Rossler(
            pitch=self.chaos_speed_sig,
            chaos=self.chaos_amount_sig,
            mul=self.drift_range_sig,
            add=self.root_freq_sig,
        )

        self.sub_table = HarmTable(SUB_HARMONICS)
        self.sub_osc = Osc(table=self.sub_table, freq=self.pitch_chaos, mul=0.5)
        self.output = MoogLP(
            self.sub_osc, freq=self.filter_base_sig, res=self.filter_res_sig
        )
        return self.finish(self.add_gate(self.output, context))
