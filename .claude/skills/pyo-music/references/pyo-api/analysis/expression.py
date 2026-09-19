"""Prefix expression evaluators -- a small functional expression language
for writing DSP algorithms as text. Not used by this project yet.
"""

__all__ = ["Expr"]

from pyo import Expr

"""
Expr(input, expr="", initValue=0, mul=1, add=0)

Evaluates a prefix-notation DSP expression (a small built-in functional
language) against an input signal, sample by sample.

Params:
    input     -- Signal(s) available to the expression.
    expr      -- The prefix expression string, e.g. "(+ (sig 0) 0.5)".
                 Default "".
    initValue -- Initial output value before evaluation starts. Default 0.
    mul       -- Output multiplier. Default 1.
    add       -- Output additive value. Default 0.
"""
