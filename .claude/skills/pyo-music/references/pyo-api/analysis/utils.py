"""Utilities -- small conversion/utility helpers (unit conversion,
sample-and-hold, writing audio to disk). Not used by this project yet.
"""

__all__ = ["Scale", "SampHold", "Interp", "MToF", "Record"]

from pyo import Scale

"""
Scale(input, inmin=0, inmax=1, outmin=0, outmax=1, exp=1, mul=1, add=0)

Maps an input range of values onto an output range, linearly or
exponentially.

Params:
    input  -- Signal to rescale.
    inmin  -- Lower bound of the input range. Default 0.
    inmax  -- Upper bound of the input range. Default 1.
    outmin -- Lower bound of the output range. Default 0.
    outmax -- Upper bound of the output range. Default 1.
    exp    -- Exponent applied to the scaling curve (1 = linear).
              Default 1.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import SampHold

"""
SampHold(input, controlsig=0, value=0, mul=1, add=0)

Samples and holds the input signal's value whenever `controlsig` crosses
`value`.

Params:
    input      -- Signal to sample.
    controlsig -- Control signal that triggers a new sample when it crosses
                  `value`. Default 0.
    value      -- Threshold that `controlsig` must cross. Default 0.
    mul        -- Output multiplier. Default 1.
    add        -- Output additive value. Default 0.
"""

from pyo import Interp

"""
Interp(input, input2, interp=0.5, mul=1, add=0)

Interpolates between two signals.

Params:
    input  -- First signal.
    input2 -- Second signal.
    interp -- Interpolation position, 0 (all input) to 1 (all input2).
              Default 0.5.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import MToF

"""
MToF(input, mul=1, add=0)

Converts a MIDI note number to its equivalent frequency in Hz.

Params:
    input -- MIDI note number (or signal of note numbers).
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Record

"""
Record(input, filename, chnls=2, fileformat=0, sampletype=0, buffering=4)

Writes an input signal to an audio file on disk.

Params:
    input      -- Signal(s) to record.
    filename   -- Output file path.
    chnls      -- Number of channels to record. Default 2.
    fileformat -- File format (0=WAV, 1=AIFF, ...). Default 0.
    sampletype -- Sample type (0=16-bit int, 1=24-bit int, ...). Default 0.
    buffering  -- Internal buffer size factor. Default 4.
"""
