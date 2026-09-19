"""PyoTableObject subclasses -- the wavetable/buffer data these table-driven generators read from (not audio signals themselves). All defined in pyo/lib/tables.py."""

__all__ = ['HarmTable', 'SawTable', 'SquareTable', 'TriangleTable', 'ChebyTable', 'HannTable', 'SincTable', 'WinTable', 'ParaTable', 'LinTable', 'LogTable', 'CosLogTable', 'CosTable', 'CurveTable', 'ExpTable', 'SndTable', 'NewTable', 'DataTable', 'AtanTable', 'PartialTable', 'PadSynthTable', 'SharedTable']

from pyo import HarmTable
"""
HarmTable(list=[1.0, 0.0], size=8192)

Harmonic waveform generator.

Generates composite waveforms made up of weighted sums
of simple sinusoids.

Params:
    list -- Relative strengths of the fixed harmonic partial numbers 1,2,3, etc. Defaults to [1].
    size -- Table size in samples. Defaults to 8192.
"""

from pyo import SawTable
"""
SawTable(order=10, size=8192)

Sawtooth waveform generator.

Generates sawtooth waveforms made up of fixed number of harmonics.

Params:
    order -- Number of harmonics sawtooth is made of. Defaults to 10.
    size  -- Table size in samples. Defaults to 8192.
"""

from pyo import SquareTable
"""
SquareTable(order=10, size=8192)

Square waveform generator.

Generates square waveforms made up of fixed number of harmonics.

Params:
    order -- Number of harmonics square waveform is made of. The waveform will contains `order` odd harmonics. Defaults to 10.
    size  -- Table size in samples. Defaults to 8192.
"""

from pyo import TriangleTable
"""
TriangleTable(order=10, size=8192)

Triangle waveform generator.

Generates triangle waveforms made up of fixed number of harmonics.

Params:
    order -- Number of harmonics triangle waveform is made of. The waveform will contains `order` odd harmonics. Defaults to 10.
    size  -- Table size in samples. Defaults to 8192.
"""

from pyo import ChebyTable
"""
ChebyTable(list=[1.0, 0.0], size=8192)

Chebyshev polynomials of the first kind.

Uses Chebyshev coefficients to generate stored polynomial functions
which, under waveshaping, can be used to split a sinusoid into
harmonic partials having a pre-definable spectrum.

Params:
    list -- Relative strengths of partials numbers 1,2,3, ..., 12 that will result when a sinusoid of amplitude 1 is waveshaped using this function table. Up to 12 partials can be specified. Defaults to [1].
    size -- Table size in samples. Defaults to 8192.
"""

from pyo import HannTable
"""
HannTable(size=8192)

Generates Hanning window function.

Params:
    size -- Table size in samples. Defaults to 8192.
"""

from pyo import SincTable
"""
SincTable(freq=6.283185307179586, windowed=False, size=8192)

Generates sinc window function.

Params:
    freq     -- Frequency, in radians, of the sinc function. Defaults to pi*2.
    windowed -- If True, an hanning window is applied on the sinc function. Defaults to False.
    size     -- Table size in samples. Defaults to 8192.
"""

from pyo import WinTable
"""
WinTable(type=2, size=8192)

Generates different kind of windowing functions.

Params:
    type -- Windowing function. Possible choices are: 0. Rectangular (no window) 1. Hamming 2. Hanning (default) 3. Bartlett (triangular) 4. Blackman 3-term 5. Blackman-Harris 4-term 6. Blackman-Harris 7-term 7. Tuckey (alpha = 0.66) 8. Sine (half-sine window)
    size -- Table size in samples. Defaults to 8192.
"""

from pyo import ParaTable
"""
ParaTable(size=8192)

Generates parabola window function.

The parabola is a conic section, the intersection of a right circular conical
surface and a plane parallel to a generating straight line of that surface.

Params:
    size -- Table size in samples. Defaults to 8192.
"""

from pyo import LinTable
"""
LinTable(list=[(0, 0.0), (8191, 1.0)], size=8192)

Construct a table from segments of straight lines in breakpoint fashion.

Params:
    list -- List of tuples indicating location and value of each points in the table. The default, [(0,0.), (8191, 1.)], creates a straight line from 0.0 at location 0 to 1.0 at the end of the table (size - 1). Location must be an integer.
    size -- Table size in samples. Defaults to 8192.
"""

