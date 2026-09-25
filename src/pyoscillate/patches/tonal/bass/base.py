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
from pyoscillate.tempo import Tempo

__all__ = ["Bass", "BassProfile"]

BASE_DIVISION = NoteDivision.SIXTEENTH


@dataclass(frozen=True)
class BassProfile:
    """Musical and perceptual policy for one bass voice."""

    pattern: tuple[int, ...]
    accents: tuple[float, ...]
    envelope_decay: float
    resonance: float
    harmonics: tuple[float, ...] = (1.0, 0.32, 0.18, 0.1)


class Bass(GatedVoice):
    """Base for a gated, monophonic bassline voice: one note is struck per
    clock step. See `note_root` for the shared root-pitch policy every
    concrete voice reads its note frequency from, and `build_voice` for the
    shared graph the groove and techno voices are built from.
    """

    def note_root(
        self,
        root_freq: float,
        clock: Clock,
        *,
        harmony: Harmony | None = None,
        octave: float = 0,
    ) -> Callable[[], float]:
        """Zero-arg callable giving this voice's current root pitch (Hz) at
        trigger time, and registers the matching live control.

        Without `harmony` the line sits on a fixed `root_freq`, exposed as a
        live `root_freq` control. With it, every note is re-rooted on the
        current bar's chord in the octave nearest `root_freq`, and the live
        control is `octave` instead - re-rooting on a live `root_freq`
        control could drag a chord-following line out of key.
        """
        state = {"root": root_freq, "octave": octave}
        if harmony is None:
            self.controls["root_freq"] = lambda value: state.update(root=value)
            return lambda: state["root"]
        self.controls["octave"] = lambda value: state.update(octave=value)
        return lambda: harmony.chord_freq(root_freq, clock.bar_index) * 2 ** state["octave"]

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
        octave: float = 0,
    ) -> Patch:
        """Build a triggered pitch voice from a musical `profile`, wire its
        scheduling and live controls, and return `self`, finished.

        A fixed `cutoff` gives a compact, controlled bass. Supplying
        `filter_base` and `filter_range` adds a bar-long continuous sweep,
        which is useful for a more animated techno voice. See `note_root`
        for the `harmony`/`octave` vs. fixed `root_freq` choice.
        """
        if len(profile.pattern) != len(profile.accents):
            raise ValueError("Bass pattern and accent pattern must have equal lengths")

        envelope_table = CosTable([(0, 0), (80, 1), (2100, 0.5), (8191, 0)])
        envelope = TrigEnv(
            self.trigger, table=envelope_table, dur=tempo.sixteenth * profile.envelope_decay
        )
        oscillator_table = HarmTable(list(profile.harmonics))
        oscillator = Osc(oscillator_table, freq=root_freq, mul=envelope)
        self.retain(envelope_table, envelope, oscillator_table, oscillator)

        cutoff_lfo: Any | None = None
        if filter_base is None:
            cutoff_source: Any = cutoff
        else:
            cutoff_lfo = LFO(freq=1 / tempo.bar, type=0, mul=filter_range, add=filter_base)
            cutoff_source = cutoff_lfo
            self.retain(cutoff_lfo)

        voice = MoogLP(
            oscillator,
            freq=cutoff_source,
            res=profile.resonance if filter_res is None else filter_res,
        )

        current_root = self.note_root(root_freq, clock, harmony=harmony, octave=octave)
        state = {"step": 0}

        def next_step() -> None:
            step = state["step"] % len(profile.pattern)
            oscillator.freq = current_root() * 2 ** (profile.pattern[step] / 12)
            envelope.mul = profile.accents[step]
            self.trigger.play()
            state["step"] += 1

        controls: dict[str, Callable[[Any], None]] = {
            "cutoff": lambda value: setattr(voice, "freq", value)
        }
        if filter_base is not None and cutoff_lfo is not None:
            controls.update(
                {
                    "filter_base": lambda value: setattr(cutoff_lfo, "add", value),
                    "filter_range": lambda value: setattr(cutoff_lfo, "mul", value),
                }
            )
        if filter_res is not None:
            controls["filter_res"] = lambda value: setattr(voice, "res", value)

        self.schedule(BASE_DIVISION, rate, clock, next_step)
        return self.finish(voice, controls)
