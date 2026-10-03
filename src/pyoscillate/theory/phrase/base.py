"""Phrases: the step patterns every gated patch plays, written once here so
any patch can select them."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pyoscillate.clock import NoteDivision
from pyoscillate.theory.catalog import CatalogItem


class PhraseMode(Enum):
    """What a `Step`'s `offset` means, and so how a patch resolves a pitch."""

    # no pitch: the phrase only says when to hit and how hard (a drum rhythm)
    NONE = "none"
    # semitones above the current chord root
    SEMITONES = "semitones"
    # an index into the current chord's triad (0 root, 1 third, 2 fifth)
    CHORD_TONE = "chord_tone"
    # an index into a pool of notes the patch supplies (an arpeggio's chord,
    # a scale); it wraps, so one order serves a triad or a whole scale
    POOL_INDEX = "pool_index"
    # a chord root, in semitones above the key, held from its step: the steps
    # are bars (a chord progression), not notes
    CHORD_ROOT = "chord_root"


class PhraseRole(Enum):
    """The job a phrase does, so a patch offers only the phrases that suit it
    (a kick has no use for a hat shuffle or a bass line)."""

    KICK = "kick"
    SNARE = "snare"
    HAT = "hat"
    CYMBAL = "cymbal"
    PERC = "perc"
    BASS = "bass"
    LEAD = "lead"
    # a short chord-tone figure (a pluck), as opposed to a longer lead line
    HOOK = "hook"
    BELL = "bell"
    FILL = "fill"
    # a chord struck on the steps (keys, a stab, strings)
    CHORD_HIT = "chord_hit"
    ARP = "arp"
    DRONE = "drone"
    # chord changes, one root per bar or run of bars, that a pitched patch
    # follows
    PROGRESSION = "progression"


@dataclass(frozen=True)
class Step:
    """One sounding step of a `Phrase`; a step with no `Step` is a rest."""

    # the step number within the phrase's cycle
    at: int
    # what this means depends on the phrase's `PhraseMode`
    offset: int = 0
    # the level (a drum's velocity); accents shape the timbre where a voice
    # maps level to brightness
    accent: float = 1.0
    # how many steps the note is held
    length: float = 1.0
    # for a hat: rings open rather than closing
    open: bool = False

    @staticmethod
    def position(step: Step) -> int:
        """`step`'s place in its cycle, for ordering."""
        return step.at


@dataclass(frozen=True, eq=False, kw_only=True)
class Phrase(CatalogItem):
    """A step pattern: `steps` sound, every other step in the `cycle` rests.

    `division` is the grid one step lasts and `cycle` the number of steps one
    pass spans. A patch holds the chosen phrase in a `Param` (see
    `choice_param`) and reads it through `values`, `accents`, `lengths` and
    `open_steps`.
    """

    division: NoteDivision
    cycle: int
    steps: tuple[Step, ...]
    # every job this phrase suits; a patch lists the roles it accepts
    roles: tuple[PhraseRole, ...]
    mode: PhraseMode = PhraseMode.NONE

    @property
    def values(self) -> dict[int, float]:
        """Step -> what a patch's step callback reads: the accent for a
        pitchless phrase, otherwise the offset."""
        if self.mode is PhraseMode.NONE:
            return self.accents
        return {step.at: int(step.offset) for step in self.steps}

    @property
    def accents(self) -> dict[int, float]:
        """Step -> level."""
        return {step.at: step.accent for step in self.steps}

    @property
    def lengths(self) -> dict[int, float]:
        """Step -> how many steps the note is held."""
        return {step.at: step.length for step in self.steps}

    @property
    def open_steps(self) -> frozenset[int]:
        """The steps a hat plays open rather than closed."""
        return frozenset(step.at for step in self.steps if step.open)

    @property
    def offsets(self) -> tuple[int, ...]:
        """Each step's offset in step order, for a patch that walks the
        phrase at its own pace instead of the clock's."""
        return tuple(int(step.offset) for step in sorted(self.steps, key=Step.position))

    def resolve(self, pool: tuple[int, ...]) -> dict[int, int]:
        """A `POOL_INDEX` phrase's pitch at each step, drawn from `pool`:
        step -> `pool[offset % len(pool)]`."""
        return {step.at: pool[step.offset % len(pool)] for step in self.steps}

    def chord_root(self, bar: int) -> int:
        """A `CHORD_ROOT` phrase's chord root sounding in `bar`, in semitones
        above the key: the latest step at or before `bar`'s place in the
        cycle holds until the next one."""
        if self.mode is not PhraseMode.CHORD_ROOT:
            raise ValueError(f"{self.id} is not a chord progression")
        position = bar % self.cycle
        held = [step for step in self.steps if step.at <= position]
        return max(held, key=Step.position).offset