from pyo import LogTable
"""
LogTable(list=[(0, 0.0), (8191, 1.0)], size=8192)

Construct a table from logarithmic segments in breakpoint fashion.

Params:
    list -- List of tuples indicating location and value of each points in the table. The default, [(0,0.), (8191, 1.)], creates a logarithmic line from 0.0 at location 0 to 1.0 at the end of the table (size - 1). Location must be an integer.
    size -- Table size in samples. Defaults to 8192.
"""

from pyo import CosLogTable
"""
CosLogTable(list=[(0, 0.0), (8191, 1.0)], size=8192)

Construct a table from logarithmic-cosine segments in breakpoint fashion.

Params:
    list -- List of tuples indicating location and value of each points in the table. The default, [(0,0.), (8191, 1.)], creates a logarithmic line from 0.0 at location 0 to 1.0 at the end of the table (size - 1). Location must be an integer.
    size -- Table size in samples. Defaults to 8192.
"""

from pyo import CosTable
"""
CosTable(list=[(0, 0.0), (8191, 1.0)], size=8192)

Construct a table from cosine interpolated segments.

Params:
    list -- List of tuples indicating location and value of each points in the table. The default, [(0,0.), (8191, 1.)], creates a cosine line from 0.0 at location 0 to 1.0 at the end of the table (size - 1). Location must be an integer.
    size -- Table size in samples. Defaults to 8192.
"""

from pyo import CurveTable
"""
CurveTable(list=[(0, 0.0), (8191, 1.0)], tension=0, bias=0, size=8192)

Construct a table from curve interpolated segments.

CurveTable uses Hermite interpolation (sort of cubic interpolation)
to calculate each points of the curve. This algorithm allows tension
and biasing controls. Tension can be used to tighten up the curvature
at the known points. The bias is used to twist the curve about the
known points.

Params:
    list    -- List of tuples indicating location and value of each points in the table. The default, [(0,0.), (8191, 1.)], creates a curved line from 0.0 at location 0 to 1.0 at the end of the table (size - 1). Location must be an integer.
    tension -- Curvature at the known points. 1 is high, 0 normal, -1 is low. Defaults to 0.
    bias    -- Curve attraction (for each segments) toward bundary points. 0 is even, positive is towards first point, negative is towards the second point. Defaults to 0.
    size    -- Table size in samples. Defaults to 8192.
"""

from pyo import ExpTable
"""
ExpTable(list=[(0, 0.0), (8192, 1.0)], exp=10, inverse=True, size=8192)

Construct a table from exponential interpolated segments.

Params:
    list    -- List of tuples indicating location and value of each points in the table. The default, [(0,0.), (8192, 1.)], creates a exponential line from 0.0 at location 0 to 1.0 at the end of the table. Location must be an integer.
    exp     -- Exponent factor. Used to control the slope of the curve. Defaults to 10.
    inverse -- If True, downward slope will be inversed. Useful to create biexponential curves. Defaults to True.
    size    -- Table size in samples. Defaults to 8192.
"""

from pyo import SndTable
"""
SndTable(path=None, chnl=None, start=0, stop=None, initchnls=1)

Transfers data from a soundfile into a function table.

If `chnl` is None, the table will contain as many table streams as
necessary to read all channels of the loaded sound.

Params:
    path      -- Full path name of the sound. The defaults, None, creates an empty table.
    chnl      -- Channel number to read in. The count starts at 0 (first channel is is 0, second is 1 and so on). Available at initialization time only. The default (None) reads all channels.
    start     -- Begins reading at `start` seconds into the file. Available at initialization time only. Defaults to 0.
    stop      -- Stops reading at `stop` seconds into the file. Available at initialization time only. The default (None) means the end of the file.
    initchnls -- Number of channels for an empty table (path=None). Defaults to 1.
"""

from pyo import NewTable
"""
NewTable(length, chnls=1, init=None, feedback=0.0)

Create an empty table ready for recording.

See :py:class:`TableRec` to write samples in the table.

Params:
    length   -- Length of the table in seconds.
    chnls    -- Number of channels that will be handled by the table. Defaults to 1.
    init     -- Initial table. List of list can match the number of channels, otherwise, the list will be loaded in all tablestreams. Defaults to None.
    feedback -- Amount of old data to mix with a new recording. Defaults to 0.0.
"""

