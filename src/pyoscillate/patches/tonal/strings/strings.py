# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.strings.strings
"""Supersaw string ensemble: a sustained, harmony-following chord pad with
no struck attack.

Four `SuperSaw` voices (each already seven detuned sawtooths internally -
pyo's JP-8000 "Supersaw" emulation) sit on the chord's root, fifth, octave,
and a fourth voice on a major 9th above the root, whose level is a separate
Colour blend rather than baked into the default chord - see `AGENTS.md`'s
"Voicing against the rack harmony" for why root/fifth/octave is the safe
default. The mix goes through a low-pass for warmth, `Chorus` for ensemble
shimmer, and a plain `Adsr` (no struck transient) that re-opens once per bar
so the chord tracks `Harmony.chord_freq` without ever being retriggered on
the clocked grid the way a struck voice is.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.controls import Adsr
from pyo.lib.effects import Chorus
from pyo.lib.filters import Biquad
from pyo.lib.generators import SuperSaw

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Gate, GatedVoice
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.utility.notes import notes

# chord-tone intervals (semitones above the bar's chord root) that stay
# consonant against any chord quality: root, fifth, octave. The colour
# voice is kept separate (see module docstring / AGENTS.md).
CHORD_TONES: tuple[int, ...] = (0, 7, 12)
# low-pass Q just under Butterworth, so brightness never rings or whistles
FILTER_Q = 0.7
# balances the four summed SuperSaw voices (three chord tones + colour)
# under the output ceiling at full Colour
GAIN = 0.16


class Strings(Gate, GatedVoice):
    """Supersaw ensemble pad, re-opening once per bar on the rack's chord.
    See the module docstring and `AGENTS.md` for the synthesis approach."""

    title = "Strings"
    summary = "Supersaw string ensemble sustaining the rack's chord, with a blendable 9th colour tone."
    volume = Patch.volume.replace(default=0.5)
    base_division: ClassVar[NoteDivision] = NoteDivision.WHOLE

    # candidate intervals (semitones above the root) for the colour voice: a
    # major 9th (default) and a major 13th, an octave-and-a-6th up - both
    # stay consonant against the rack's Dm9-G13-Cmaj9-Am9 vamp the way the
    # 9th does. A rack-level `GroupController` rotates which one is blended
    # in via `on_evolve`, tens of bars apart - see `Keys.PROGRESSIONS` for
    # the same pattern.
    COLOUR_TONE_VARIANTS: ClassVar[tuple[int, ...]] = (14, 21)

    # the graph, assigned by build(); finish() retains every one of them
    chord_saws: list[SuperSaw]
    colour_saw: SuperSaw
    mixed: Mix
    filtered: Biquad
    chorus: Chorus
    amp_env: Adsr
    voice_signal: PyoObject

    # the rack's harmony, frozen at build time - fed to `next_step`, which
    # build() can no longer close over now that it's a real method
    harmony: Harmony

    # explicit per patches/AGENTS.md rule 5 (timing/state), not a `@Param`:
    # only `on_evolve` and `next_step`/`build` read/write it - which
    # `COLOUR_TONE_VARIANTS` entry the colour voice is currently on
    _colour_interval: int

    root_freq = Param(
        notes.A2,
        notes.A4,
        1,
        notes.A3,
        "Register",
        "Moves the ensemble up or down; low sits warm and covered under the melody, high moves it "
        "closer to the surface.",
        scale="note",
    )

    @Param(
        400,
        6000,
        50,
        2200,
        "Brightness",
        "How much top end the ensemble keeps; low is muffled and distant, high is airier and closer.",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.filtered.freq = value

    @Param(
        0.1,
        3.0,
        0.05,
        1.2,
        "Attack",
        "How gradually the chord swells in each bar; short is a soft entrance, long is barely perceptible.",
        sweep=True,
    )
    def attack(self, value: float) -> None:
        self.amp_env.setAttack(value)

    @Param(
        0.2,
        4.0,
        0.05,
        2.0,
        "Release",
        "How long the chord lingers once the bar turns over; short changes cleanly, long blurs into the "
        "next chord.",
        sweep=True,
    )
    def release(self, value: float) -> None:
        self.amp_env.setRelease(value)

    @Param(
        0.0,
        1.0,
        0.05,
        0.35,
        "Spread",
        "How far the ensemble's inner voices drift from the centre pitch; low is a tight, almost single "
        "string, high is a wide, shimmering section.",
        sweep=True,
    )
    def spread(self, value: float) -> None:
        for saw in (*self.chord_saws, self.colour_saw):
            saw.detune = value

    @Param(
        0.0,
        1.0,
        0.05,
        0.5,
        "Shimmer",
        "How strongly the ensemble chorus wobbles the sound; low stays still, high adds a lush, wavering "
        "chorus.",
        sweep=True,
    )
    def shimmer(self, value: float) -> None:
        self.chorus.depth = value
        self.chorus.feedback = 0.15 + 0.25 * value

    @Param(
        0.0,
        1.0,
        0.05,
        0.3,
        "Colour",
        "Blends in a bright upper tone above the chord root (a 9th or, after it evolves, a 13th); zero "
        "is a plain open fifth, full brings out a jazz-tinged upper colour.",
        sweep=True,
    )
    def colour(self, value: float) -> None:
        self.colour_saw.mul = GAIN * value

    rate = rate_param(
        base_division,
        "Speeds up how often the ensemble re-articulates for each step away from its default of once per "
        "bar; it can't go slower than once per bar.",
    )

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony
        self._colour_interval = self.COLOUR_TONE_VARIANTS[0]

        root = self.current_root(context.clock)
        # neutral detune/mul here; the Spread and Colour controls (run by
        # finish() below) apply the live values, per patches/AGENTS.md's
        # rule against repeating a parameter's mapping in build()
        self.chord_saws = [
            SuperSaw(freq=root * 2 ** (interval / 12), detune=0, bal=0.7, mul=GAIN)
            for interval in CHORD_TONES
        ]
        self.colour_saw = SuperSaw(
            freq=root * 2 ** (self._colour_interval / 12), detune=0, bal=0.7, mul=0
        )
        self.mixed = Mix([*self.chord_saws, self.colour_saw], voices=1)
        self.filtered = Biquad(self.mixed, freq=self.brightness, q=FILTER_Q, type=0)
        self.chorus = Chorus(self.filtered, depth=0, feedback=0.15, bal=0.5)

        self.amp_env = Adsr(
            attack=self.attack, decay=0.05, sustain=1.0, release=self.release, mul=1.0
        )
        self.voice_signal = self.chorus * self.amp_env

        self.schedule(self.base_division, self.rate, context.clock)
        return self.finish(
            self.add_gate(self.voice_signal, context), resources=(*self.chord_saws,)
        )

    def current_root(self, clock: Clock) -> float:
        return self.harmony.chord_freq(self.root_freq, clock.bar_index)

    def on_evolve(self, index: int) -> None:
        """Rotate which `COLOUR_TONE_VARIANTS` interval the colour voice is
        on; called rarely (tens of bars) by a rack-level `GroupController`,
        never by the clock directly - see `Keys.on_evolve`. Takes effect on
        the next `next_step()`, not immediately, so the colour tone never
        jumps mid-chord."""
        self._colour_interval = self.COLOUR_TONE_VARIANTS[
            index % len(self.COLOUR_TONE_VARIANTS)
        ]

    def next_step(self) -> None:
        new_root = self.current_root(self._clock)
        for saw, interval in zip(self.chord_saws, CHORD_TONES, strict=True):
            saw.freq = new_root * 2 ** (interval / 12)
        self.colour_saw.freq = new_root * 2 ** (self._colour_interval / 12)
        self.amp_env.play()
