# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.sub_swell
"""Slow-swelling sub drone: a near-static low fundamental that breathes in
and out in level rather than changing pitch or timbre.

This is the drone family's "level" style - the tone and pitch stay put; the
only thing that moves is amplitude, on a slow tidal cycle.
"""

from __future__ import annotations

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Sine
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice, Gate
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes

# mostly fundamental with a touch of 2nd/3rd harmonic - rounded, sub-heavy tone
SUB_HARMONICS = [1, 0.15, 0.05]


class BassDrone(Gate, ContinuousVoice):
    """Slow-swelling sub drone: a near-static low fundamental that breathes in and out in level rather than changing pitch or timbre."""

    title = "Bass - slow-swelling sub drone"
    summary = "Slow-breathing sub bed that swells and recedes."
    volume = Patch.volume.replace(default=0.8)

    # the graph, assigned by build(); finish() retains every one of them
    root_freq_sig: SigTo
    swell_period_sig: SigTo
    swell_depth_sig: SigTo
    filter_base_sig: SigTo
    filter_res_sig: SigTo
    swell_frequency: PyoObject
    swell_amplitude: PyoObject
    swell: Sine
    sub_table: HarmTable
    sub_osc: Osc
    output: MoogLP

    @Param(
        notes.E0,
        notes.E2,
        1,
        notes.E1,
        "Register",
        "Sets the fixed pitch of the sub drone.",
        scale="note",
    )
    def root_freq(self, value: float) -> None:
        self.root_freq_sig.value = value

    @Param(
        2,
        30,
        0.5,
        9.0,
        "Breathing rate",
        "How long one swell cycle takes; longer feels like a slow tide, shorter reads as a more rhythmic "
        "pulse.",
        sweep=True,
    )
    def swell_period(self, value: float) -> None:
        self.swell_period_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.4,
        "Swell depth",
        "How dramatic the level swell is; higher makes the breathing more audible, lower keeps the drone "
        "closer to constant.",
        sweep=True,
    )
    def swell_depth(self, value: float) -> None:
        self.swell_depth_sig.value = value

    @Param(
        60,
        500,
        10,
        180,
        "Brightness",
        "Darkens or brightens the low end; lower keeps it duller and softer, higher lets more harmonic "
        "content through.",
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
        "Adds emphasis around the cutoff; kept low here so the drone stays smooth rather than whistly.",
        sweep=True,
    )
    def filter_res(self, value: float) -> None:
        self.filter_res_sig.value = value

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()
        self.root_freq_sig = self.live(type(self).root_freq)
        self.swell_period_sig = self.live(type(self).swell_period)
        self.swell_depth_sig = self.live(type(self).swell_depth)
        self.filter_base_sig = self.live(type(self).filter_base)
        self.filter_res_sig = self.live(type(self).filter_res)

        self.swell_frequency = 1 / self.swell_period_sig
        self.swell_amplitude = self.swell_depth_sig / 2
        self.swell = Sine(
            freq=self.swell_frequency,
            mul=self.swell_amplitude,
            add=1 - self.swell_depth / 2,
        )

        self.sub_table = HarmTable(SUB_HARMONICS)
        self.sub_osc = Osc(
            table=self.sub_table, freq=self.root_freq_sig, mul=self.swell
        )
        self.output = MoogLP(
            self.sub_osc, freq=self.filter_base_sig, res=self.filter_res_sig
        )
        return self.finish(self.add_gate(self.output, context))
