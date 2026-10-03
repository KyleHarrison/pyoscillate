# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.stab.stab
#   style: velvet | organ | shimmer
"""Offbeat chord-stab voices."""

import random
from typing import ClassVar

from pyo import PyoObject, PyoTableObject
from pyo.lib.effects import Chorus, Delay, Freeverb
from pyo.lib.filters import Biquad
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable, SawTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Gate, GatedVoice, Phrased
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.phrase import PhraseRole, Rhythms
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.scale import Scale, Scales


class Stab(Gate, Phrased, GatedVoice):
    """Offbeat minor-seventh chord stab, following `harmony`'s current-bar
    chord. Style variants subclass this and override `table()` for their
    own oscillator table, plus the profile attributes below; the rest of
    the graph is identical across styles."""

    volume = Patch.volume.replace(default=0.4)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH
    # a stab on every offbeat 16th of the bar
    phrase_roles = (PhraseRole.CHORD_HIT,)
    phrase = Phrased.phrase.replace(
        default=Rhythms.OFFBEAT_HOUSE,
        help_text="Picks when in the bar the hits fall, from a plain pulse to a backbeat or a swung, "
        "ghost-noted pocket; every voice draws on the same shared patterns.",
    )

    # every chord root snaps to the octave nearest this, around D3
    register_centre: ClassVar[float] = 146

    # per-note level, and the timing/level spread (s, fraction of level) that
    # `strum` and `feel` of 1.0 give
    NOTE_LEVEL: ClassVar[float] = 0.19
    # the voice count `NOTE_LEVEL` is balanced for; a voicing with more or
    # fewer notes scales each one so the stab's loudness stays the same
    REFERENCE_VOICES: ClassVar[int] = 4
    # the scale a voicing's degrees are read through: the stab's own quality,
    # independent of the rack's key, so a rack that sets no `scale` still gets
    # minor chords on every root
    voicing_scale: ClassVar[Scale] = Scales.MINOR
    STRUM_SPAN: ClassVar[float] = 0.04
    HUMAN_TIMING: ClassVar[float] = 0.025
    HUMAN_LEVEL: ClassVar[float] = 0.5

    # envelope duration (s), reverb wet balance, chorus on/off - overridden
    # per style
    duration: ClassVar[float]
    wet: ClassVar[float]
    chorus: ClassVar[bool] = False

    # the graph, assigned by build(); finish() retains every one of them
    envelope_table: CosTable
    note_delays: list[Delay]
    note_envs: list[TrigEnv]
    oscillator_table: PyoTableObject
    voices: list[Osc]
    source: PyoObject
    filter_voice: Biquad
    # only assigned by styles with `chorus` on
    chorus_voice: Chorus
    reverb: Freeverb

    # the voicing's notes as semitones above the chord root, and the level of
    # each one, both fixed at build time
    intervals: tuple[int, ...]
    note_level: float
    # this bar's chord source, frozen at build time - fed to `next_step`,
    # which build() can no longer close over now that it's a real method
    harmony: Harmony
    # the human-feel jitter's own source, so it never touches the global one
    _feel: random.Random
    # the server's rate, so a delay can be whole samples (see `whole_samples`)
    _sample_rate: float

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

    voicing = Param(
        0,
        0,
        1,
        Chords.SEVENTH_CHORD,
        "Voicing",
        "Picks the chord shape, from a bare power chord through triads and sevenths to wide, "
        "cinematic clusters; more notes sound fuller.",
        rebuild=True,
        catalog=Chords,
    )

    strum = Param(
        0,
        1,
        0.05,
        0,
        "Strum",
        "Spreads the chord's notes in time, low to high, like a hand rolling across strings; zero "
        "plays them as one block.",
    )

    feel = Param(
        0,
        1,
        0.05,
        0,
        "Human feel",
        "Loosens each stab: notes land a touch early or late and at slightly different strengths, "
        "so repeats stop sounding machine-exact.",
    )

    rate = rate_param(
        base_division,
        "Halves or doubles the chord-stab pattern speed for each step away from its 16th-note grid.",
    )

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony
        self.intervals = self.harmony.voice(
            Chords.by_index(int(self.voicing)), scale=self.voicing_scale
        )
        self.note_level = self.NOTE_LEVEL * self.REFERENCE_VOICES / len(self.intervals)

        self.oscillator_table = self.table()
        self.envelope_table = CosTable([(0, 0), (200, 1), (2500, 0.55), (8191, 0)])
        self._feel = random.Random()
        self._sample_rate = self.trigger.getServer().getSamplingRate()
        # one delayed trigger and envelope per note, so a strum can offset
        # each note's attack; at zero delay they all strike together
        self.note_delays = [
            Delay(self.trigger, delay=0, maxdelay=0.3) for _ in self.intervals
        ]
        self.note_envs = [
            TrigEnv(
                note_delay,
                self.envelope_table,
                dur=self.duration,
                mul=self.note_level,
            )
            for note_delay in self.note_delays
        ]
        self.retain(*self.note_delays, *self.note_envs)
        self.voices = [
            Osc(
                self.oscillator_table,
                freq=Note.transpose(
                    self.harmony.chord_freq(
                        self.register_centre, context.clock.bar_index
                    ),
                    12 * self.octave + interval,
                ),
                mul=note_env,
            )
            for interval, note_env in zip(self.intervals, self.note_envs, strict=True)
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

        self.schedule_pattern(context)
        return self.finish(self.add_gate(self.reverb, context))

    def whole_samples(self, seconds: float) -> float:
        """`seconds` rounded to a whole number of samples. `Delay` interpolates
        a fractional delay, which splits the trigger's one-sample pulse into
        two partial values, and `TrigEnv` only fires on a full 1.0: a delay
        off the sample grid would silence the note."""
        return round(seconds * self._sample_rate) / self._sample_rate

    def next_step(self) -> None:
        if self._step().hit:
            chord_root = Note.transpose(
                self.harmony.chord_freq(self.register_centre, self._clock.bar_index),
                12 * self.octave,
            )
            for index, (oscillator, interval) in enumerate(
                zip(self.voices, self.intervals, strict=True)
            ):
                oscillator.freq = Note.transpose(chord_root, interval)
                self.note_delays[index].delay = self.whole_samples(
                    index * self.strum * self.STRUM_SPAN
                    + self._feel.random() * self.feel * self.HUMAN_TIMING
                )
                self.note_envs[index].mul = self.note_level * (
                    1 - self._feel.random() * self.feel * self.HUMAN_LEVEL
                )
            self.trigger.play()


class StabVelvet(Stab):
    """Warm, rounded minor-seventh chord stabs."""

    title = "Chord Stab - Velvet"
    duration, wet = 0.34, 0.42

    def table(self) -> PyoTableObject:
        return HarmTable([1, 0.25, 0.12])


class StabOrgan(Stab):
    """Sustained, organ-like harmonic bed."""

    title = "Chord Stab - Organ"
    duration, wet = 0.22, 0.2

    def table(self) -> PyoTableObject:
        return HarmTable([1, 0.7, 0.4, 0.2])


class StabShimmer(Stab):
    """Bright, shimmering chord stabs with more edge."""

    title = "Chord Stab - Shimmer"
    duration, wet, chorus = 0.42, 0.58, True

    def table(self) -> PyoTableObject:
        return SawTable(order=12)
