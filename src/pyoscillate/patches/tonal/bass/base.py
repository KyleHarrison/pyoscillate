"""Bass-archetype name for the shared gated-voice base.

Every voice in this family strikes one note per clock step against a fixed
pattern of scale degrees, either on a live `root_freq` or re-rooted on the
rack's current chord each bar - see `note_root` for that shared policy.
That's the shape `GatedVoice` (`pyoscillate.patches.common`) doesn't already
cover - `drums.base.DrumVoice` is that base's name for the drums family,
this is its name for the bass family.

`build_voice` additionally covers the shared Osc+HarmTable+MoogLP graph the
groove and techno voices build from a `BassProfile` (a fixed or LFO-swept
low-pass driven by a per-step semitone/accent pattern). A voice with a
genuinely different graph (`fm`, `funk`) still subclasses `Bass` for
`note_root`/`schedule`/`finish`, but builds its own oscillator and filter
chain directly in its own `build()` - see `patches/CLAUDE.md`'s design
rule 1 on when a subclass needs different behavior, not just different
profile data.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pyo.lib.filters import MoogLP
from pyo.lib.generators import LFO
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import GatedVoice
from pyoscillate.patches.params import Param
from pyoscillate.tempo import Tempo

__all__ = ["Bass", "BassProfile"]

BASE_DIVISION = NoteDivision.SIXTEENTH


@dataclass(frozen=True)
class BassProfile:
    """Musical and perceptual policy for one bass voice.

    `gates` marks which steps actually strike a note; a `False` step is a
    rest - `next_step` skips both the retune and the trigger, so the
    previous note's envelope tail (and the silence after it) is what's
    heard, rather than every step restriking the pattern's pitch. Leaving
    it `None` gates every step, matching every profile before this field
    existed.
    """

    pattern: tuple[int, ...]
    accents: tuple[float, ...]
    envelope_decay: float
    resonance: float
    harmonics: tuple[float, ...] = (1.0, 0.32, 0.18, 0.1)
    gates: tuple[bool, ...] | None = None


class Bass(GatedVoice):
    """Base for a gated, monophonic bassline voice: one note is struck per
    clock step. See `note_root` for the shared root-pitch policy every
    concrete voice reads its note frequency from, and `build_voice` for the
    shared graph the groove and techno voices are built from.
    """

    # shared "Register" control for the harmony-following voices (`note_root`
    # re-roots on the current chord in the octave nearest its anchor); a
    # style that also wants it inherits this unmodified, one whose wording
    # should differ only redeclares `help_text`, e.g.
    # `octave = Bass.octave.replace(help_text="...")`
    octave = Param(
        0,
        1,
        1,
        0,
        "Register",
        "Lifts the bassline up an octave; low sits deep and heavy under the kick, high brings it "
        "closer to the chords. The notes always follow the rack's key and chord changes.",
    )

    # the graph `build_voice` assigns; finish() retains every one of them.
    # `cutoff_lfo` is only built when `build_voice` is given a `filter_base`.
    envelope_table: CosTable
    envelope: TrigEnv
    oscillator_table: HarmTable
    oscillator: Osc
    cutoff_lfo: LFO | None
    filtered: MoogLP

    def note_root(
        self, root_freq: float, clock: Clock, *, harmony: Harmony | None = None
    ) -> Callable[[], float]:
        """Zero-arg callable giving this voice's current root pitch (Hz) at
        trigger time.

        Without `harmony` the line sits on a fixed `root_freq`, read live off
        `self.root_freq` - a concrete voice using this branch declares that
        `Param` itself (only it needs a Register-in-Hz control). With
        `harmony`, every note is re-rooted on the current bar's chord in the
        octave nearest `root_freq`, tracked live off `self.octave` above -
        re-rooting on a live `root_freq` control could drag a chord-following
        line out of key.
        """
        if harmony is None:
            return lambda: self.root_freq
        return lambda: harmony.chord_freq(root_freq, clock.bar_index) * 2 ** self.octave

    def build_voice(
        self,
        tempo: Tempo,
        clock: Clock,
        profile: BassProfile,
        root_freq: float,
        cutoff: float,
        rate: float = 0,
        *,
        filter_base: float | None = None,
        filter_range: float = 0,
        filter_res: float | None = None,
        harmony: Harmony | None = None,
    ) -> Patch:
        """Build a triggered pitch voice from a musical `profile`, wire its
        scheduling, and return `self`, finished. Every parameter this graph
        exposes (`cutoff`, `filter_base`, `filter_range`, `filter_res`,
        `root_freq`/`octave`) is a `@Param` on the calling concrete class,
        whose control writes straight onto the nodes assigned here.

        A fixed `cutoff` gives a compact, controlled bass. Supplying
        `filter_base` and `filter_range` adds a bar-long continuous sweep,
        which is useful for a more animated techno voice. See `note_root`
        for the `harmony` vs. fixed `root_freq` choice.
        """
        if len(profile.pattern) != len(profile.accents):
            raise ValueError("Bass pattern and accent pattern must have equal lengths")
        if profile.gates is not None and len(profile.gates) != len(profile.pattern):
            raise ValueError("Bass gates must have the same length as the pattern")

        self.envelope_table = CosTable([(0, 0), (80, 1), (2100, 0.5), (8191, 0)])
        self.envelope = TrigEnv(
            self.trigger, table=self.envelope_table, dur=tempo.sixteenth * profile.envelope_decay
        )
        self.oscillator_table = HarmTable(list(profile.harmonics))
        self.oscillator = Osc(self.oscillator_table, freq=root_freq, mul=self.envelope)

        self.cutoff_lfo = None
        if filter_base is None:
            cutoff_source: Any = cutoff
        else:
            self.cutoff_lfo = LFO(freq=1 / tempo.bar, type=0, mul=filter_range, add=filter_base)
            cutoff_source = self.cutoff_lfo

        self.filtered = MoogLP(
            self.oscillator,
            freq=cutoff_source,
            res=profile.resonance if filter_res is None else filter_res,
        )

        current_root = self.note_root(root_freq, clock, harmony=harmony)

        def next_step() -> None:
            # derived from the shared clock's own tick, not a local counter
            # that starts at 0 whenever this patch is built or restarted -
            # see `Clock.tick`'s docstring
            step = (clock.tick // self._division.steps) % len(profile.pattern)
            if profile.gates is None or profile.gates[step]:
                self.oscillator.freq = current_root() * 2 ** (profile.pattern[step] / 12)
                self.envelope.mul = profile.accents[step]
                self.trigger.play()

        self.schedule(BASE_DIVISION, rate, clock, next_step)
        return self.finish(self.filtered)
