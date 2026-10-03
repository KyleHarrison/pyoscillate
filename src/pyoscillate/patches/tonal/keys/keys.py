# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.keys.keys
"""FM electric piano: a struck tine over a round body, comping a progression.

Each note is two FM pairs on the same carrier, both read from break-point
envelopes (pyo example x10/01) whose reader frequency is 1/dur, so one set of
tables fits any Decay:

- the **body**: ratio 1, a low index that falls over the note. Bite raises
  it towards a reedy, Wurlitzer-like edge.
- the **tine**: ratio 14, an index that dies inside a tenth of a second.
  That short, bright ping on the front of the note is the hammer hitting
  the tine. Its index scales with velocity squared, so hard notes bark and
  soft ones stay round, as on the DX7's E.PIANO patches.

Both share one exponential amplitude envelope with no sustain. An optional
8th-note tremolo gives the suitcase-amp throb. Chords are close, rootless
voicings, comped in a Charleston rhythm (beat one, then the "and" of two).
Notes rotate over `SLOTS` chord slots, so a long Decay rings into the next
chord instead of being cut.

An optional slow, continuous Wobble - a sub-1 Hz sine multiplying every
voice's pitch by a tiny, ever-drifting ratio - models tape wow-and-flutter:
distinct from Tremolo, which throbs the *level* in a fixed 8th-note rhythm,
Wobble drifts the *pitch* at its own slow, unrhythmic rate. Each note's base
pitch is held in its own `Sig` (`freq_sigs`) instead of being written straight
onto `FM.carrier`, so the wobble ratio can multiply every currently-sounding
voice continuously between triggers, not just at the strike.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Sig
from pyo.lib.controls import SigTo
from pyo.lib.filters import ButHP
from pyo.lib.generators import FM, Sine
from pyo.lib.tables import LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import (
    RING_CURVE,
    Gate,
    GatedVoice,
    Step,
    decay_points,
)
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory import notes
from pyoscillate.theory.intervals import KeysProgression

# step on the 16th grid -> velocity: the Charleston rhythm
HITS = {0: 1.0, 6: 0.55}
# HITS' steps, in order - used to number each bar's hits (0, 1, ...) so the
# slot rotation below stays deterministic from the shared clock
HIT_STEPS = tuple(sorted(HITS))
BAR_STEPS = 16
NOTES = 4
SLOTS = 4


def _per_note(per_slot: list[float]) -> list[float]:
    """Spread one value per chord slot across that slot's note streams."""
    return [value for value in per_slot for _ in range(NOTES)]


