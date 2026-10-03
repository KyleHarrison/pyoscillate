# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.arp.arp
"""Slow, fixed pentatonic arpeggio locked to the shared clock.

A single FM voice's carrier frequency glides to each new step's pentatonic
target via a `SigTo`, so the melody drifts continuously between pitches
instead of being plucked note by note.
"""

from __future__ import annotations

from collections.abc import Callable

from pyo.lib.controls import SigTo
from pyo.lib.generators import FM

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Gate, GatedVoice, Reverb, Step
from pyoscillate.patches.params import Param
from pyoscillate.theory import notes
from pyoscillate.theory.harmony import Harmony
from pyoscillate.theory.intervals import ArpOrder, Scale

MID_ROOT = notes.E4  # current default


class Arp(Gate, Reverb, GatedVoice):
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
    harmony: Harmony
    _step: Callable[[], Step]

    mid_freq: SigTo
    fm_voice: FM

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

    contour = Param(
        0,
        6,
        1,
        0,
        "Contour",
        "Sets the shape the melody traces through its notes: 0 climbs and falls in one arch, "
        "1 only rises, 2 only falls, 3 repeats a short three-note climb, 4 alternates four up "
        "with four down, 5 rises and falls then stutters, 6 rises and snaps back to the root. "
        "Notes come from a calm major pentatonic, so every contour stays consonant.",
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

    def build(self, context: BuildContext) -> Patch:
        self._reset()

        # glides to each new note over most of the step time instead of
        # snapping, so the melody drifts between pitches rather than
        # plucking them
        self.mid_freq = SigTo(
            value=self.root_freq, time=context.tempo.bar * self.step_bars * 0.85
        )
        self.fm_voice = FM(
            carrier=self.mid_freq, ratio=self.fm_ratio, index=self.fm_index, mul=0.18
        )
        self.sync(
            context.tempo,
            lambda t: setattr(self.mid_freq, "time", t.bar * self.step_bars * 0.85),
        )
        self.reverb = self.add_reverb(self.fm_voice)

        self.harmony = context.harmony
        self.step_root_freq = self.root_freq
        # a calm major pentatonic - consonant, no leading tones to create tension
        order = ArpOrder.by_index(int(self.contour))
        self._step = self.step_pattern(
            order.cycle, order.steps(Scale.MAJOR_PENTATONIC_OCTAVE.value)
        )

        # `step_bars` counts whole bars, not a `NoteDivision` offset
        self.schedule_steps(
            context.clock, context.clock.bar * self.step_bars, self.next_step
        )
        return self.finish(self.add_gate(self.reverb, context))

    def next_step(self) -> None:
        step = self._step()
        self.mid_freq.value = self.harmony.quantise(
            self.step_root_freq * pow(2, step.value / 12)
        )
