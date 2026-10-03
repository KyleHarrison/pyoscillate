# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.fm
"""Chaotic FM drone: a free-running FM voice whose timbre is driven entirely
by chaotic attractors, with no clocked note pattern at all.

This is the drone family's "timbre" style - the held pitch itself never
moves; movement instead comes from ratio and index each riding their own
chaotic attractor. Rossler wanders smoothly, Lorenz more angularly - pairing
them on ratio and index gives the timbre two independently-textured axes of
drift instead of both parameters moving in the same "shape" of way.
"""

from __future__ import annotations

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.generators import FM, Lorenz, Rossler

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice, Echo, Gate, Reverb, RootPitch
from pyoscillate.patches.params import Param
from pyoscillate.theory.pitch import Note


class SoundscapeFm(Gate, Reverb, Echo, RootPitch, ContinuousVoice):
    """Free-running FM pad whose timbre is driven entirely by chaotic attractors, with no clocked note pattern at all."""

    title = "Soundscape - chaotic FM pad"
    summary = "Slow-morphing, unpredictable pad that never quite repeats itself."
    volume = Patch.volume.replace(default=0.6)

    # the graph, assigned by build(); finish() retains every one of them
    root_freq_sig: SigTo
    chaos_speed_sig: SigTo
    chaos_amount_sig: SigTo
    ratio_chaos: Rossler
    index_speed: PyoObject
    index_chaos: Lorenz
    fm_voice: FM

    root_freq = RootPitch.root_freq.replace(
        minimum=Note.A1,
        maximum=Note.A3,
        default=Note.A2,
        help_text="Sets the pad's held pitch, the carrier tone everything else is built on.",
    )

    @Param(
        0.01,
        0.5,
        0.01,
        0.04,
        "Drift speed",
        "How fast the pad's timbre wanders; lower is slower and more hypnotic, higher feels more restless.",
        sweep=True,
    )
    def chaos_speed(self, value: float) -> None:
        self.chaos_speed_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Instability",
        "How unpredictable the wander is; higher feels more psychedelic and alive, lower stays closer to "
        "a steady tone.",
        sweep=True,
    )
    def chaos_amount(self, value: float) -> None:
        self.chaos_amount_sig.value = value

    reverb_size = Reverb.reverb_size.replace(default=0.85)
    reverb_damp = Reverb.reverb_damp.replace(default=0.4)
    reverb_bal = Reverb.reverb_bal.replace(default=0.85)

    delay_time = Echo.delay_time.replace(default=0.6)
    delay_feedback = Echo.delay_feedback.replace(default=0.35)

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()
        self.root_freq_sig = self.live(type(self).root_freq)
        self.chaos_speed_sig = self.live(type(self).chaos_speed)
        self.chaos_amount_sig = self.live(type(self).chaos_amount)

        self.ratio_chaos = Rossler(
            pitch=self.chaos_speed_sig, chaos=self.chaos_amount_sig, mul=0.4, add=1.5
        )
        self.index_speed = self.chaos_speed_sig * 1.3
        self.index_chaos = Lorenz(
            pitch=self.index_speed, chaos=self.chaos_amount_sig, mul=3, add=4
        )

        self.fm_voice = FM(
            carrier=self.root_freq_sig,
            ratio=self.ratio_chaos,
            index=self.index_chaos,
            mul=0.2,
        )
        self.reverb = self.add_reverb(self.fm_voice)
        self.output = self.add_echo(self.reverb)
        return self.finish(self.add_gate(self.output, context))
