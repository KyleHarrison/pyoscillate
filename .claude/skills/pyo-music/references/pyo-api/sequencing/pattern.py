"""Callback-driven pattern/score sequencing. All defined in pyo/lib/pattern.py."""

__all__ = ['Pattern', 'Score', 'CallAfter']

from pyo import Pattern
"""
Pattern(function, time=1, arg=None)

Periodically calls a Python function.

The play() method starts the pattern timer and is not called
at the object creation time.

Params:
    function -- Python function to be called periodically.
    time     -- Time, in seconds, between each call. Default to 1.
    arg      -- Argument sent to the function's call. If None, the function will be called without argument. Defaults to None.
"""

from pyo import Score
"""
Score(input, fname='event_')

Calls functions by incrementation of a preformatted name.

Score takes audio stream containning integers in input and calls
a function whose name is the concatenation of `fname` and the changing
integer.

Can be used to sequence events, first by creating functions p0, p1,
p2, etc. and then, by passing a counter to a Score object with "p"
as `fname` argument. Functions are called without parameters.

Params:
    input -- Audio signal. Must contains integer numbers. Integer must change before calling its function again.
    fname -- Name of the functions to be called. Defaults to 'event_', meaning that the object will call the function 'event_0', 'event_1', 'event_2', and so on... Available at initialization time only.
"""

from pyo import CallAfter
"""
CallAfter(function, time=1, arg=None)

Calls a Python function after a given time.

Params:
    function -- Python callable execute after `time` seconds.
    time     -- Time, in seconds, before the call. Default to 1.
    arg      -- Argument sent to the called function. Default to None.
"""
