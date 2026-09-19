"""Random-value generator objects (as opposed to trigger-driven random draws in triggers.py). All defined in pyo/lib/randoms.py."""

__all__ = ['Randi', 'Randh', 'Choice', 'RandInt', 'RandDur', 'Xnoise', 'XnoiseMidi', 'XnoiseDur', 'Urn', 'LogiMap']

from pyo import Randi
"""
Randi(min=0.0, max=1.0, freq=1.0, mul=1, add=0)

Periodic pseudo-random generator with interpolation.

Randi generates a pseudo-random number between `min` and `max`
values at a frequency specified by `freq` parameter. Randi will
produce straight-line interpolation between current number and the next.

Params:
    min  -- Minimum value for the random generation. Defaults to 0.
    max  -- Maximum value for the random generation. Defaults to 1.
    freq -- Polling frequency. Defaults to 1.
"""

from pyo import Randh
"""
Randh(min=0.0, max=1.0, freq=1.0, mul=1, add=0)

Periodic pseudo-random generator.

Randh generates a pseudo-random number between `min` and `max`
values at a frequency specified by `freq` parameter. Randh will
hold generated value until next generation.

Params:
    min  -- Minimum value for the random generation. Defaults to 0.
    max  -- Maximum value for the random generation. Defaults to 1.
    freq -- Polling frequency. Defaults to 1.
"""

from pyo import Choice
"""
Choice(choice, freq=1.0, mul=1, add=0)

Periodically choose a new value from a user list.

Choice chooses a new value from a predefined list of floats `choice`
at a frequency specified by `freq` parameter. Choice will
hold choosen value until next generation.

Params:
    choice -- Possible values for the random generation.
    freq   -- Polling frequency. Defaults to 1.
"""

from pyo import RandInt
"""
RandInt(max=100, freq=1.0, mul=1, add=0)

Periodic pseudo-random integer generator.

RandInt generates a pseudo-random integer number between 0 and `max`
values at a frequency specified by `freq` parameter. RandInt will
hold generated value until the next generation.

Params:
    max  -- Maximum value for the random generation. Defaults to 100.
    freq -- Polling frequency. Defaults to 1.
"""

from pyo import RandDur
"""
RandDur(min=0.0, max=1.0, mul=1, add=0)

Recursive time varying pseudo-random generator.

RandDur generates a pseudo-random number between `min` and `max`
arguments and uses that number to set the delay time before the next
generation. RandDur will hold the generated value until next generation.

Params:
    min -- Minimum value for the random generation. Defaults to 0.
    max -- Maximum value for the random generation. Defaults to 1.
"""

from pyo import Xnoise
"""
Xnoise(dist=0, freq=1.0, x1=0.5, x2=0.5, mul=1, add=0)

X-class pseudo-random generator.

Xnoise implements a few of the most common noise distributions.
Each distribution generates values in the range 0 and 1.

Params:
    dist -- Distribution type. Defaults to 0.
    freq -- Polling frequency. Defaults to 1.
    x1   -- First parameter. Defaults to 0.5.
    x2   -- Second parameter. Defaults to 0.5.
"""

from pyo import XnoiseMidi
"""
XnoiseMidi(dist=0, freq=1.0, x1=0.5, x2=0.5, scale=0, mrange=(0, 127), mul=1, add=0)

X-class midi notes pseudo-random generator.

XnoiseMidi implements a few of the most common noise distributions.
Each distribution generates integer values in the range defined with
`mrange` parameter and output can be scaled on midi notes, hertz or
transposition factor.

Params:
    dist   -- Distribution type. Defaults to 0.
    freq   -- Polling frequency. Defaults to 1.
    x1     -- First parameter. Defaults to 0.5.
    x2     -- Second parameter. Defaults to 0.5.
    scale  -- Output format. 0 = Midi, 1 = Hertz, 2 = transposition factor. In the transposition mode, the central key (the key where there is no transposition) is (`minrange` + `maxrange`) / 2. Defaults to 0.
    mrange -- Minimum and maximum possible values, in Midi notes. Available only at initialization time. Defaults to (0, 127).
"""

from pyo import XnoiseDur
"""
XnoiseDur(dist=0, min=0.0, max=1.0, x1=0.5, x2=0.5, mul=1, add=0)

Recursive time varying X-class pseudo-random generator.

Xnoise implements a few of the most common noise distributions.
Each distribution generates values in the range 0 to 1, which are
then rescaled between `min` and `max` arguments. The object uses
the generated value to set the delay time before the next generation.
XnoiseDur will hold the value until next generation.

Params:
    dist -- Distribution type. Can be the name of the distribution as a string or its associated number. Defaults to 0.
    min  -- Minimum value for the random generation. Defaults to 0.
    max  -- Maximum value for the random generation. Defaults to 1.
    x1   -- First parameter. Defaults to 0.5.
    x2   -- Second parameter. Defaults to 0.5.
"""

from pyo import Urn
"""
Urn(max=100, freq=1.0, mul=1, add=0)

Periodic pseudo-random integer generator without duplicates.

Urn generates a pseudo-random integer number between 0 and `max`
values at a frequency specified by `freq` parameter. Urn will
hold generated value until the next generation. Urn works like RandInt,
except that it keeps track of each number which has been generated. After
all numbers have been outputed, the pool is reseted and the object send
a trigger signal.

Params:
    max  -- Maximum value for the random generation. Defaults to 100.
    freq -- Polling frequency. Defaults to 1.
"""

from pyo import LogiMap
"""
LogiMap(chaos=0.6, freq=1.0, init=0.5, mul=1, add=0)

Random generator based on the logistic map.

The logistic equation (sometimes called the Verhulst model or logistic
growth curve) is a model of population growth first published by Pierre
Verhulst (1845, 1847). The logistic map is a discrete quadratic recurrence
equation derived from the logistic equation that can be effectively used
as a number generator that exhibit chaotic behavior. This object uses the
following equation:

    x[n] = (r + 3) * x[n-1] * (1.0 - x[n-1])

where 'r' is the randomization factor between 0 and 1.

Params:
    chaos -- Randomization factor, 0.0 < chaos < 1.0. Defaults to 0.6.
    freq  -- Polling frequency. Defaults to 1.
    init  -- Initial value, 0.0 < init < 1.0. Defaults to 0.5.
"""
