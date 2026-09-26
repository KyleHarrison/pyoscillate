# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.strings.strings
"""Supersaw string ensemble: a sustained, harmony-following chord pad with
no struck attack.

Four `SuperSaw` voices (each already seven detuned sawtooths internally -
pyo's JP-8000 "Supersaw" emulation) sit on the chord's root, fifth, octave,
and a fourth voice on a major 9th above the root, whose level is a separate
Colour blend rather than baked into the default chord - see `CLAUDE.md`'s
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
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import GatedVoice
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

# chord-tone intervals (semitones above the bar's chord root) that stay
# consonant against any chord quality: root, fifth, octave. The major-9th
# colour voice is kept separate (see module docstring / CLAUDE.md).
CHORD_TONES: tuple[int, ...] = (0, 7, 12)
COLOUR_TONE = 14
# low-pass Q just under Butterworth, so brightness never rings or whistles
FILTER_Q = 0.7
# balances the four summed SuperSaw voices (three chord tones + colour)
# under the output ceiling at full Colour
GAIN = 0.16


class Strings(GatedVoice):
    """Supersaw ensemble pad, re-opening once per bar on the rack's chord.
    See the module docstring and `CLAUDE.md` for the synthesis approach."""

    title = "Strings"
    summary = "Supersaw string ensemble sustaining the rack's chord, with a blendable 9th colour tone."
    volume_default = 0.5
    base_division: ClassVar[NoteDivision] = NoteDivision.WHOLE
    needs_harmony: ClassVar[bool] = True

    # the graph, assigned by build(); finish() retains every one of them
    chord_saws: list[SuperSaw]
    colour_saw: SuperSaw
    mixed: Mix
    filtered: Biquad
    chorus: Chorus
    amp_env: Adsr
    voice_signal: PyoObject

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
        "Blends in a bright major-9th tone above the chord root; zero is a plain open fifth, full brings "
        "out a jazz-tinged upper colour.",
    )
    def colour(self, value: float) -> None:
        self.colour_saw.mul = GAIN * value

    rate = rate_param(
        base_division,
        "Speeds up how often the ensemble re-articulates for each step away from its default of once per "
        "bar; it can't go slower than once per bar.",
    )

    def build(self, tempo: Tempo, clock: Clock, harmony: Harmony | None = None) -> Patch:
        self._reset()

        def current_root() -> float:
            if harmony is None:
                return self.root_freq
            return harmony.chord_freq(self.root_freq, clock.bar_index)

        root = current_root()
        # neutral detune/mul here; the Spread and Colour controls (run by
        # finish() below) apply the live values, per patches/CLAUDE.md's
        # rule against repeating a parameter's mapping in build()
        self.chord_saws = [
            SuperSaw(freq=root * 2 ** (interval / 12), detune=0, bal=0.7, mul=GAIN)
            for interval in CHORD_TONES
        ]
        self.colour_saw = SuperSaw(freq=root * 2 ** (COLOUR_TONE / 12), detune=0, bal=0.7, mul=0)
        self.mixed = Mix([*self.chord_saws, self.colour_saw], voices=1)
        self.filtered = Biquad(self.mixed, freq=self.brightness, q=FILTER_Q, type=0)
        self.chorus = Chorus(self.filtered, depth=0, feedback=0.15, bal=0.5)

        self.amp_env = Adsr(
            attack=self.attack, decay=0.05, sustain=1.0, release=self.release, mul=1.0
        )
        self.voice_signal = self.chorus * self.amp_env

        def next_step() -> None:
            new_root = current_root()
            for saw, interval in zip(self.chord_saws, CHORD_TONES, strict=True):
                saw.freq = new_root * 2 ** (interval / 12)
            self.colour_saw.freq = new_root * 2 ** (COLOUR_TONE / 12)
            self.amp_env.play()

        self.schedule(self.base_division, self.rate, clock, next_step)
        return self.finish(self.voice_signal, resources=(*self.chord_saws,))
