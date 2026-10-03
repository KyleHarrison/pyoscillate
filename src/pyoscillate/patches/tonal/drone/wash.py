# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.wash
"""Washy detuned pad: a SuperSaw voice smeared with chorus, reverb, and delay
for a shoegaze-style dream-pop ambience.

This is the drone family's "space" style - unlike `fm`/`filter`, the
"evolving" quality here comes mostly from spatial smear (chorus/reverb/delay)
rather than timbral or filter movement, so the character is width and haze
rather than wander.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.effects import Chorus
from pyo.lib.filters import Tone
from pyo.lib.generators import Rossler, Sine, SuperSaw

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice, Echo, Gate, Reverb, RootPitch
from pyoscillate.patches.params import Param
from pyoscillate.theory import notes


class SoundscapeWash(Gate, Reverb, Echo, RootPitch, ContinuousVoice):
    """Washy detuned pad: a SuperSaw voice smeared with chorus, reverb, and delay for a shoegaze-style dream-pop ambience.

    Unlike `SoundscapeFm`/`SoundscapeFilter`, the "evolving" quality here
    comes mostly from spatial smear (chorus/reverb/delay) rather than
    timbral or filter movement - the character is width and haze rather
    than wander.
    """

    title = "Soundscape - washy detuned pad"
    summary = "Wide, hazy detuned wash that dissolves into echoing space."
    volume = Patch.volume.replace(default=0.6)
    EVOLUTION_VARIANTS: ClassVar[tuple[tuple[float, float], ...]] = (
        (1.0, 1.0),
        (1.2, 1.1),
    )

    # the graph, assigned by build(); finish() retains every one of them
    root_freq_sig: SigTo
    detune_sig: SigTo
    detune_bal_sig: SigTo
    pitch_drift_sig: SigTo
    chorus_depth_sig: SigTo
    chorus_feedback_sig: SigTo
    chorus_bal_sig: SigTo
    pitch_wander: Rossler
    saw_voice: SuperSaw
    softened: Tone
    chorus_motion: Sine
    chorused: Chorus
    output: PyoObject

    root_freq = RootPitch.root_freq.replace(
        minimum=notes.A1,
        default=notes.E3,
        help_text="Sets the wash's base pitch.",
    )

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Thickness",
        "Spreads the oscillators apart in pitch; higher makes the wash thicker and hazier, lower keeps it "
        "cleaner and more focused.",
        sweep=True,
    )
    def detune(self, value: float) -> None:
        self.detune_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.7,
        "Detune blend",
        "Balances how much of the detuned layers come through versus the centered tone; higher leans "
        "further into the thick, chorused character.",
        sweep=True,
    )
    def detune_bal(self, value: float) -> None:
        self.detune_bal_sig.value = value

    @Param(
        0,
        1,
        0.01,
        0.03,
        "Instability",
        "Adds slow pitch wobble; higher makes the wash feel more alive and unstable, lower keeps it steadier.",
        sweep=True,
    )
    def pitch_drift(self, value: float) -> None:
        self.pitch_drift_sig.value = value

    @Param(
        0,
        5,
        0.1,
        2.5,
        "Shimmer",
        "Deepens the chorus modulation for a wider, more shimmering movement; lower keeps it subtler and "
        "more static.",
        sweep=True,
    )
    def chorus_depth(self, value: float) -> None:
        self.chorus_depth_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.35,
        "Chorus density",
        "Adds more layered repeats to the chorus effect for a denser, more swirling texture.",
        sweep=True,
    )
    def chorus_feedback(self, value: float) -> None:
        self.chorus_feedback_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Chorus blend",
        "Blends how much of the chorused signal is heard versus the dry tone; higher leans further into "
        "the wide, shimmering effect.",
        sweep=True,
    )
    def chorus_bal(self, value: float) -> None:
        self.chorus_bal_sig.value = value

    reverb_size = Reverb.reverb_size.replace(default=0.9)
    reverb_damp = Reverb.reverb_damp.replace(default=0.35)
    reverb_bal = Reverb.reverb_bal.replace(default=0.9)

    delay_time = Echo.delay_time.replace(default=0.8)
    delay_feedback = Echo.delay_feedback.replace(default=0.25)

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()
        self.root_freq_sig = self.live(type(self).root_freq)
        self.detune_sig = self.live(type(self).detune)
        self.detune_bal_sig = self.live(type(self).detune_bal)
        self.pitch_drift_sig = self.live(type(self).pitch_drift)
        self.chorus_depth_sig = self.live(type(self).chorus_depth)
        self.chorus_feedback_sig = self.live(type(self).chorus_feedback)
        self.chorus_bal_sig = self.live(type(self).chorus_bal)

        # subtle, slow pitch instability rather than a discrete note pattern -
        # keeps the drone "dreamy" without ever resolving to a new pitch
        self.pitch_wander = Rossler(
            pitch=0.02, chaos=0.4, mul=self.pitch_drift_sig, add=self.root_freq_sig
        )

        self.saw_voice = SuperSaw(
            freq=self.pitch_wander,
            detune=self.detune_sig,
            bal=self.detune_bal_sig,
            mul=0.2,
        )
        self.softened = Tone(self.saw_voice, freq=self.root_freq_sig * 4)
        self.chorus_motion = Sine(
            freq=0.12, mul=self.chorus_bal_sig * 0.4, add=self.chorus_bal_sig * 0.6
        )
        self.chorused = Chorus(
            self.softened,
            depth=self.chorus_depth_sig,
            feedback=self.chorus_feedback_sig,
            bal=self.chorus_motion,
        )
        self.reverb = self.add_reverb(self.chorused)
        self.echo = self.add_echo(self.reverb)
        self.output = self.reverb + self.echo * 0.3
        return self.finish(self.add_gate(self.output, context))

    def on_evolve(self, index: int) -> None:
        depth_scale, feedback_scale = self.EVOLUTION_VARIANTS[
            index % len(self.EVOLUTION_VARIANTS)
        ]
        self.chorus_depth_sig.value = min(
            type(self).chorus_depth.spec.maximum, self.chorus_depth * depth_scale
        )
        self.delay_feedback_sig.value = min(
            type(self).delay_feedback.spec.maximum, self.delay_feedback * feedback_scale
        )
