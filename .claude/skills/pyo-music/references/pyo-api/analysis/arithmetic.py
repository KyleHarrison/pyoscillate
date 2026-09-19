"""Arithmetic -- per-sample math functions applied to a signal, for building
custom DSP expressions. Not used by this project yet.
"""

__all__ = ["Sin", "Log", "Abs", "Pow", "Round"]

from pyo import Sin

"""
Sin(input, mul=1, add=0)

Applies the sine function to an input signal, sample by sample.

Params:
    input -- Signal to transform.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Log

"""
Log(input, mul=1, add=0)

Applies the natural logarithm to an input signal, sample by sample.

Params:
    input -- Signal to transform.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Abs

"""
Abs(input, mul=1, add=0)

Applies the absolute value function to an input signal, sample by sample.

Params:
    input -- Signal to transform.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Pow

"""
Pow(base=10, exponent=1, mul=1, add=0)

Raises `base` to the power of `exponent`, sample by sample; either can be a
signal.

Params:
    base     -- Base value or signal. Default 10.
    exponent -- Exponent value or signal. Default 1.
    mul      -- Output multiplier. Default 1.
    add      -- Output additive value. Default 0.
"""

from pyo import Round

"""
Round(input, mul=1, add=0)

Rounds an input signal to the nearest integer, sample by sample.

Params:
    input -- Signal to transform.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""
