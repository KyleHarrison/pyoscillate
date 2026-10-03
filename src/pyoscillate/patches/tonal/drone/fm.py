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
from pyo.lib.effects import Delay, Freeverb
from pyo.lib.generators import FM, Lorenz, Rossler

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice, Gate
from pyoscillate.patches.params import Param
from pyoscillate.theory import notes


class SoundscapeFm(Gate, ContinuousVoice):
    """Free-running FM pad whose timbre is driven entirely by chaotic attractors, with no clocked note pattern at all."""

    title = "Soundscape - chaotic FM pad"
    summary = "Slow-morphing, unpredictable pad that never quite repeats itself."
    volume = Patch.volume.replace(default=0.6)

    # the graph, assigned by build(); finish() retains every one of them
    root_freq_sig: SigTo
    chaos_speed_sig: SigTo
    chaos_amount_sig: SigTo
    reverb_size_sig: SigTo
    reverb_damp_sig: SigTo
    reverb_bal_sig: SigTo
    delay_time_sig: SigTo
    delay_feedback_sig: SigTo
    ratio_chaos: Rossler
    index_speed: PyoObject
    index_chaos: Lorenz
    fm_voice: FM
    reverb_voice: Freeverb
    output: Delay

    @Param(
        notes.A1,
        notes.A3,
        1,
        notes.A2,
        "Register",
        "Sets the pad's held pitch, the carrier tone everything else is built on.",
        scale="note",
    )
    def root_freq(self, value: float) -> None:
        self.root_freq_sig.value = value

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

    @Param(
        0,
        1,
        0.05,
        0.85,
        "Space",
        "Sets how enveloping the pad's room feels; larger is more immersive and distant.",
        sweep=True,
    )
    def reverb_size(self, value: float) -> None:
        self.reverb_size_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.4,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher is warmer and more muffled, lower stays brighter and "
        "shimmering.",
        sweep=True,
    )
    def reverb_damp(self, value: float) -> None:
        self.reverb_damp_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.85,
        "Distance",
        "Blends how much of the pad is heard through the reverb versus dry; higher dissolves it into the "
        "space, lower keeps it present.",
        sweep=True,
    )
    def reverb_bal(self, value: float) -> None:
        self.reverb_bal_sig.value = value

    @Param(
        0.05,
        2,
        0.05,
        0.6,
        "Echo spacing",
        "Sets the time between echo repeats, smearing the timbral drift across time.",
        sweep=True,
    )
    def delay_time(self, value: float) -> None:
        self.delay_time_sig.value = value

    @Param(
        0,
        0.9,
        0.05,
        0.35,
        "Echo density",
        "Sets how many times each echo repeats before decaying; higher creates a denser, more layered wash.",
        sweep=True,
    )
    def delay_feedback(self, value: float) -> None:
        self.delay_feedback_sig.value = value

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()
        self.root_freq_sig = self.live(type(self).root_freq)
        self.chaos_speed_sig = self.live(type(self).chaos_speed)
        self.chaos_amount_sig = self.live(type(self).chaos_amount)
        self.reverb_size_sig = self.live(type(self).reverb_size)
        self.reverb_damp_sig = self.live(type(self).reverb_damp)
        self.reverb_bal_sig = self.live(type(self).reverb_bal)
        self.delay_time_sig = self.live(type(self).delay_time)
        self.delay_feedback_sig = self.live(type(self).delay_feedback)

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
        self.reverb_voice = Freeverb(
            self.fm_voice,
            size=self.reverb_size_sig,
            damp=self.reverb_damp_sig,
            bal=self.reverb_bal_sig,
        )
        self.output = Delay(
            self.reverb_voice,
            delay=self.delay_time_sig,
            feedback=self.delay_feedback_sig,
            maxdelay=2,
        )
        return self.finish(self.add_gate(self.output, context))
