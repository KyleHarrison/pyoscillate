# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.keys.organ
"""Held keyboards built from ranks: the base of the organ and the accordion.

A key held down on these instruments does not die away, it sounds for as long
as it is down, so they are `Held` voices (see `common.py`): the note starts on
the phrase's hit, stays for the rest of its step plus Legato, and lets go over
Release. What the instrument adds is a stack of *ranks*. A rank is one
oscillator per sounding note at a fixed ratio to the note's pitch: an organ's
drawbars are sine ranks on the harmonic series, an accordion's registers are
reed ranks an octave apart or a few cents out of tune. Each rank has its own
level, so the instrument's tone is the balance of its ranks.

A style names its ranks (`ranks`, ratios to the note), builds one rank's
oscillator in `rank_tone()`, and declares a `Param` for each rank it wants a
control for, each calling `apply_ranks()`.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix, Sig
from pyo.lib.controls import SigTo

from pyoscillate.patches.common import Held, Phrased
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.phrase import PhraseRole, Rhythms


class RankedKeys(Held):
    """A held keyboard whose tone is a stack of ranks. Plays the rack's chord
    on a chord rhythm and a line of its chord tones on a figure, so one
    instrument comps or leads."""

    chord_shape = Chords.TRIAD
    # each rank's frequency ratio to the note: 1 is the note, 2 an octave up
    ranks: ClassVar[tuple[float, ...]] = (1.0,)
    # the loudest the ranks can add up to before the trim: a full set of ranks
    # is louder than one, but by the square root of the count, not the count
    gain: ClassVar[float] = 0.05
    # seconds a rank takes to follow a new level, so a drawbar or stop that is
    # moved or swept does not click
    rank_glide: ClassVar[float] = 0.03

    rank_ratios: list[Sig]
    rank_levels: list[SigTo]
    rank_pitches: list[PyoObject]
    rank_gains: list[PyoObject]
    rank_tones: list[PyoObject]
    rank_bank: Mix

    phrase_roles = (PhraseRole.CHORD_HIT, PhraseRole.HOOK, PhraseRole.LEAD)
    phrase = Phrased.phrase.replace(
        default=Rhythms.BAR_PULSE,
        help_text="Picks when in the bar the keys are pressed: a chord held a bar, a backbeat or a swung pulse, "
        "or a figure of chord tones; every voice draws on the same shared patterns.",
    )

    def rank_values(self) -> list[float]:
        """Each rank's level as the style's `Param`s currently have it (0 to
        1), in the order of `ranks`."""
        raise NotImplementedError

    def rank_tone(self, freq: PyoObject, level: PyoObject) -> PyoObject:
        """One rank's oscillators: a stream per voice at `freq`, silenced and
        scaled by `level`. A style builds the oscillator; the base sums them."""
        raise NotImplementedError

    def apply_ranks(self) -> None:
        """Push every rank's level to its oscillator. The ranks are trimmed by
        the square root of their total, so a full set is louder than a single
        rank without being as many times louder as it has ranks."""
        values = self.rank_values()
        trim = self.gain / max(sum(values), 1.0) ** 0.5
        for level, value in zip(self.rank_levels, values, strict=True):
            level.value = value * trim

    def make_tone(self) -> PyoObject:
        self.rank_ratios = [Sig(ratio) for ratio in self.ranks]
        self.rank_levels = [SigTo(value=0, time=self.rank_glide) for _ in self.ranks]
        self.rank_pitches = [self.held_pitch * ratio for ratio in self.rank_ratios]
        self.rank_gains = [self.voice_gain * level for level in self.rank_levels]
        self.rank_tones = [
            self.rank_tone(freq, level)
            for freq, level in zip(self.rank_pitches, self.rank_gains, strict=True)
        ]
        self.retain(
            *self.rank_ratios,
            *self.rank_levels,
            *self.rank_pitches,
            *self.rank_gains,
            *self.rank_tones,
        )
        self.rank_bank = Mix(self.rank_tones, voices=1)
        return self.rank_bank
