"""Random generators -- free-running (non-triggered) random value
generators; the continuous counterpart to the trig-reactive Trig* random
objects (see ../core/05_trig_reactive.py). Not used by this project yet.
"""

__all__ = ['Choice', 'Randh', 'Xnoise', 'Urn']

from pyo import Choice

"""
Choice(choice=[0, 1], freq=1, mul=1, add=0)

Periodically chooses a new value from a user-supplied list, at `freq`
times per second.

Params:
    choice -- List of values to choose from. Default [0, 1].
    freq   -- Rate of new choices, in Hz. Default 1.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import Randh

"""
Randh(min=0, max=1, freq=1, mul=1, add=0)

Periodic pseudo-random generator -- holds a new random value (no
interpolation) at `freq` times per second.

Params:
    min  -- Lower bound of the random range. Default 0.
    max  -- Upper bound of the random range. Default 1.
    freq -- Rate of new random values, in Hz. Default 1.
    mul  -- Output multiplier. Default 1.
    add  -- Output additive value. Default 0.
"""

from pyo import Xnoise

"""
Xnoise(dist="uniform", freq=1, x1=0.5, x2=0.5, mul=1, add=0)

X-class pseudo-random generator -- like Randh but drawing from a choice of
probability distributions instead of a flat uniform range.

Params:
    dist -- Distribution name (e.g. "uniform", "expon", "gaussian").
            Default "uniform".
    freq -- Rate of new random values, in Hz. Default 1.
    x1   -- First distribution shape parameter. Default 0.5.
    x2   -- Second distribution shape parameter. Default 0.5.
    mul  -- Output multiplier. Default 1.
    add  -- Output additive value. Default 0.
"""

from pyo import Urn

"""
Urn(max=100, freq=1, mul=1, add=0)

Periodic pseudo-random integer generator without duplicates -- draws
without replacement from range(max) until exhausted, then reshuffles.

Params:
    max  -- Number of integers to draw from (0 to max-1). Default 100.
    freq -- Rate of new draws, in Hz. Default 1.
    mul  -- Output multiplier. Default 1.
    add  -- Output additive value. Default 0.
"""
