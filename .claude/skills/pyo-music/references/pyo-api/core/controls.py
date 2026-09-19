"""Control-signal generators for shaping amplitude/parameters over time: faders, ADSR, and line/exponential segment generators. All defined in pyo/lib/controls.py."""

__all__ = ['Fader', 'Adsr', 'Linseg', 'Expseg', 'SigTo']

from pyo import Fader
"""
Fader(fadein=0.01, fadeout=0.1, dur=0, mul=1, add=0)

Fadein - fadeout envelope generator.

Generate an amplitude envelope between 0 and 1 with control on fade
times and total duration of the envelope.

The play() method starts the envelope and is not called at the
object creation time.

Params:
    fadein  -- Rising time of the envelope in seconds. Defaults to 0.01.
    fadeout -- Falling time of the envelope in seconds. Defaults to 0.1.
    dur     -- Total duration of the envelope in seocnds. Defaults to 0, which means wait for the stop() method to start the fadeout.
"""

from pyo import Adsr
"""
Adsr(attack=0.01, decay=0.05, sustain=0.707, release=0.1, dur=0, mul=1, add=0)

Attack - Decay - Sustain - Release envelope generator.

Calculates the classical ADSR envelope using linear segments.
Duration can be set to 0 to give an infinite sustain. In this
case, the stop() method calls the envelope release part.

The play() method starts the envelope and is not called at the
object creation time.

Params:
    attack  -- Duration of the attack phase in seconds. Defaults to 0.01.
    decay   -- Duration of the decay in seconds. Defaults to 0.05.
    sustain -- Amplitude of the sustain phase. Defaults to 0.707.
    release -- Duration of the release in seconds. Defaults to 0.1.
    dur     -- Total duration of the envelope in seconds. Defaults to 0, which means wait for the stop() method to start the release phase.
"""

from pyo import Linseg
"""
Linseg(list, loop=False, initToFirstVal=False, mul=1, add=0)

Draw a series of line segments between specified break-points.

The play() method starts the envelope and is not called at the
object creation time.

Params:
    list           -- Points used to construct the line segments. Each tuple is a new point in the form (time, value). Times are given in seconds and must be in increasing order.
    loop           -- Looping mode. Defaults to False.
    initToFirstVal -- If True, audio buffer will be filled at initialization with the first value of the line. Defaults to False.
"""

from pyo import Expseg
"""
Expseg(list, loop=False, exp=10, inverse=True, initToFirstVal=False, mul=1, add=0)

Draw a series of exponential segments between specified break-points.

The play() method starts the envelope and is not called at the
object creation time.

Params:
    list           -- Points used to construct the line segments. Each tuple is a new point in the form (time, value). Times are given in seconds and must be in increasing order.
    loop           -- Looping mode. Defaults to False.
    exp            -- Exponent factor. Used to control the slope of the curves. Defaults to 10.
    inverse        -- If True, downward slope will be inversed. Useful to create biexponential curves. Defaults to True.
    initToFirstVal -- If True, audio buffer will be filled at initialization with the first value of the line. Defaults to False.
"""

from pyo import SigTo
"""
SigTo(value, time=0.025, init=0.0, mul=1, add=0)

Convert numeric value to PyoObject signal with portamento.

When `value` is changed, a ramp is applied from the current
value to the new value. Can be used with PyoObject to apply
a linear portamento on an audio signal.

Params:
    value -- Numerical value to convert.
    time  -- Ramp time, in seconds, to reach the new value. Defaults to 0.025.
    init  -- Initial value of the internal memory. Defaults to 0.
"""
