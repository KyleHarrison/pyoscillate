"""Offbeat chord-stab voices."""

from typing import Any, ClassVar

from pyo import PyoTableObject
from pyo.lib.effects import Chorus, Freeverb
from pyo.lib.filters import Biquad
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable, SawTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec, rate_slider
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "octave",
        -1,
        1,
        1,
        0,
        "Register",
        "Moves the chord stabs down an octave for a darker, lower bed or up an octave to "
        "sit clearer above the bass; the chords always follow the rack's key and progression.",
    ),
    SliderSpec(
        "brightness",
        300,
        5000,
        50,
        1500,
        "Brightness",
        "Opens or closes the stab's tone, from a dark, rounded voicing to a brighter, more cutting one.",
    ),
    rate_slider(
        BASE_DIVISION,
        "Halves or doubles the chord-stab pattern speed for each step away from its 16th-note grid.",
    ),
)
# i-iv-bVII-v as parallel minor-seventh stabs, one chord per bar - used
# only when the patch runs outside a rack that shares its own `Harmony`
FALLBACK_HARMONY = Harmony(progression=(0, 5, 10, 7))
INTERVALS = (0, 3, 7, 10)
# every chord root snaps to the octave nearest this, around D3
REGISTER_CENTRE = 146
VOLUME_DEFAULT = 0.4


class Chord(Patch):
    """Offbeat minor-seventh chord stab, following `harmony`'s current-bar
    chord. Style variants subclass this and override `table()` for their
    own oscillator table, plus the profile attributes below; the rest of
    the graph is identical across styles."""

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    needs_tempo: ClassVar[bool] = True
    needs_clock: ClassVar[bool] = True
    needs_harmony: ClassVar[bool] = True

    # envelope duration (s), reverb wet balance, chorus on/off - overridden
    # per style
    duration: ClassVar[float]
    wet: ClassVar[float]
    chorus: ClassVar[bool] = False

    octave: float
    brightness: float
    rate: float

    def table(self) -> PyoTableObject:
        """This style's oscillator table. Overridden per style."""
        raise NotImplementedError

    def build(
        self, tempo: Tempo, clock: Clock, harmony: Harmony | None = None, **values: Any
    ) -> Patch:
        self.configure(**values)
        self._reset()
        harmony = harmony or FALLBACK_HARMONY

        table = self.table()
        trigger = Trig()
        envelope_table = CosTable([(0, 0), (200, 1), (2500, 0.55), (8191, 0)])
        envelope = TrigEnv(trigger, envelope_table, dur=self.duration)
        amplitude = envelope * 0.19
        voices = [
            Osc(
                table,
                freq=harmony.chord_freq(REGISTER_CENTRE, clock.bar_index)
                * 2 ** (self.octave + interval / 12),
                mul=amplitude,
            )
            for interval in INTERVALS
        ]
        source = sum(voices)
        filter_voice = Biquad(source, freq=self.brightness, q=1.2, type=0)
        voice = filter_voice
        chorus_voice = None
        if self.chorus:
            chorus_voice = Chorus(voice, depth=1.2, feedback=0.15, bal=0.28)
            voice = chorus_voice
        voice = Freeverb(voice, size=0.72, damp=0.45, bal=self.wet)
        self.retain(
            table, trigger, envelope_table, envelope, amplitude, *voices, source, filter_voice, chorus_voice
        )

        state = {"step": 0, "octave": self.octave}

        def next_step() -> None:
            step = state["step"] % 16
            if step % 4 == 2:
                chord_root = (
                    harmony.chord_freq(REGISTER_CENTRE, clock.bar_index) * 2 ** state["octave"]
                )
                for oscillator, interval in zip(voices, INTERVALS, strict=True):
                    oscillator.freq = chord_root * 2 ** (interval / 12)
                trigger.play()
            state["step"] += 1

        division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, self.rate), next_step)
        self.sequencer = division
        self.voice = voice
        self.controls = {
            "octave": lambda value: state.update(octave=value),
            "brightness": lambda value: setattr(filter_voice, "freq", value),
            "rate": lambda value: setattr(
                division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        }
        return self


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