from pyo import DataTable
"""
DataTable(size, chnls=1, init=None)

Create an empty table ready for data recording.

See :py:class:`TableRec` to write samples in the table.

Params:
    size  -- Size of the table in samples.
    chnls -- Number of channels that will be handled by the table. Defaults to 1.
    init  -- Initial table. List of list can match the number of channels, otherwise, the list will be loaded in all tablestreams.
"""

from pyo import AtanTable
"""
AtanTable(slope=0.5, size=8192)

Generates an arctangent transfert function.

This table allow the creation of the classic arctangent transfert function,
useful in distortion design. See Lookup object for a simple table lookup
process.

Params:
    slope -- Slope of the arctangent function, between 0 and 1. Defaults to 0.5.
    size  -- Table size in samples. Defaults to 8192.
"""

from pyo import PartialTable
"""
PartialTable(list=[(1, 1), (1.33, 0.5), (1.67, 0.3)], size=65536)

Inharmonic waveform generator.

Generates waveforms made of inharmonic components. Partials are
given as a list of 2-values tuple, where the first one is the
partial number (can be float) and the second one is the strength
of the partial.

The object uses the first two decimal values of each partial to
compute a higher harmonic at a multiple of 100 (so each component
is in reality truly harmonic). If the oscillator has a frequency
divided by 100, the real desired partials will be restituted.

The list:

[(1, 1), (1.1, 0.7), (1.15, 0.5)] will draw a table with:

harmonic 100: amplitude = 1
harmonic 110: amplitude = 0.7
harmonic 115: amplitude = 0.5

To listen to a signal composed of 200, 220 and 230 Hz, one should
declared an oscillator like this (frequency of 200Hz divided by 100):

a = Osc(t, freq=2, mul=0.5).out()

Params:
    list -- List of 2-values tuples. First value is the partial number (float up to two decimal values) and second value is its amplitude (relative to the other harmonics). Defaults to [(1,1), (1.33,0.5),(1.67,0.3)].
    size -- Table size in samples. Because computed harmonics are very high in frequency, the table size must be bigger than a classic HarmTable. Defaults to 65536.
"""

from pyo import PadSynthTable
"""
PadSynthTable(basefreq=440, spread=1, bw=50, bwscl=1, nharms=64, damp=0.7, size=262144)

Generates wavetable with the PadSynth algorithm from Nasca Octavian Paul.

This object generates a wavetable with the PadSynth algorithm describe here:

http://zynaddsubfx.sourceforge.net/doc/PADsynth/PADsynth.htm

This algorithm generates some large wavetables that can be played at
different speeds to get the desired sound. This algorithm describes
only how these wavetables are generated. The result is a perfectly
looped wavetable.

To get the desired pitch from the table, the playback speed must be
`sr / table size`. This speed can be transposed to obtain different
pitches from a single wavetable.

Params:
    basefreq -- The base frequency of the algorithm in Hz. If the spreading factor is near 1.0, this frequency is the fundamental of the spectrum. Defaults to 440.
    spread   -- The spreading factor for the harmonics. Each harmonic real frequency is computed as `basefreq * pow(n, spread)` where `n` is the harmonic order. Defaults to 1.
    bw       -- The bandwidth of the first harmonic in cents. The bandwidth allows to control the harmonic profile using a gaussian distribution (bell shape). Defaults to 50.
    bwscl    -- The bandswidth scale specifies how much the bandwidth of the harmonic increase according to its frequency. Defaults to 1.
    nharms   -- The number of harmonics in the generated wavetable. Higher numbers of harmonics take more time to generate the wavetable. Defaults to 64.
    damp     -- The amplitude damping factor specifies how much the amplitude of the harmonic decrease according to its order. It uses a simple power serie, `amp = pow(damp, n)` where `n` is the harmonic order. Defaults to 0.7.
    size     -- Table size in samples. Must be a power-of-two, usually a big one! Defaults to 262144.
"""

from pyo import SharedTable
"""
SharedTable(name, create, size)

Create an inter-process shared memory table.

This table uses the given name to open an internal shared memory
object, used as the data memory of the table. Two or more tables
from different processes, if they use the same name, can read and
write to the same memory space.

"""
