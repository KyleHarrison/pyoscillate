"""Event Sequencing -- periodically call back into Python code, as opposed
to the Trig* objects (see ../core/04_triggers.py / ../core/05_trig_reactive.py)
which stay
inside the audio graph. Not used by this project yet.
"""

__all__ = ["Pattern", "CallAfter", "Score"]

from pyo import Pattern

"""
Pattern(function, time=1, arg=None)

Periodically calls a Python function, on the audio thread's scheduling
clock.

Params:
    function -- Python callable to invoke.
    time     -- Time between calls, in seconds. Default 1.
    arg      -- Optional argument passed to `function`. Default None.
"""

from pyo import CallAfter

"""
CallAfter(function, time=1, arg=None)

Calls a Python function once, after a given delay.

Params:
    function -- Python callable to invoke.
    time     -- Delay before the call, in seconds. Default 1.
    arg      -- Optional argument passed to `function`. Default None.
"""

from pyo import Score

"""
Score(fname="event", callback=None)

Calls functions named `<fname><n>` in sequence, one per trigger, allowing a
sequence of differently-named Python callbacks to fire in order.

Params:
    fname    -- Common name prefix of the callback functions. Default
                "event".
    callback -- Optional function called after the last one in the sequence.
                Default None.
"""
