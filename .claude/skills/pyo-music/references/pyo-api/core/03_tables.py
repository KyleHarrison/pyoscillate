"""3. Tables -- not sound themselves, but shapes/data that generators read from.

An `Osc` needs a table to know what waveform to play each cycle. Tables are
pre-computed arrays of samples (a waveform, a window, a breakpoint curve)
rather than live signals.
"""

__all__ = ["SquareTable", "SawTable", "CosTable", "CurveTable"]

from pyo import SquareTable

"""
SquareTable(order=10, size=8192)

Generates a square waveform in a table, built from `order` harmonics.

Params:
    order -- Number of harmonics used to build the waveform. Default 10.
    size  -- Table size in samples. Default 8192.
"""

from pyo import SawTable

"""
SawTable(order=10, size=8192)

Generates a sawtooth waveform in a table, built from `order` harmonics.

Params:
    order -- Number of harmonics used to build the waveform. Default 10.
    size  -- Table size in samples. Default 8192.
"""

from pyo import CosTable

"""
CosTable(list=[(0, 0), (8191, 1)], size=8192)

Builds a table from cosine-interpolated segments between breakpoints.

Params:
    list -- List of (time, value) breakpoint tuples. Default a single rising
            ramp across the table.
    size -- Table size in samples. Default 8192.
"""

from pyo import CurveTable

"""
CurveTable(list=[(0, 0), (8191, 1)], tension=0, bias=0, size=8192)

Builds a table from curved (Kochanek-Bartels spline) segments between
breakpoints -- like CosTable but with adjustable curve tension/bias.

Params:
    list    -- List of (time, value) breakpoint tuples.
    tension -- Curve tension, -1 to 1. Default 0.
    bias    -- Curve bias, -1 to 1. Default 0.
    size    -- Table size in samples. Default 8192.
"""
