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
from pyo.lib.effects import Chorus, Delay, Freeverb
from pyo.lib.filters import Tone
from pyo.lib.generators import Rossler, Sine, SuperSaw

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes


class SoundscapeWash(ContinuousVoice):
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
    reverb_size_sig: SigTo
    reverb_damp_sig: SigTo
    reverb_bal_sig: SigTo
    delay_time_sig: SigTo
    delay_feedback_sig: SigTo
    pitch_wander: Rossler
    saw_voice: SuperSaw
    softened: Tone
    chorus_motion: Sine
    chorused: Chorus
    reverb_voice: Freeverb
    echo: Delay
    output: PyoObject

    @Param(
        notes.A1,
        notes.A4,
        1,
        notes.E3,
        "Register",
        "Sets the wash's base pitch.",
        scale="note",
    )
    def root_freq(self, value: float) -> None:
        self.root_freq_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Thickness",
        "Spreads the oscillators apart in pitch; higher makes the wash thicker and hazier, lower keeps it "
        "cleaner and more focused.",
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
    )
    def chorus_bal(self, value: float) -> None:
        self.chorus_bal_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.9,
        "Space",
        "Sets how large and distant the wash's room feels, from a tight presence to a huge, cavernous decay.",
    )
    def reverb_size(self, value: float) -> None:
        self.reverb_size_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.35,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower "
        "settings stay bright and shimmering.",
    )
    def reverb_damp(self, value: float) -> None:
        self.reverb_damp_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.9,
        "Distance",
        "Blends how much of the wash is heard through the reverb versus dry; higher dissolves it into the "
        "atmosphere, lower keeps it present.",
    )
    def reverb_bal(self, value: float) -> None:
        self.reverb_bal_sig.value = value

    @Param(
        0.05,
        2,
        0.05,
        0.8,
        "Echo spacing",
        "Sets the time between echo repeats, smearing the wash across time.",
    )
    def delay_time(self, value: float) -> None:
        self.delay_time_sig.value = value

    @Param(
        0,
        0.9,
        0.05,
        0.25,
        "Echo density",
        "Sets how many times each echo repeats before fading; higher creates a denser, more layered wash.",
    )
    def delay_feedback(self, value: float) -> None:
        self.delay_feedback_sig.value = value

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
        self.reverb_size_sig = self.live(type(self).reverb_size)
        self.reverb_damp_sig = self.live(type(self).reverb_damp)
        self.reverb_bal_sig = self.live(type(self).reverb_bal)
        self.delay_time_sig = self.live(type(self).delay_time)
        self.delay_feedback_sig = self.live(type(self).delay_feedback)

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
        self.reverb_voice = Freeverb(
            self.chorused,
            size=self.reverb_size_sig,
            damp=self.reverb_damp_sig,
            bal=self.reverb_bal_sig,
        )
        self.echo = Delay(
            self.reverb_voice,
            delay=self.delay_time_sig,
            feedback=self.delay_feedback_sig,
            maxdelay=2,
        )
        self.output = self.reverb_voice + self.echo * 0.3
        return self.finish(self.output)

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
