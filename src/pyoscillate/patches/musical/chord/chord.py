# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.chord.chord style=velvet
#   style: velvet | organ | shimmer
"""Offbeat chord-stab voices."""

from collections.abc import Callable
from typing import ClassVar

from pyo import PyoObject, PyoTableObject
from pyo.lib.effects import Chorus, Freeverb
from pyo.lib.filters import Biquad
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable, SawTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import GatedVoice, Step
from pyoscillate.patches.params import Param, rate_param

INTERVALS = (0, 3, 7, 10)


class Chord(GatedVoice):
    """Offbeat minor-seventh chord stab, following `harmony`'s current-bar
    chord. Style variants subclass this and override `table()` for their
    own oscillator table, plus the profile attributes below; the rest of
    the graph is identical across styles."""

    volume = Patch.volume.replace(default=0.4)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH

    # every chord root snaps to the octave nearest this, around D3
    register_centre: ClassVar[float] = 146

    # envelope duration (s), reverb wet balance, chorus on/off - overridden
    # per style
    duration: ClassVar[float]
    wet: ClassVar[float]
    chorus: ClassVar[bool] = False

    # the graph, assigned by build(); finish() retains every one of them
    envelope_table: CosTable
    chord_env: TrigEnv
    amplitude: PyoObject
    oscillator_table: PyoTableObject
    voices: list[Osc]
    source: PyoObject
    filter_voice: Biquad
    # only assigned by styles with `chorus` on
    chorus_voice: Chorus
    reverb: Freeverb

    # this bar's chord source, frozen at build time - fed to `next_step`,
    # which build() can no longer close over now that it's a real method
    harmony: Harmony
    _step: Callable[[], Step]

    def table(self) -> PyoTableObject:
        """This style's oscillator table. Overridden per style."""
        raise NotImplementedError

    octave = Param(
        -1,
        1,
        1,
        0,
        "Register",
        "Moves the chord stabs down an octave for a darker, lower bed or up an octave to sit "
        "clearer above the bass; the chords always follow the rack's key and progression.",
    )

    @Param(
        300,
        5000,
        50,
        1500,
        "Brightness",
        "Opens or closes the stab's tone, from a dark, rounded voicing to a brighter, more cutting "
        "one.",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.filter_voice.freq = value

    rate = rate_param(
        base_division,
        "Halves or doubles the chord-stab pattern speed for each step away from its 16th-note grid.",
    )

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony

        self.oscillator_table = self.table()
        self.envelope_table = CosTable([(0, 0), (200, 1), (2500, 0.55), (8191, 0)])
        self.chord_env = TrigEnv(self.trigger, self.envelope_table, dur=self.duration)
        self.amplitude = self.chord_env * 0.19
        self.voices = [
            Osc(
                self.oscillator_table,
                freq=self.harmony.chord_freq(
                    self.register_centre, context.clock.bar_index
                )
                * 2 ** (self.octave + interval / 12),
                mul=self.amplitude,
            )
            for interval in INTERVALS
        ]
        self.retain(*self.voices)
        self.source = sum(self.voices)
        self.filter_voice = Biquad(self.source, freq=self.brightness, q=1.2, type=0)

        pre_reverb: PyoObject = self.filter_voice
        if self.chorus:
            self.chorus_voice = Chorus(
                self.filter_voice, depth=1.2, feedback=0.15, bal=0.28
            )
            pre_reverb = self.chorus_voice
        self.reverb = Freeverb(pre_reverb, size=0.72, damp=0.45, bal=self.wet)

        # fires on the third 16th of every 4-step group, i.e. every offbeat
        # 16th-note pair within the bar
        self._step = self.step_pattern(16, {2, 6, 10, 14})

        self.schedule(self.base_division, self.rate, context.clock)
        return self.finish(self.reverb)

    def next_step(self) -> None:
        if self._step().hit:
            chord_root = (
                self.harmony.chord_freq(self.register_centre, self._clock.bar_index)
                * 2**self.octave
            )
            for oscillator, interval in zip(self.voices, INTERVALS, strict=True):
                oscillator.freq = chord_root * 2 ** (interval / 12)
            self.trigger.play()


class ChordVelvet(Chord):
    """Warm, rounded minor-seventh chord stabs."""

    title = "Chord Stab - Velvet"
    duration, wet = 0.34, 0.42

    def table(self) -> PyoTableObject:
        return HarmTable([1, 0.25, 0.12])


class ChordOrgan(Chord):
    """Sustained, organ-like harmonic bed."""

    title = "Chord Stab - Organ"
    duration, wet = 0.22, 0.2

    def table(self) -> PyoTableObject:
        return HarmTable([1, 0.7, 0.4, 0.2])


class ChordShimmer(Chord):
    """Bright, shimmering chord stabs with more edge."""

    title = "Chord Stab - Shimmer"
    duration, wet, chorus = 0.42, 0.58, True

    def table(self) -> PyoTableObject:
        return SawTable(order=12)
