"""6. Envelopes / control signals -- shape a parameter over time, usually
gated by a trigger or note-on.

Used for one-shot shaping, like a note's loudness contour. `TrigEnv` (see
05_trig_reactive.py) also belongs here when it's driven by a recurring
trigger to replay a shape per note.
"""

__all__ = ["Adsr", "Fader"]

from pyo import Adsr

"""
Adsr(attack=0.01, decay=0.05, sustain=0.707, release=0.1, dur=0, mul=1)

Classical Attack-Decay-Sustain-Release envelope generator, built from
linear segments. Call `.play()` to trigger a new envelope.

Params:
    attack  -- Attack time, in seconds. Default 0.01.
    decay   -- Decay time, in seconds. Default 0.05.
    sustain -- Sustain level, 0-1. Default 0.707.
    release -- Release time, in seconds. Default 0.1.
    dur     -- Total duration; 0 means sustain indefinitely until `.stop()`.
               Default 0.
    mul     -- Output multiplier. Default 1.
"""

from pyo import Fader

"""
Fader(fadein=0.01, fadeout=0.1, dur=0, mul=1)

Simple fade-in/fade-out envelope between 0 and 1, without a sustain stage.
Call `.play()` to trigger.

Params:
    fadein  -- Fade-in time, in seconds. Default 0.01.
    fadeout -- Fade-out time, in seconds. Default 0.1.
    dur     -- Total duration; 0 means hold at 1 until `.stop()`.
               Default 0.
    mul     -- Output multiplier. Default 1.
"""
