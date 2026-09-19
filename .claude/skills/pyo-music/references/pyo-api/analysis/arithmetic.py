"""Per-sample math operators as audio-rate objects (trig, log, rounding). All defined in pyo/lib/arithmetic.py."""

__all__ = ['Sin', 'Cos', 'Tan', 'Abs', 'Sqrt', 'Log', 'Log2', 'Log10', 'Atan2', 'Floor', 'Ceil', 'Round', 'Tanh', 'Exp', 'Div', 'Sub']

from pyo import Sin
"""
Sin(input, mul=1, add=0)

Performs a sine function on audio signal.

Returns the sine of audio signal as input.

Params:
    input -- Input signal, angle in radians.
"""

from pyo import Cos
"""
Cos(input, mul=1, add=0)

Performs a cosine function on audio signal.

Returns the cosine of audio signal as input.

Params:
    input -- Input signal, angle in radians.
"""

from pyo import Tan
"""
Tan(input, mul=1, add=0)

Performs a tangent function on audio signal.

Returns the tangent of audio signal as input.

Params:
    input -- Input signal, angle in radians.
"""

from pyo import Abs
"""
Abs(input, mul=1, add=0)

Performs an absolute function on audio signal.

Returns the absolute value of audio signal as input.

Params:
    input -- Input signal to process.
"""

from pyo import Sqrt
"""
Sqrt(input, mul=1, add=0)

Performs a square-root function on audio signal.

Returns the square-root value of audio signal as input.

Params:
    input -- Input signal to process.
"""

from pyo import Log
"""
Log(input, mul=1, add=0)

Performs a natural log function on audio signal.

Returns the natural log value of of audio signal as input.
Values less than 0.0 return 0.0.

Params:
    input -- Input signal to process.
"""

from pyo import Log2
"""
Log2(input, mul=1, add=0)

Performs a base 2 log function on audio signal.

Returns the base 2 log value of audio signal as input.
Values less than 0.0 return 0.0.

Params:
    input -- Input signal to process.
"""

from pyo import Log10
"""
Log10(input, mul=1, add=0)

Performs a base 10 log function on audio signal.

Returns the base 10 log value of audio signal as input.
Values less than 0.0 return 0.0.

Params:
    input -- Input signal to process.
"""

from pyo import Atan2
"""
Atan2(b=1, a=1, mul=1, add=0)

Computes the principal value of the arc tangent of b/a.

Computes the principal value of the arc tangent of b/a,
using the signs of both arguments to determine the quadrant
of the return value.

Params:
    b -- Numerator. Defaults to 1.
    a -- Denominator. Defaults to 1.
"""

from pyo import Floor
"""
Floor(input, mul=1, add=0)

Rounds to largest integral value not greater than audio signal.

For each samples in the input signal, rounds to the largest integral
value not greater than the sample value.

Params:
    input -- Input signal to process.
"""

from pyo import Ceil
"""
Ceil(input, mul=1, add=0)

Rounds to smallest integral value greater than or equal to the input signal.

For each samples in the input signal, rounds to the smallest integral
value greater than or equal to the sample value.

Params:
    input -- Input signal to process.
"""

from pyo import Round
"""
Round(input, mul=1, add=0)

Rounds to the nearest integer value in a floating-point format.

For each samples in the input signal, rounds to the nearest integer
value of the sample value.

Params:
    input -- Input signal to process.
"""

from pyo import Tanh
"""
Tanh(input, mul=1, add=0)

Performs a hyperbolic tangent function on audio signal.

Returns the hyperbolic tangent of audio signal as input.

Params:
    input -- Input signal, angle in radians.
"""

from pyo import Exp
"""
Exp(input, mul=1, add=0)

Calculates the value of e to the power of x.

Returns the value of e to the power of x, where e is the base of the
natural logarithm, 2.718281828...

Params:
    input -- Input signal, the exponent.
"""

from pyo import Div
"""
Div(a=1, b=1, mul=1, add=0)

Divides a by b.

Params:
    a -- Numerator. Defaults to 1.
    b -- Denominator. Defaults to 1.
"""

from pyo import Sub
"""
Sub(a=1, b=1, mul=1, add=0)

Substracts b from a.

Params:
    a -- Left operand. Defaults to 1.
    b -- Right operand. Defaults to 1.
"""
