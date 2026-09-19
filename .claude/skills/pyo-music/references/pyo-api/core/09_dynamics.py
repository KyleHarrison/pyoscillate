"""9. Dynamics (gain management) -- reshape a signal's amplitude range
rather than its spectrum.

Sits between the signal chain and output, same conceptual slot as a filter
but working on level instead of tone. `Compress` is what
`src/pyoscillate/patches/base.py` wraps each patch's voice in before `.out()`,
so `Patch.volume` can push loudness up without clipping.
"""

__all__ = [
    "Compress",
    "Gate",
    "Clip",
    "Mirror",
    "Wrap",
    "Balance",
    "Expand",
    "Min",
    "Max",
]

from pyo import Compress

"""
Compress(input, thresh=-20, ratio=2, risetime=0.01, falltime=0.1,
          lookahead=5, knee=0, outputAmp=False, mul=1, add=0)

Reduces the dynamic range of a signal above a threshold -- used as a
limiter in this project (high ratio) so raising `mul`/`volume` increases
loudness without hard-clipping.

Params:
    input     -- Input signal to compress.
    thresh    -- Threshold in dB above which gain reduction kicks in.
                 Default -20.
    ratio     -- Compression ratio (e.g. 3 means 3dB in -> 1dB out above
                 threshold). Default 2.
    risetime  -- Time to respond to a level increase, in seconds.
                 Default 0.01.
    falltime  -- Time to release after a level decrease, in seconds.
                 Default 0.1.
    lookahead -- Lookahead time in ms, to catch transients before they clip.
                 Default 5.
    knee      -- Knee softness, 0 (hard) to 1 (soft). Default 0.
    outputAmp -- If True, outputs the gain reduction amount instead of the
                 processed signal. Default False.
    mul       -- Output multiplier. Default 1.
    add       -- Output additive value. Default 0.
"""

from pyo import Gate

"""
Gate(input, thresh=-70, risetime=0.01, falltime=0.05, lookahead=5,
     mul=1, add=0)

Mutes the signal whenever its amplitude falls below a threshold -- a noise
gate.

Params:
    input     -- Input signal to gate.
    thresh    -- Threshold in dB below which the signal is muted.
                 Default -70.
    risetime  -- Time to open the gate, in seconds. Default 0.01.
    falltime  -- Time to close the gate, in seconds. Default 0.05.
    lookahead -- Lookahead time in ms. Default 5.
    mul       -- Output multiplier. Default 1.
    add       -- Output additive value. Default 0.
"""

from pyo import Clip

"""
Clip(input, min=-1, max=1, mul=1, add=0)

Hard-clips the signal to [min, max].

Params:
    input -- Input signal to clip.
    min   -- Lower bound. Default -1.
    max   -- Upper bound. Default 1.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Mirror

"""
Mirror(input, min=0, max=1, mul=1, add=0)

Reflects the signal back into range whenever it exceeds min/max, instead of
clipping it flat.

Params:
    input -- Input signal to process.
    min   -- Lower bound. Default 0.
    max   -- Upper bound. Default 1.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Wrap

"""
Wrap(input, min=0, max=1, mul=1, add=0)

Wraps the signal around to the opposite bound whenever it exceeds min/max
(modulo-style, instead of clipping or reflecting).

Params:
    input -- Input signal to process.
    min   -- Lower bound. Default 0.
    max   -- Upper bound. Default 1.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Balance

"""
Balance(input, input2, freq=10, mul=1, add=0)

Adjusts the RMS power of `input` to match the RMS power of `input2` --
useful after a distortion/filter stage to restore the original loudness.

Params:
    input  -- Signal whose level will be adjusted.
    input2 -- Reference signal to match the RMS power of.
    freq   -- Frequency of the RMS-tracking internal filter, in Hz.
              Default 10.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import Expand

"""
Expand(input, downthresh=-40, upthresh=-10, ratio=2, risetime=0.01,
        falltime=0.1, lookahead=5, mul=1, add=0)

Expands the dynamic range of a signal -- the inverse of Compress; makes
quiet parts quieter and/or loud parts louder outside a threshold band.

Params:
    input      -- Input signal to expand.
    downthresh -- Threshold in dB below which downward expansion applies.
                  Default -40.
    upthresh   -- Threshold in dB above which upward expansion applies.
                  Default -10.
    ratio      -- Expansion ratio. Default 2.
    risetime   -- Response time to a level increase, in seconds.
                  Default 0.01.
    falltime   -- Response time to a level decrease, in seconds.
                  Default 0.1.
    lookahead  -- Lookahead time in ms. Default 5.
    mul        -- Output multiplier. Default 1.
    add        -- Output additive value. Default 0.
"""

from pyo import Min

"""
Min(x, y, mul=1, add=0)

Outputs the per-sample minimum of two signals/values.

Params:
    x   -- First input.
    y   -- Second input.
    mul -- Output multiplier. Default 1.
    add -- Output additive value. Default 0.
"""

from pyo import Max

"""
Max(x, y, mul=1, add=0)

Outputs the per-sample maximum of two signals/values.

Params:
    x   -- First input.
    y   -- Second input.
    mul -- Output multiplier. Default 1.
    add -- Output additive value. Default 0.
"""
