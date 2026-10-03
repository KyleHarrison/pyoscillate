# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone
"""Slow-winding FM drone: the drone family's "slow pitch steps" style, paired
with continuous FM timbre drift.

The centre holds for whole bars at a time - far slower than the bass (per
16th), arp (per 8th), or either hat - then glides to a new note instead of
snapping, so the pitch change reads as a drift rather than an event. Ratio
and index each ride their own slow LFO, independent of the pitch steps, so
the timbre keeps evolving between note changes too.
"""

from __future__ import annotations

from typing import ClassVar

from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM, Sine

from pyoscillate.intervals import Walk
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice, Gate
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes

# mostly small steps so the pitch glides rather than leaps
### One pre-existing latent bug was surfaced but deliberately left alone (out of scope, no sonic-behavior changes were part of this task): tonal/drone's base Drone.next_step snapshots root_freq at build time rather than reading it live, so a live Register-slider move doesn't affect future note steps. Worth a separate follow-up if you want it fixed.


class Drone(Gate, ContinuousVoice):
    """Slow-winding FM drone: note changes once every 8 bars, with a continuously drifting timbre."""

    summary = "Slow-winding sustained drone that rarely changes note."
    volume = Patch.volume.replace(default=1.0)
    # bars between note-step changes
    step_bars: ClassVar[int] = 8

    # the graph, assigned by build(); finish() retains every one of them
    drone_freq_sig: SigTo
    ratio_lfo: Sine
    index_lfo: Sine
    fm_voice: FM
    reverb: Freeverb

    @Param(
        notes.A1,
        notes.A3,
        1,
        notes.Fs3,
        "Register",
        "Moves the drone's register; higher brings it closer to the arp and reads as more melodic, lower "
        "pushes it toward a sustained sub layer.",
        scale="note",
    )
    def root_freq(self, value: float) -> None:
        self.drone_freq_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.7,
        "Space",
        "Sets how vast the drone's reverb tail feels, from a tighter presence to a huge, cavernous wash.",
        sweep=True,
    )
    def reverb_size(self, value: float) -> None:
        self.reverb.size = value

    @Param(
        0,
        1,
        0.05,
        0.7,
        "Tail darkness",
        "Controls how bright or muffled the reverb tail sounds as it decays; lower keeps it shimmering, "
        "higher makes it warmer and duller.",
        sweep=True,
    )
    def reverb_damp(self, value: float) -> None:
        self.reverb.damp = value

    @Param(
        0,
        1,
        0.05,
        0.9,
        "Distance",
        "Blends dry tone against reverb; higher dissolves the drone into a diffuse atmospheric bed, lower "
        "keeps the raw pitch more present.",
        sweep=True,
    )
    def reverb_bal(self, value: float) -> None:
        self.reverb.bal = value

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()
        # the drone changes note far more slowly than the bass (per 16th),
        # arp (per 8th), or either hat
        step_time = context.tempo.bar * self.step_bars

        # glides to each new frequency over most of the step time instead of snapping
        self.drone_freq_sig = self.live(type(self).root_freq, time=step_time * 0.9)

        # ratio and index each ride their own slow LFO, with periods measured in
        # whole drone steps, so the tone keeps evolving independently of pitch changes
        self.ratio_lfo = Sine(freq=1 / (step_time * 1.3), mul=0.2, add=1.5)
        self.index_lfo = Sine(freq=1 / (step_time * 0.7), mul=2, add=3)

        self.fm_voice = FM(
            carrier=self.drone_freq_sig,
            ratio=self.ratio_lfo,
            index=self.index_lfo,
            mul=0.2,
        )
        self.reverb = Freeverb(
            self.fm_voice,
            size=self.reverb_size,
            damp=self.reverb_damp,
            bal=self.reverb_bal,
        )

        root_freq = self.root_freq
        step = {"i": 0}

        def next_step() -> None:
            i = step["i"] % len(Walk.DRONE_WANDER.value)
            self.drone_freq_sig.value = root_freq * pow(
                2, Walk.DRONE_WANDER.value[i] / 12
            )
            step["i"] += 1

        # a drone has no trigger-to-envelope path, but its slow scheduled
        # pitch step still needs to start/stop with the patch, so this
        # replaces ContinuousVoice's no-op sequencer with a real division
        self.sequencer = context.clock.subscribe(
            context.clock.bar * self.step_bars, next_step
        )
        return self.finish(self.add_gate(self.reverb, context))
