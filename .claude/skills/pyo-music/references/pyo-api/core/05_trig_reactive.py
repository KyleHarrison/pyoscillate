"""5. Trig-reactive objects -- listen for a trigger and do something each
time one arrives.

This is how "Metro fires -> new note happens" gets wired up: a trigger
source (04_triggers.py) feeds one of these, and each pulse causes a fresh
envelope, a fresh random value, etc.
"""

__all__ = ["TrigEnv", "TrigXnoiseMidi", "TrigRand"]

from pyo import TrigEnv

"""
TrigEnv(input, table, dur=1, mul=1, add=0)

Reads through a table's shape once, from the start, every time a trigger
arrives -- i.e. replays an arbitrary envelope shape on each note.

Params:
    input -- Trigger stream (e.g. a Metro) that restarts the envelope.
    table -- PyoTableObject holding the envelope shape to read.
    dur   -- Duration of the envelope read, in seconds. Default 1.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import TrigXnoiseMidi

"""
TrigXnoiseMidi(input, dist="uniform", x1=1, x2=0.5, scale=1,
                mrange=(0, 127), mul=1, add=0)

Picks a new random MIDI note (optionally converted to Hz) each time a
trigger arrives, drawn from one of several probability distributions.

Params:
    input  -- Trigger stream that fires a new random draw.
    dist   -- Distribution name (e.g. "uniform", "expon", "biexp", "gaussian").
              Default "uniform".
    x1     -- First distribution shape parameter. Default 1.
    x2     -- Second distribution shape parameter. Default 0.5.
    scale  -- Output scaling (0=MIDI note, 1=Hz, 2=transposition factor).
              Default 1.
    mrange -- (min, max) MIDI note range to draw from. Default (0, 127).
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import TrigRand

"""
TrigRand(input, min=0, max=1, port=0, init=0, mul=1, add=0)

Picks a new random float in [min, max) each time a trigger arrives.

Params:
    input -- Trigger stream that fires a new random draw.
    min   -- Lower bound of the random range. Default 0.
    max   -- Upper bound of the random range. Default 1.
    port  -- Portamento time (seconds) to glide to the new value. Default 0.
    init  -- Initial value before the first trigger. Default 0.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""