class Keys(Gate, GatedVoice):
    """FM electric piano comping a `KeysProgression` vamp in the Charleston rhythm.
    See the module docstring for the sonic detail."""

    title = "Keys (FM electric piano)"
    summary = "Struck FM electric piano comping a close-voiced progression."
    volume = Patch.volume.replace(default=0.8)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH

    body_ratio: ClassVar[float] = 1
    tine_ratio: ClassVar[float] = 14
    # seconds the tine's ping (its index) takes to die away
    tine_time: ClassVar[float] = 0.08
    # seconds the tine pair's own level takes to die away, after the ping
    tine_ring: ClassVar[float] = 0.3
    # the tine pair's level against the body's: loud enough to ping, quiet
    # enough that the strike doesn't tower over the ring
    tine_level: ClassVar[float] = 0.5
    # the body's index falls this many times faster than the level, so the
    # chord mellows as it rings
    body_speed: ClassVar[float] = 2.0
    # soft notes keep this share of the body's Bite
    bite_floor: ClassVar[float] = 0.5
    # four notes of two FM pairs each, in phase on the same carriers at the
    # strike; the loudest chord in the slider ranges peaks at ~5 x gain x
    # volume, 0.16 at the default volume, under the output ceiling
    gain: ClassVar[float] = 0.04
    # under the lowest note (Register 110, four semitones down: 87 Hz)
    subsonic: ClassVar[float] = 20
    # tape wow-and-flutter LFO rate (Hz) - slow and unrhythmic, unlike the
    # tremolo's fixed 8th-note throb - and its widest fractional pitch swing
    # at full Wobble
    wobble_rate: ClassVar[float] = 0.18
    wobble_depth_max: ClassVar[float] = 0.015

    # the four-bar voicing sets comping the chosen `vamp` come from
    # `KeysProgression`: semitones above Register, one close rootless voicing
    # per bar. Set 0 is the home voicing; a `GroupController` (see
    # controller.py) rotates through the sets via `on_evolve`, so the
    # harmony never changes, only which inversion voices it. Keys never
    # reads the rack's harmony, so a rack must be given the same changes:
    # `Harmony(progression=KeysProgression.X.roots)`.

    # the graph, assigned by build(); finish() retains every one of them
    triggers: list[Trig]
    strikes: list[Trig]
    freqs: list[float]
    freq_sigs: list[Sig]
    velocities: list[float]
    _progression_index: int
    # the active vamp's voicing sets, fixed at build time
    _voicing_sets: tuple[tuple[tuple[int, ...], ...], ...]
    _step: Callable[[], Step]
    amp_table: LinTable
    body_table: LinTable
    tine_table: LinTable
    amp: TrigEnv
    body_index: TrigEnv
    tine_index: TrigEnv
    tine_amp: TrigEnv
    wobble_depth: SigTo
    wobble_lfo: Sine
    wobble_ratio: PyoObject
    wobbled_freqs: list[PyoObject]
    body: FM
    tine: FM
    chord_notes_signal: PyoObject
    mixed: PyoObject
    chord: ButHP
    depth: SigTo
    tremolo_lfo: Sine
    swing: PyoObject
    throb: PyoObject
    voice_signal: PyoObject

    vamp = Param(
        0,
        5,
        1,
        0,
        "Vamp",
        "Picks the four-bar chord changes the piano comps: 0 ii-V-I-vi, 1 I-vi-IV-V, 2 vi-IV-I-V, "
        "3 ii-V-I-IV, 4 I-iii-vi-ii, 5 iii-vi-ii-V. The rest of the rack has to play the same "
        "changes to stay in key.",
        rebuild=True,
    )

    # only read at trigger time (next_step()), so it needs no live control:
    # assigning it already keeps self.root_freq current
    root_freq = Param(
        notes.A2,
        notes.E4,
        1,
        notes.A3,
        "Register",
        "Moves the chords up or down; low is warm and dark under a vocal, high is bell-like and sits above the mix.",
        scale="note",
    )

    @Param(
        0,
        6,
        0.1,
        2.5,
        "Bark",
        "How much each strike pings: low is a soft, round touch, high a bright, glassy bark on hard notes that fades as the chord rings.",
        sweep=True,
    )
    def bark(self, value: float) -> None:
        self.apply_touch()

    @Param(
        0,
        3,
        0.1,
        0.8,
        "Bite",
        "The edge on the sustained tone: low is a pure, mellow Rhodes-like body, high a reedy, nasal Wurlitzer-like growl.",
        sweep=True,
    )
    def bite(self, value: float) -> None:
        self.apply_touch()

    @Param(
        0.5,
        4,
        0.1,
        1.8,
        "Decay",
        "How long each chord rings, in seconds, before it dies away; short is a tight stab, long lets the chords overlap.",
        sweep=True,
    )
    def decay(self, value: float) -> None:
        self.amp.dur = value
        self.body_index.dur = value

    @Param(
        0,
        1,
        0.05,
        0.3,
        "Tremolo",
        "How strongly the level throbs in 8th notes, like an electric piano through a tremolo amp; 0 holds it steady.",
        sweep=True,
    )
    def tremolo(self, value: float) -> None:
        self.depth.value = value / 2

    @Param(
        0,
        1,
        0.05,
        0.0,
        "Wobble",
        "Slow, unsteady pitch drift like tape wow-and-flutter - distinct from Tremolo, which throbs the "
        "level in a fixed rhythm; 0 keeps the pitch rock steady, higher adds a slow, wavering detune.",
        sweep=True,
    )
    def wobble(self, value: float) -> None:
        self.wobble_depth.value = value * self.wobble_depth_max

    rate = rate_param(
        base_division,
        "Halves or doubles the comping speed for each step away from its 16th-note grid.",
    )

    def apply_touch(self) -> None:
        """Rescale every slot's envelopes from its stored velocity."""
        self.amp.mul = _per_note([self.gain * velocity for velocity in self.velocities])
        self.tine_amp.mul = _per_note(
            [self.gain * self.tine_level * velocity for velocity in self.velocities]
        )
        self.body_index.mul = _per_note(
            [
                self.bite * (self.bite_floor + (1 - self.bite_floor) * velocity)
                for velocity in self.velocities
            ]
        )
        self.tine_index.mul = _per_note(
            [self.bark * velocity**2 for velocity in self.velocities]
        )

    def on_evolve(self, index: int) -> None:
        """Rotate which voicing set is comping the shared vamp; called
        rarely (tens of bars) by a rack-level `GroupController`, never by
        the clock directly. Owns its own wraparound, per `on_evolve`'s
        contract - there's no shared numeric range to clamp against."""
        self._progression_index = index % len(self._voicing_sets)

    def build(self, context: BuildContext) -> Patch:
        self._reset()

        # explicit per patches/AGENTS.md rule 5 (timing/state), not a
        # `@Param`: only `on_evolve` and `next_step()` read/write it
        self._progression_index = 0
        self._voicing_sets = KeysProgression.by_index(int(self.vamp)).voicing_sets
        self.velocities = [0.0] * SLOTS
        self.freqs = [self.root_freq] * (SLOTS * NOTES)
        self.triggers = [Trig().stop() for _ in range(SLOTS)]
        # one stream per (slot, note), each struck by its slot's trigger
        self.strikes = [trigger for trigger in self.triggers for _ in range(NOTES)]

        self.amp_table = LinTable(decay_points())
        self.body_table = LinTable(decay_points(RING_CURVE * self.body_speed))
        self.tine_table = LinTable(decay_points())
        self.amp = TrigEnv(self.strikes, self.amp_table, dur=self.decay, mul=0)
        self.body_index = TrigEnv(self.strikes, self.body_table, dur=self.decay, mul=0)
        self.tine_index = TrigEnv(
            self.strikes, self.tine_table, dur=self.tine_time, mul=0
        )
        # the tine pair fades soon after its ping: `FM` integrates frequency, so
        # the index burst leaves the tine's carrier out of phase with the body's
        # on the same pitch, and a tine carrier left ringing would cancel part of
        # the body's fundamental (see test_keys.py)
        self.tine_amp = TrigEnv(self.strikes, self.amp_table, dur=self.tine_ring, mul=0)

        # each voice's base pitch lives in its own Sig instead of a plain
        # float, so a continuous wobble ratio can multiply every currently-
        # sounding note between triggers, not just restate it at the strike
        self.freq_sigs = [Sig(freq) for freq in self.freqs]
        self.wobble_depth = SigTo(value=self.wobble * self.wobble_depth_max, time=0.5)
        self.wobble_lfo = Sine(freq=self.wobble_rate, mul=self.wobble_depth)
        self.wobble_ratio = self.wobble_lfo + 1
        self.wobbled_freqs = [sig * self.wobble_ratio for sig in self.freq_sigs]

        self.body = FM(
            carrier=self.wobbled_freqs,
            ratio=self.body_ratio,
            index=self.body_index,
            mul=self.amp,
        )
        self.tine = FM(
            carrier=self.wobbled_freqs,
            ratio=self.tine_ratio,
            index=self.tine_index,
            mul=self.tine_amp,
        )
        self.chord_notes_signal = self.body + self.tine
        self.mixed = self.chord_notes_signal.mix(1)
        # the body's ratio 1 puts its first lower sideband on 0 Hz: a DC offset
        # that follows the index envelope (see the FM bass). Clear it below the
        # lowest note.
        self.chord = ButHP(self.mixed, freq=self.subsonic)

        # gain swings between 1 - tremolo and 1
        self.depth = SigTo(value=self.tremolo / 2, time=0.05, init=self.tremolo / 2)
        self.tremolo_lfo = Sine(freq=1 / context.tempo.eighth, mul=self.depth)
        self.swing = self.tremolo_lfo - self.depth
        self.throb = self.swing + 1
        self.voice_signal = self.chord * self.throb

        self.schedule(self.base_division, self.rate, context.clock)
        self._step = self.step_pattern(BAR_STEPS, HITS)
        return self.finish(
            self.add_gate(self.voice_signal, context),
            resources=(*self.triggers, *self.freq_sigs, *self.wobbled_freqs),
        )

    def next_step(self) -> None:
        # derived from the shared clock's own tick, not a local counter
        # that starts at 0 whenever this patch is built or restarted -
        # see Harmony's docstring on why chord/beat position must come
        # from the clock, never from a patch's own step count
        step = self._step()
        if step.hit:
            bar = self._clock.bar_index
            hit_index = bar * len(HIT_STEPS) + HIT_STEPS.index(step.index)
            slot = hit_index % SLOTS
            progression = self._voicing_sets[self._progression_index]
            chord_notes = progression[bar % len(progression)]
            start = slot * NOTES
            new_freqs = [
                notes.transpose(self.root_freq, semitones) for semitones in chord_notes
            ]
            self.freqs[start : start + NOTES] = new_freqs
            for offset, freq in enumerate(new_freqs):
                self.freq_sigs[start + offset].value = freq
            self.velocities[slot] = step.value
            self.apply_touch()
            self.triggers[slot].play()
