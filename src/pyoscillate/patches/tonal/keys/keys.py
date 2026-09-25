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

from typing import Any, ClassVar

from pyo.lib.controls import SigTo
from pyo.lib.filters import ButHP
from pyo.lib.generators import FM, Sine
from pyo.lib.tables import LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import RING_CURVE, decay_points
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A2,
        notes.E4,
        1,
        notes.A3,
        "Register",
        "Moves the chords up or down; low is warm and dark under a vocal, high is bell-like and sits above the mix.",
        (PyoParamRef(FM, "carrier"),),
        scale="note",
    ),
    SliderSpec(
        "bark",
        0,
        6,
        0.1,
        2.5,
        "Bark",
        "How much each strike pings: low is a soft, round touch, high a bright, glassy bark on hard notes that fades as the chord rings.",
        (PyoParamRef(TrigEnv, "mul"),),
    ),
    SliderSpec(
        "bite",
        0,
        3,
        0.1,
        0.8,
        "Bite",
        "The edge on the sustained tone: low is a pure, mellow Rhodes-like body, high a reedy, nasal Wurlitzer-like growl.",
        (PyoParamRef(TrigEnv, "mul"),),
    ),
    SliderSpec(
        "decay",
        0.5,
        4,
        0.1,
        1.8,
        "Decay",
        "How long each chord rings, in seconds, before it dies away; short is a tight stab, long lets the chords overlap.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "tremolo",
        0,
        1,
        0.05,
        0.3,
        "Tremolo",
        "How strongly the level throbs in 8th notes, like an electric piano through a tremolo amp; 0 holds it steady.",
        (PyoParamRef(SigTo, "value"),),
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the comping speed for each step away from its 16th-note grid.",
    ),
)
# semitones above Register (the key's tonic), one close rootless voicing per
# bar: Am9 (C E G B), Dm9 (F A C E), Fmaj9 (A C E G), Em7 (G B D E). The
# common tones keep the top voices moving by step.
CHORDS = ((3, 7, 10, 14), (-4, 0, 3, 7), (0, 3, 7, 10), (-2, 2, 5, 7))
# step on the 16th grid -> velocity: the Charleston rhythm
HITS = {0: 1.0, 6: 0.55}
BAR_STEPS = 16
NOTES = 4
SLOTS = 4
BODY_RATIO = 1
TINE_RATIO = 14
# seconds the tine's ping (its index) takes to die away
TINE_TIME = 0.08
# seconds the tine pair's own level takes to die away, after the ping
TINE_RING = 0.3
# the tine pair's level against the body's: loud enough to ping, quiet enough
# that the strike doesn't tower over the ring
TINE_LEVEL = 0.5
# the body's index falls this many times faster than the level, so the chord
# mellows as it rings
BODY_SPEED = 2.0
# soft notes keep this share of the body's Bite
BITE_FLOOR = 0.5
# four notes of two FM pairs each, in phase on the same carriers at the
# strike; the loudest chord in the slider ranges peaks at ~5 x GAIN x volume,
# 0.16 at the default volume, under the output ceiling
GAIN = 0.04
VOLUME_DEFAULT = 0.8
# under the lowest note (Register 110, four semitones down: 87 Hz)
SUBSONIC = 20


def _per_note(per_slot: list[float]) -> list[float]:
    """Spread one value per chord slot across that slot's note streams."""
    return [value for value in per_slot for _ in range(NOTES)]


