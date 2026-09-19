"""Dynamics processors -- compression, gating, clipping, degrade. All defined in pyo/lib/dynamics.py."""

__all__ = ['Clip', 'Mirror', 'Degrade', 'Compress', 'Gate', 'Balance', 'Min', 'Max', 'Expand']

from pyo import Clip
"""
Clip(input, min=-1.0, max=1.0, mul=1, add=0)

Clips a signal to a predefined limit.

Params:
    input -- Input signal to process.
    min   -- Minimum possible value. Defaults to -1.
    max   -- Maximum possible value. Defaults to 1.
"""

from pyo import Mirror
"""
Mirror(input, min=0.0, max=1.0, mul=1, add=0)

Reflects the signal that exceeds the `min` and `max` thresholds.

This object is useful for table indexing or for clipping and
modeling an audio signal.

Params:
    input -- Input signal to process.
    min   -- Minimum possible value. Defaults to 0.
    max   -- Maximum possible value. Defaults to 1.
"""

from pyo import Degrade
"""
Degrade(input, bitdepth=16, srscale=1.0, mul=1, add=0)

Signal quality reducer.

Degrade takes an audio signal and reduces the sampling rate and/or
bit-depth as specified.

Params:
    input    -- Input signal to process.
    bitdepth -- Signal quantization in bits. Must be in range 1 -> 32. Defaults to 16.
    srscale  -- Sampling rate multiplier. Must be in range 0.0009765625 -> 1. Defaults to 1.
"""

from pyo import Compress
"""
Compress(input, thresh=-20, ratio=2, risetime=0.01, falltime=0.1, lookahead=5.0, knee=0, outputAmp=False, mul=1, add=0)

Reduces the dynamic range of an audio signal.

Compress reduces the volume of loud sounds or amplifies quiet sounds by
narrowing or compressing an audio signal's dynamic range.

Params:
    input     -- Input signal to process.
    thresh    -- Level, expressed in dB, above which the signal is reduced. Reference level is 0dB. Defaults to -20.
    ratio     -- Determines the input/output ratio for signals above the threshold. Defaults to 2.
    risetime  -- Used in amplitude follower, time to reach upward value in seconds. Defaults to 0.01.
    falltime  -- Used in amplitude follower, time to reach downward value in seconds. Defaults to 0.1.
    lookahead -- Delay length, in ms, for the "look-ahead" buffer. Range is 0 -> 25 ms. Defaults to 5.0.
    knee      -- Shape of the transfert function around the threshold, specified in the range 0 -> 1. A value of 0 means a hard knee and a value of 1.0 means a softer knee. Defaults to 0.
    outputAmp -- If True, the object's output signal will be the compression level alone, not the compressed signal. It can be useful if 2 or more channels need to be linked on the same compression slope. Defaults to False. Available at initialization only.
"""

from pyo import Gate
"""
Gate(input, thresh=-70, risetime=0.01, falltime=0.05, lookahead=5.0, outputAmp=False, mul=1, add=0)

Allows a signal to pass only when its amplitude is above a set threshold.

A noise gate is used when the level of the signal is below the level of
the noise floor. The threshold is set above the level of the noise and so when
there is no signal the gate is closed. A noise gate does not remove noise
from the signal. When the gate is open both the signal and the noise will
pass through.

Params:
    input     -- Input signal to process.
    thresh    -- Level, expressed in dB, below which the gate is closed. Reference level is 0dB. Defaults to -70.
    risetime  -- Time to open the gate in seconds. Defaults to 0.01.
    falltime  -- Time to close the gate in seconds. Defaults to 0.05.
    lookahead -- Delay length, in ms, for the "look-ahead" buffer. Range is 0 -> 25 ms. Defaults to 5.0.
    outputAmp -- If True, the object's output signal will be the gating level alone, not the gated signal. It can be useful if 2 or more channels need to linked on the same gating slope. Defaults to False. Available at initialization only.
"""

from pyo import Balance
"""
Balance(input, input2, freq=10, mul=1, add=0)

Adjust rms power of an audio signal according to the rms power of another.

The rms power of a signal is adjusted to match that of a comparator signal.

Params:
    input  -- Input signal to process.
    input2 -- Comparator signal.
    freq   -- Cutoff frequency of the lowpass filter in hertz. Default to 10.
"""

from pyo import Min
"""
Min(input, comp=0.5, mul=1, add=0)

Outputs the minimum of two values.

Params:
    input -- Input signal to process.
    comp  -- Comparison value. If `input` is lower than this value, `input` is send to the output, otherwise, `comp` is outputted.
"""

from pyo import Max
"""
Max(input, comp=0.5, mul=1, add=0)

Outputs the maximum of two values.

Params:
    input -- Input signal to process.
    comp  -- Comparison value. If `input` is higher than this value, `input` is send to the output, otherwise, `comp` is outputted.
"""

from pyo import Expand
"""
Expand(input, downthresh=-40, upthresh=-10, ratio=2, risetime=0.01, falltime=0.1, lookahead=5.0, outputAmp=False, mul=1, add=0)

Expand the dynamic range of an audio signal.

The Expand object will boost the volume of the input sound if it rises
above the upper threshold. It will also reduce the volume of the input
sound if it falls below the lower threshold. This process will "expand"
the audio signal's dynamic range.

Params:
    input      -- Input signal to process.
    downthresh -- Level, expressed in dB, below which the signal is getting softer, according to the `ratio`. Reference level is 0dB. Defaults to -20.
    upthresh   -- Level, expressed in dB, above which the signal is getting louder, according to the same `ratio` as the lower threshold. Reference level is 0dB. Defaults to -20.
    ratio      -- The `ratio` argument controls is the amount of expansion (with a ratio of 4, if there is a rise of 2 dB above the upper threshold, the output signal will rises by 8 dB), and contrary for the lower threshold. Defaults to 2.
    risetime   -- Used in amplitude follower, time to reach upward value in seconds. Defaults to 0.01.
    falltime   -- Used in amplitude follower, time to reach downward value in seconds. Defaults to 0.1.
    lookahead  -- Delay length, in ms, for the "look-ahead" buffer. Range is 0 -> 25 ms. Defaults to 5.0.
    outputAmp  -- If True, the object's output signal will be the expansion level alone, not the expanded signal. It can be useful if 2 or more channels need to be linked on the same expansion slope. Defaults to False. Available at initialization only.
"""
