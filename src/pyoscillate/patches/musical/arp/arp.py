# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.arp.arp
"""Slow, fixed pentatonic arpeggio locked to the shared clock.

A single FM voice's carrier frequency glides to each new step's pentatonic
target via a `SigTo`, so the melody drifts continuously between pitches
instead of being plucked note by note.
"""

from __future__ import annotations

from collections.abc import Callable

from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import GatedVoice, Step
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes

# major pentatonic - consonant, calm, no leading tones to create tension
MID_INTERVALS = [0, 2, 4, 7, 9, 12, 9, 7, 4, 2]

MID_ROOT = notes.E4  # current default


class Arp(GatedVoice):
    """Calm, consonant melodic line locked to the groove.

    `step_bars` is a `rebuild` parameter: it sets the `SigTo` glide
    time and the clock division at build time, so changing it live can't
    just update an existing control.
    """

    name = "mid_arp"
    title = "Mid - slow pentatonic arpeggio"
    summary = "Calm, consonant melodic line locked to the groove."
    volume = Patch.volume.replace(default=0.6)

    # the root frequency the running step sequence steps from, frozen at
    # build time - `root_freq`'s own control re-pitches whatever note is
    # currently gliding, but (as before migration) doesn't retroactively
    # change the interval walk's root until the next rebuild
    step_root_freq: float
    _step: Callable[[], Step]

    mid_freq: SigTo
    fm_voice: FM
    reverb: Freeverb

    @Param(
        notes.A2,
        notes.E5,
        1,
        MID_ROOT,
        "Register",
        "Shifts the melody up or down in pitch relative to the pads and bass beneath it.",
        scale="note",
    )
    def root_freq(self, value: float) -> None:
        self.mid_freq.value = value

    step_bars = Param(
        1,
        8,
        1,
        2,
        "Pace",
        "Sets how often the melody moves; fewer bars feels more active, more bars stretches it "
        "into a slower, more spacious unfolding.",
        rebuild=True,
    )

    @Param(
        0.5,
        4,
        0.1,
        1.5,
        "Tone character",
        "Detunes the melody's overtones; near a simple ratio sounds clean and bell-like, drifting "
        "away adds a warmer, more unstable shimmer.",
        sweep=True,
    )
    def fm_ratio(self, value: float) -> None:
        self.fm_voice.ratio = value

    @Param(
        0,
        6,
        0.1,
        1.5,
        "Brightness",
        "Moves the melody from a plain, mellow tone to a brighter, buzzier, more harmonically "
        "complex one.",
        sweep=True,
    )
    def fm_index(self, value: float) -> None:
        self.fm_voice.index = value

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Space",
        "Sets how large and distant the melody's room feels, from a tight presence to a huge, "
        "cavernous decay.",
        sweep=True,
    )
    def reverb_size(self, value: float) -> None:
        self.reverb.size = value

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, "
        "lower settings stay bright and shimmering.",
        sweep=True,
    )
    def reverb_damp(self, value: float) -> None:
        self.reverb.damp = value

    @Param(
        0,
        1,
        0.05,
        0.4,
        "Distance",
        "Blends how much of the melody is heard through the reverb versus dry; higher dissolves "
        "it into the atmosphere, lower keeps it present and up front.",
        sweep=True,
    )
    def reverb_bal(self, value: float) -> None:
        self.reverb.bal = value

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        step_time = context.tempo.bar * self.step_bars

        # glides to each new note over most of the step time instead of
        # snapping, so the melody drifts between pitches rather than
        # plucking them
        self.mid_freq = SigTo(value=self.root_freq, time=step_time * 0.85)
        self.fm_voice = FM(
            carrier=self.mid_freq, ratio=self.fm_ratio, index=self.fm_index, mul=0.18
        )
        self.reverb = Freeverb(
            self.fm_voice,
            size=self.reverb_size,
            damp=self.reverb_damp,
            bal=self.reverb_bal,
        )

        self.step_root_freq = self.root_freq
        self._step = self.step_pattern(
            len(MID_INTERVALS), dict(enumerate(MID_INTERVALS))
        )

        # `step_bars` counts whole bars, not a `NoteDivision` offset
        self.schedule_steps(
            context.clock, context.clock.bar * self.step_bars, self.next_step
        )
        return self.finish(self.reverb)

    def next_step(self) -> None:
        step = self._step()
        self.mid_freq.value = self.step_root_freq * pow(2, step.value / 12)