class Keys(Patch):
    """FM electric piano comping `CHORDS` in the Charleston rhythm. See the
    module docstring for the sonic detail."""

    title = "Keys (FM electric piano)"
    summary = "Struck FM electric piano comping a close-voiced progression."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    needs_tempo: ClassVar[bool] = True
    needs_clock: ClassVar[bool] = True

    root_freq: float
    bark: float
    bite: float
    decay: float
    tremolo: float
    rate: float

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        state = {"step": 0, "slot": 0, "root": self.root_freq, "bark": self.bark, "bite": self.bite}
        velocities = [0.0] * SLOTS
        freqs = [self.root_freq] * (SLOTS * NOTES)
        triggers = [Trig().stop() for _ in range(SLOTS)]
        # one stream per (slot, note), each struck by its slot's trigger
        strikes = [trigger for trigger in triggers for _ in range(NOTES)]

        amp_table = LinTable(decay_points())
        body_table = LinTable(decay_points(RING_CURVE * BODY_SPEED))
        tine_table = LinTable(decay_points())
        amp = TrigEnv(strikes, amp_table, dur=self.decay, mul=0)
        body_index = TrigEnv(strikes, body_table, dur=self.decay, mul=0)
        tine_index = TrigEnv(strikes, tine_table, dur=TINE_TIME, mul=0)
        # the tine pair fades soon after its ping: `FM` integrates frequency, so
        # the index burst leaves the tine's carrier out of phase with the body's
        # on the same pitch, and a tine carrier left ringing would cancel part of
        # the body's fundamental (see test_keys.py)
        tine_amp = TrigEnv(strikes, amp_table, dur=TINE_RING, mul=0)
        body = FM(carrier=freqs, ratio=BODY_RATIO, index=body_index, mul=amp)
        tine = FM(carrier=freqs, ratio=TINE_RATIO, index=tine_index, mul=tine_amp)
        chord_notes_signal = body + tine
        mixed = chord_notes_signal.mix(1)
        # the body's ratio 1 puts its first lower sideband on 0 Hz: a DC offset
        # that follows the index envelope (see the FM bass). Clear it below the
        # lowest note.
        chord = ButHP(mixed, freq=SUBSONIC)

        # gain swings between 1 - tremolo and 1
        depth = SigTo(value=self.tremolo / 2, time=0.05, init=self.tremolo / 2)
        wobble = Sine(freq=1 / tempo.eighth, mul=depth)
        swing = wobble - depth
        throb = swing + 1
        voice = chord * throb
        self.retain(
            *triggers,
            amp_table,
            body_table,
            tine_table,
            amp,
            body_index,
            tine_index,
            tine_amp,
            body,
            tine,
            chord_notes_signal,
            mixed,
            chord,
            depth,
            wobble,
            swing,
            throb,
        )

        def apply_touch() -> None:
            """Rescale every slot's envelopes from its stored velocity."""
            amp.mul = _per_note([GAIN * velocity for velocity in velocities])
            tine_amp.mul = _per_note([GAIN * TINE_LEVEL * velocity for velocity in velocities])
            body_index.mul = _per_note(
                [state["bite"] * (BITE_FLOOR + (1 - BITE_FLOOR) * velocity) for velocity in velocities]
            )
            tine_index.mul = _per_note([state["bark"] * velocity**2 for velocity in velocities])

        def next_step() -> None:
            step = state["step"] % BAR_STEPS
            velocity = HITS.get(step)
            if velocity is not None:
                slot = state["slot"]
                chord_notes = CHORDS[(state["step"] // BAR_STEPS) % len(CHORDS)]
                start = slot * NOTES
                freqs[start : start + NOTES] = [
                    state["root"] * 2 ** (semitones / 12) for semitones in chord_notes
                ]
                body.carrier = freqs
                tine.carrier = freqs
                velocities[slot] = velocity
                apply_touch()
                triggers[slot].play()
                state["slot"] = (slot + 1) % SLOTS
            state["step"] += 1

        def set_touch(name: str, value: float) -> None:
            state[name] = value
            apply_touch()

        def set_decay(value: float) -> None:
            amp.dur = value
            body_index.dur = value

        division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, self.rate), next_step)
        self.sequencer = division
        self.voice = voice
        self.controls = {
            "root_freq": lambda value: state.update(root=value),
            "bark": lambda value: set_touch("bark", value),
            "bite": lambda value: set_touch("bite", value),
            "decay": set_decay,
            "tremolo": lambda value: setattr(depth, "value", value / 2),
            "rate": lambda value: setattr(
                division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        }
        return self
