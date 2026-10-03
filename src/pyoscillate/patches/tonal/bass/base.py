"""Bass-archetype name for the shared gated-voice base.

Every voice in this family strikes one note per clock step against a fixed
pattern of scale degrees, either on a live `root_freq` or re-rooted on the
rack's current chord each bar - see `current_root` for that shared policy.
That's the shape `GatedVoice` (`pyoscillate.patches.common`) doesn't already
cover - `drums.base.DrumVoice` is that base's name for the drums family,
this is its name for the bass family.

`build` additionally covers the shared Osc+HarmTable+MoogLP graph the
groove, hover and techno voices build from a `BassProfile` (a fixed or
LFO-swept low-pass driven by a per-step semitone/accent pattern). A voice
with a genuinely different graph (`fm`, `funk`) still subclasses `Bass` for
`chord_root`/`schedule`/`finish`, but builds its own oscillator and filter
chain directly in its own `build()` - see `patches/AGENTS.md`'s design
rule 1 on when a subclass needs different behavior, not just different
profile data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.filters import MoogLP
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Gate, GatedVoice, PitchBend
from pyoscillate.patches.params import Param
from pyoscillate.tempo import Tempo
from pyoscillate.theory import notes

__all__ = ["AccentBass", "Bass", "BassProfile"]

BASE_DIVISION = NoteDivision.SIXTEENTH


@dataclass(frozen=True)
class BassProfile:
    """Musical and perceptual policy for one bass voice.

    `gates` marks which steps actually strike a note; a `False` step is a
    rest - `next_step` skips both the retune and the trigger, so the
    previous note's envelope tail (and the silence after it) is what's
    heard, rather than every step restriking the pattern's pitch. A profile
    that strikes every step passes an all-`True` tuple.
    """

    pattern: tuple[int, ...]
    accents: tuple[float, ...]
    gates: tuple[bool, ...]
    envelope_decay: float
    resonance: float
    harmonics: tuple[float, ...] = (1.0, 0.32, 0.18, 0.1)


class Bass(PitchBend, Gate, GatedVoice):
    """Base for a gated, monophonic bassline voice: one note is struck per
    clock step. See `current_root` for the root-pitch policy every concrete
    voice supplies, and `build` for the shared graph the groove, hover and
    techno voices are built from.
    """

    # the centre a chord-following voice's `chord_root` snaps every chord
    # root to the octave nearest
    register_centre: ClassVar[float] = notes.A1
    # the style's musical policy; supplied by each style subclass
    profile: ClassVar[BassProfile]

    # shared "Register" control for the harmony-following voices (`chord_root`
    # re-roots on the current chord in the octave nearest `register_centre`);
    # a style that also wants it inherits this unmodified, one whose wording
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

    @Param(
        0,
        0.25,
        0.01,
        0,
        "Glide",
        "Slides each note into the next over this many seconds; none is stepped and exact, long "
        "is a smeared, sliding line.",
        sweep=True,
    )
    def glide(self, value: float) -> None:
        self.pitch.time = value

    # the graph `build` assigns; finish() retains every one of them.
    pitch: SigTo
    bent_pitch: PyoObject
    envelope_table: CosTable
    envelope: TrigEnv
    oscillator_table: HarmTable
    oscillator: Osc
    filtered: MoogLP

    # the fixed-pitch voices' Register `Param` and the fixed-cutoff voices'
    # Brightness `Param`, declared by the style that has them
    root_freq: float
    cutoff: float
    # the clocked `rate` `Param` every style declares (with its own help text)
    rate: float

    # the context and profile `next_step`/`chord_root` read at trigger time,
    # frozen at build time (`_profile` may be swapped live by `on_evolve`)
    _context: BuildContext
    _profile: BassProfile
    _tempo: Tempo

    def current_root(self) -> float:
        """This voice's current root pitch (Hz) at trigger time. A fixed-pitch
        style returns its live `root_freq`; a chord-following style returns
        `chord_root()`. Overridden per style."""
        raise NotImplementedError

    def chord_root(self) -> float:
        """The current bar's chord root in the octave nearest
        `register_centre`, lifted by the live `octave` - re-rooting on a live
        `root_freq` control could drag a chord-following line out of key."""
        context = self._context
        return context.harmony.chord_freq(
            self.register_centre, context.clock.bar_index
        ) * (2**self.octave)

    def cutoff_source(self) -> Any:
        """Hook: what drives the low-pass cutoff. The default is the fixed
        `cutoff` value (its `Param` control retunes `filtered` live); a style
        overrides this to sweep it, assigning any node it builds onto `self`."""
        return self.cutoff

    def build(self, context: BuildContext) -> Patch:
        """Build a triggered pitch voice from `profile`, wire its scheduling,
        and return `self`, finished. Every parameter this graph exposes is a
        `@Param` on the calling concrete class, whose control writes straight
        onto the nodes assigned here, so the nodes are built neutral."""
        self._reset()
        profile = self.profile
        if len(profile.pattern) != len(profile.accents):
            raise ValueError("Bass pattern and accent pattern must have equal lengths")
        if len(profile.gates) != len(profile.pattern):
            raise ValueError("Bass gates must have the same length as the pattern")
        self._context = context
        self._profile = profile
        self._tempo = context.tempo

        self.envelope_table = CosTable([(0, 0), (80, 1), (2100, 0.5), (8191, 0)])
        self.envelope = TrigEnv(
            self.trigger,
            table=self.envelope_table,
            dur=context.tempo.sixteenth * profile.envelope_decay,
        )
        self.sync(
            context.tempo,
            lambda t: setattr(
                self.envelope, "dur", t.sixteenth * self._profile.envelope_decay
            ),
        )
        self.oscillator_table = HarmTable(list(profile.harmonics))
        freq = self.pitch_signal(self.current_root())
        self.oscillator = Osc(self.oscillator_table, freq=freq, mul=self.envelope)
        self.filtered = MoogLP(
            self.oscillator,
            freq=self.cutoff_source(),
            res=profile.resonance,
        )

        self.schedule(BASE_DIVISION, self.rate, context.clock)
        return self.finish(self.add_gate(self.voice_output(), context))

    def pitch_signal(self, initial: float) -> PyoObject:
        """The note frequency every voice in this family plays from. Setting
        `self.pitch.value` per step glides at the live `glide` time, and each
        struck note is scooped by the live `bend` (`finish()` applies both
        controls, so the neutral values here never sound)."""
        self.pitch = SigTo(value=initial, time=self.glide, init=initial)
        self.bent_pitch = self.pitch * self.add_bend(self.trigger)
        return self.bent_pitch

    def voice_output(self) -> PyoObject:
        """Hook: the final output node after `self.filtered`. The default is
        a no-op; a style overrides this to add its own post-processing
        (e.g. a reverb tail), assigning any node it builds onto `self` too -
        same pattern as `Kick.voice_output`/`Groove.voice_output`."""
        return self.filtered

    def next_step(self) -> None:
        # derived from the shared clock's own tick, not a local counter
        # that starts at 0 whenever this patch is built or restarted -
        # see `Clock.tick`'s docstring
        profile = self._profile
        step = (self._clock.tick // self._division.steps) % len(profile.pattern)
        if profile.gates[step]:
            self.pitch.value = notes.transpose(
                self.current_root(), profile.pattern[step]
            )
            self.apply_accent(profile.accents[step])
            self.trigger.play()

    def apply_accent(self, accent: float) -> None:
        """Hook: how a struck note's profile accent (0-1) shapes it. The
        default is level only; `AccentBass` also couples decay and resonance."""
        self.envelope.mul = accent


class AccentBass(Bass):
    """A profile-driven bass whose `accent` amount couples the pattern's
    per-step accents to timbre, as one macro (patches/AGENTS.md, "Macro
    parameters"). At 0 an accent is only louder. As it rises, accented notes
    also get louder still relative to the ghosts, shorter and snappier, and
    more resonant, so they speak instead of just sitting higher in level."""

    ACCENT_SHORTEN: ClassVar[float] = 0.45
    ACCENT_SQUELCH: ClassVar[float] = 0.3
    ACCENT_CONTRAST: ClassVar[float] = 2.0

    accent = Param(
        0,
        1,
        0.05,
        0,
        "Accent",
        "Makes the strong notes of the pattern speak: louder against the soft ones, shorter and "
        "snappier, with more squelch in the filter. At zero they differ only in level.",
    )

    def apply_accent(self, accent: float) -> None:
        amount = self.accent
        profile = self._profile
        self.envelope.mul = accent ** (1 + amount * self.ACCENT_CONTRAST)
        self.envelope.dur = (
            self._tempo.sixteenth
            * profile.envelope_decay
            * (1 - amount * accent * self.ACCENT_SHORTEN)
        )
        self.filtered.res = min(
            1.0, profile.resonance + amount * accent * self.ACCENT_SQUELCH
        )
