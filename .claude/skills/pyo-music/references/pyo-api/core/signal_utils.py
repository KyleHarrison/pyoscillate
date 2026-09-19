"""Signal-utility PyoObjects that ship in pyo's core module rather than a topical one -- mixing, value holding/smoothing, arithmetic. All defined in pyo/lib/_core.py."""

__all__ = ['Mix', 'Dummy', 'InputFader', 'Sig', 'VarPort', 'Pow', 'Wrap', 'Compare']

from pyo import Mix
"""
Mix(input, voices=1, mul=1, add=0)

Mix audio streams to arbitrary number of streams.

Mix the object's audio streams as `input` argument into `voices`
streams.

Params:
    input  -- Input signal(s) to mix the streams.
    voices -- Number of streams of the Mix object. If more than 1, input object's streams are alternated and added into Mix object's streams. Defaults to 1.
"""

from pyo import Dummy
"""
Dummy(objs_list)

Dummy object used to perform arithmetics on PyoObject.

The user should never instantiate an object of this class.

Params:
    objs_list -- List of Stream objects return by the PyoObject hidden method getBaseObjects().
"""

from pyo import InputFader
"""
InputFader(input)

Audio streams crossfader.

Params:
    input -- Input signal.
"""

from pyo import Sig
"""
Sig(value, mul=1, add=0)

Convert numeric value to PyoObject signal.

Params:
    value -- Numerical value to convert.
"""

from pyo import VarPort
"""
VarPort(value, time=0.025, init=0.0, function=None, arg=None, mul=1, add=0)

Convert numeric value to PyoObject signal with portamento.

When `value` attribute is changed, a smoothed ramp is applied from the
current value to the new value. If a callback is provided as `function`
argument, it will be called at the end of the line.

Params:
    value    -- Numerical target value to reach as an audio stream.
    time     -- Ramp time, in seconds, to reach the new value. Defaults to 0.025.
    init     -- Initial value of the internal memory. Defaults to 0.
    function -- If provided, it will be called at the end of the line. Defaults to None.
    arg      -- Optional argument sent to the function called at the end of the line. Defaults to None.
"""

from pyo import Pow
"""
Pow(base=10, exponent=1, mul=1, add=0)

Performs a power function on audio signal.

Params:
    base     -- Base composant. Defaults to 10.
    exponent -- Exponent composant. Defaults to 1.
"""

from pyo import Wrap
"""
Wrap(input, min=0.0, max=1.0, mul=1, add=0)

Wraps-around the signal that exceeds the `min` and `max` thresholds.

This object is useful for table indexing, phase shifting or for
clipping and modeling an audio signal.

Params:
    input -- Input signal to process.
    min   -- Minimum possible value. Defaults to 0.
    max   -- Maximum possible value. Defaults to 1.
"""

from pyo import Compare
"""
Compare(input, comp, mode='<', mul=1, add=0)

Comparison object.

Compare evaluates a comparison between a PyoObject and a number or
between two PyoObjects and outputs 1.0, as audio stream, if the
comparison is true, otherwise outputs 0.0.

Params:
    input -- Input signal.
    comp  -- comparison signal.
    mode  -- Comparison operator as a string. Allowed operator are "<", "<=", ">", ">=", "==", "!=". Default to "<".
"""
