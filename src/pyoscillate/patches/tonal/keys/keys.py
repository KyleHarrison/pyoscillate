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
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.filters import ButHP
from pyo.lib.generators import FM, Sine
from pyo.lib.tables import LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import RING_CURVE, GatedVoice, decay_points
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

# semitones above Register (the key's tonic), one close rootless voicing per
# bar: Am9 (C E G B), Dm9 (F A C E), Fmaj9 (A C E G), Em7 (G B D E). The
# common tones keep the top voices moving by step.
CHORDS = ((3, 7, 10, 14), (-4, 0, 3, 7), (0, 3, 7, 10), (-2, 2, 5, 7))
# step on the 16th grid -> velocity: the Charleston rhythm
HITS = {0: 1.0, 6: 0.55}
BAR_STEPS = 16
NOTES = 4
SLOTS = 4


def _per_note(per_slot: list[float]) -> list[float]:
    """Spread one value per chord slot across that slot's note streams."""
    return [value for value in per_slot for _ in range(NOTES)]


class Keys(GatedVoice):
    """FM electric piano comping `CHORDS` in the Charleston rhythm. See the
    module docstring for the sonic detail."""

    title = "Keys (FM electric piano)"
    summary = "Struck FM electric piano comping a close-voiced progression."
    volume_default = 0.8
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

    # the graph, assigned by build(); finish() retains every one of them
    triggers: list[Trig]
    strikes: list[Trig]
    freqs: list[float]
    velocities: list[float]
    amp_table: LinTable
    body_table: LinTable
    tine_table: LinTable
    amp: TrigEnv
    body_index: TrigEnv
    tine_index: TrigEnv
    tine_amp: TrigEnv
    body: FM
    tine: FM
    chord_notes_signal: PyoObject
    mixed: PyoObject
    chord: ButHP
    depth: SigTo
    wobble: Sine
    swing: PyoObject
    throb: PyoObject
    voice_signal: PyoObject

    # only read at trigger time (next_step()), so it needs no live control -
    # Patch.set() already keeps self.root_freq current on its own
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
    )
    def tremolo(self, value: float) -> None:
        self.depth.value = value / 2

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

    def build(self, tempo: Tempo, clock: Clock) -> Patch:
        self._reset()

        self._step = 0
        self._slot = 0
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
        self.tine_index = TrigEnv(self.strikes, self.tine_table, dur=self.tine_time, mul=0)
        # the tine pair fades soon after its ping: `FM` integrates frequency, so
        # the index burst leaves the tine's carrier out of phase with the body's
        # on the same pitch, and a tine carrier left ringing would cancel part of
        # the body's fundamental (see test_keys.py)
        self.tine_amp = TrigEnv(self.strikes, self.amp_table, dur=self.tine_ring, mul=0)
        self.body = FM(carrier=self.freqs, ratio=self.body_ratio, index=self.body_index, mul=self.amp)
        self.tine = FM(carrier=self.freqs, ratio=self.tine_ratio, index=self.tine_index, mul=self.tine_amp)
        self.chord_notes_signal = self.body + self.tine
        self.mixed = self.chord_notes_signal.mix(1)
        # the body's ratio 1 puts its first lower sideband on 0 Hz: a DC offset
        # that follows the index envelope (see the FM bass). Clear it below the
        # lowest note.
        self.chord = ButHP(self.mixed, freq=self.subsonic)

        # gain swings between 1 - tremolo and 1
        self.depth = SigTo(value=self.tremolo / 2, time=0.05, init=self.tremolo / 2)
        self.wobble = Sine(freq=1 / tempo.eighth, mul=self.depth)
        self.swing = self.wobble - self.depth
        self.throb = self.swing + 1
        self.voice_signal = self.chord * self.throb

        def next_step() -> None:
            step = self._step % BAR_STEPS
            velocity = HITS.get(step)
            if velocity is not None:
                slot = self._slot
                chord_notes = CHORDS[(self._step // BAR_STEPS) % len(CHORDS)]
                start = slot * NOTES
                self.freqs[start : start + NOTES] = [
                    self.root_freq * 2 ** (semitones / 12) for semitones in chord_notes
                ]
                self.body.carrier = self.freqs
                self.tine.carrier = self.freqs
                self.velocities[slot] = velocity
                self.apply_touch()
                self.triggers[slot].play()
                self._slot = (slot + 1) % SLOTS
            self._step += 1

        self.schedule(self.base_division, self.rate, clock, next_step)
        return self.finish(self.voice_signal, resources=tuple(self.triggers))
