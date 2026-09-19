"""FFT-domain analysis/resynthesis and frequency-domain processors. All defined in pyo/lib/fourier.py."""

__all__ = ['FFT', 'IFFT', 'CarToPol', 'PolToCar', 'FrameDelta', 'FrameAccum', 'Vectral', 'CvlVerb', 'IFFTMatrix']

from pyo import FFT
"""
FFT(input, size=1024, overlaps=4, wintype=2)

Fast Fourier Transform.

FFT analyses an input signal and converts it into the spectral
domain. Three audio signals are sent out of the object, the
`real` part, from bin 0 (DC) to bin size/2 (Nyquist), the
`imaginary` part, from bin 0 to bin size/2-1, and the bin
number, an increasing count from 0 to size-1. `real` and
`imaginary` buffer's left samples  up to size-1 are filled
with zeros. See notes below for an example of how to retrieve
each signal component.

Params:
    input    -- Input signal to process.
    size     -- FFT size. Must be a power of two greater than 4. The FFT size is the number of samples used in each analysis frame. Defaults to 1024.
    overlaps -- The number of overlaped analysis block. Must be a positive integer. More overlaps can greatly improved sound quality synthesis but it is also more CPU expensive. Defaults to 4.
    wintype  -- Shape of the envelope used to filter each input frame. Possible shapes are : 0. rectangular (no windowing) 1. Hamming 2. Hanning 3. Bartlett (triangular) 4. Blackman 3-term 5. Blackman-Harris 4-term 6. Blackman-Harris 7-term 7. Tuckey (alpha = 0.66) 8. Sine (half-sine window)
"""

from pyo import IFFT
"""
IFFT(inreal, inimag, size=1024, overlaps=4, wintype=2, mul=1, add=0)

Inverse Fast Fourier Transform.

IFFT takes a signal in the spectral domain and converts it to a
real audio signal using an inverse fast fourier transform.
IFFT takes two signals in input, the `real` and `imaginary` parts
of an FFT analysis and returns the corresponding real signal.
These signals must correspond to `real` and `imaginary` parts
from an FFT object.

Params:
    inreal   -- Input `real` signal.
    inimag   -- Input `imaginary` signal.
    size     -- FFT size. Must be a power of two greater than 4. The FFT size is the number of samples used in each analysis frame. This value must match the `size` attribute of the former FFT object. Defaults to 1024.
    overlaps -- The number of overlaped analysis block. Must be a positive integer. More overlaps can greatly improved sound quality synthesis but it is also more CPU expensive. This value must match the `overlaps` atribute of the former FFT object. Defaults to 4.
    wintype  -- Shape of the envelope used to filter each output frame. Possible shapes are : 0. rectangular (no windowing) 1. Hamming 2. Hanning 3. Bartlett (triangular) 4. Blackman 3-term 5. Blackman-Harris 4-term 6. Blackman-Harris 7-term 7. Tuckey (alpha = 0.66) 8. Sine (half-sine window)
"""

from pyo import CarToPol
"""
CarToPol(inreal, inimag, mul=1, add=0)

Performs the cartesian to polar conversion.

The Cartesian system locates points on a plane by measuring the  horizontal and
vertical distances from an arbitrary origin to a point.  These are usually denoted
as a pair of values (X,Y).

The Polar system locates the point by measuring the straight line distance, usually
denoted by R, from the origin to the point and the angle of an imaginary line from
the origin to the point measured counterclockwise from the positive X axis.

Params:
    inreal -- Real input signal.
    inimag -- Imaginary input signal.
"""

from pyo import PolToCar
"""
PolToCar(inmag, inang, mul=1, add=0)

Performs the polar to cartesian conversion.

The Polar system locates the point by measuring the straight line distance, usually
denoted by R, from the origin to the point and the angle of an imaginary line from
the origin to the point measured counterclockwise from the positive X axis.

The Cartesian system locates points on a plane by measuring the  horizontal and
vertical distances from an arbitrary origin to a point.  These are usually denoted
as a pair of values (X,Y).

Params:
    inmag -- Magintude input signal.
    inang -- Angle input signal.
"""

from pyo import FrameDelta
"""
FrameDelta(input, framesize=1024, overlaps=4, mul=1, add=0)

Computes the phase differences between successive frames.

The difference between the phase values of successive FFT frames for a given bin
determines the exact frequency of the energy centered in that bin. This is often
known as the phase difference (and sometimes also referred to as phase derivative
or instantaneous frequency if it's been subjected to a few additional calculations).

In order to reconstruct a plausible playback of re-ordered FFT frames, we need to
calculate the phase difference between successive frames and use it to construct a
`running phase` (by simply summing the successive differences with FrameAccum) for
the output FFT frames.

Params:
    input     -- Phase input signal, usually from an FFT analysis.
    framesize -- Frame size in samples. Usually the same as the FFT size. Defaults to 1024.
    overlaps  -- Number of overlaps in incomming signal. Usually the same as the FFT overlaps. Defaults to 4.
"""

from pyo import FrameAccum
"""
FrameAccum(input, framesize=1024, overlaps=4, mul=1, add=0)

Accumulates the phase differences between successive frames.

The difference between the phase values of successive FFT frames for a given bin
determines the exact frequency of the energy centered in that bin. This is often
known as the phase difference (and sometimes also referred to as phase derivative
or instantaneous frequency if it's been subjected to a few additional calculations).

In order to reconstruct a plausible playback of re-ordered FFT frames, we need to
calculate the phase difference between successive frames, with FrameDelta, and use
it to construct a `running phase` (by simply summing the successive differences) for
the output FFT frames.

Params:
    input     -- Phase input signal.
    framesize -- Frame size in samples. Usually same as the FFT size. Defaults to 1024.
    overlaps  -- Number of overlaps in incomming signal. Usually the same as the FFT overlaps. Defaults to 4.
"""

from pyo import Vectral
"""
Vectral(input, framesize=1024, overlaps=4, up=1.0, down=0.7, damp=0.9, mul=1, add=0)

Performs magnitude smoothing between successive frames.

Vectral applies filter with different coefficients for increasing
and decreasing magnitude vectors, bin by bin.

Params:
    input     -- Magnitude input signal, usually from an FFT analysis.
    framesize -- Frame size in samples. Usually the same as the FFT size. Defaults to 1024.
    overlaps  -- Number of overlaps in incomming signal. Usually the same as the FFT overlaps. Defaults to 4.
    up        -- Filter coefficient for increasing bins, between 0 and 1. Lower values results in a longer ramp time for bin magnitude. Defaults to 1.
    down      -- Filter coefficient for decreasing bins, between 0 and 1. Lower values results in a longer decay time for bin magnitude. Defaults to 0.7
    damp      -- High frequencies damping factor, between 0 and 1. Lower values mean more damping. Defaults to 0.9.
"""

from pyo import CvlVerb
"""
CvlVerb(input, impulse='/Users/Kyle/Projects/pyoscillate/.venv/lib/python3.10/site-packages/pyo/lib/snds/IRMediumHallStereo.wav', bal=0.25, size=1024, mul=1, add=0)

Convolution based reverb.

CvlVerb implements convolution based on a uniformly partitioned overlap-save
algorithm. This object can be used to convolve an input signal with an
impulse response soundfile to simulate real acoustic spaces.

Params:
    input   -- Input signal to process.
    impulse -- Path to the impulse response soundfile. The file must have the same sampling rate as the server to get the proper convolution. Available at initialization time only. Defaults to 'IRMediumHallStereo.wav', located in pyo SNDS_PATH folder.
    size    -- The size in samples of each partition of the impulse file. Small size means smaller latency but more computation time. If not a power-of-2, the object will find the next power-of-2 greater and use that as the actual partition size. This value must also be greater or equal than the server's buffer size. Available at initialization time only. Defaults to 1024.
    bal     -- Balance between wet and dry signal, between 0 and 1. 0 means no reverb. Defaults to 0.25.
"""

from pyo import IFFTMatrix
"""
IFFTMatrix(matrix, index, phase, size=1024, overlaps=4, wintype=2, mul=1, add=0)

Inverse Fast Fourier Transform with a PyoMatrixObject as input.

IFFTMatrix takes a matrix as input and read it as it is a sonogram.
On the current column, given by the `index` argument, the cells
at the bottom represent the lower frequencies of the spectrum and
the cells at the top, the higher frequencies of the spectrum.

Because a matrix is usually used to store bipolar signals (with the
amplitude between -1 and 1), a cell value of -1 represent a frequency
bin with no amplitude and a cell value of 1 represents the maximum
amplitude for the given frequency bin.

The instantaneous angle value (in polar coordinates) of each frequency
bin is given by the current sample in the audio signal given to the
`phase` argument. Generally speaking, the more noisy this signal is,
the more energy a bin with a positive amplitude value will have.

Params:
    matrix   -- The matrix used like a sonogram.
    index    -- Normalized horizontal position in the matrix. 0 is the first column and 1 is the last. Positions between two columns are interpolated. If this signal is a Phasor, the matrix is read from left to right.
    phase    -- Instantaneous angle value used to compute the inverse FFT. Try different signals like white noise or an oscillator with a frequency slightly detuned in relation to the frequency of the FFT (sr / fftsize).
    size     -- FFT size. Must be a power of two greater than 4. The FFT size is the number of samples used in each analysis frame. This value must match the `size` attribute of the former FFT object. Defaults to 1024.
    overlaps -- The number of overlaped analysis block. Must be a positive integer. More overlaps can greatly improved sound quality synthesis but it is also more CPU expensive. This value must match the `overlaps` atribute of the former FFT object. Defaults to 4.
    wintype  -- Shape of the envelope used to filter each output frame. Possible shapes are : 0. rectangular (no windowing) 1. Hamming 2. Hanning 3. Bartlett (triangular) 4. Blackman 3-term 5. Blackman-Harris 4-term 6. Blackman-Harris 7-term 7. Tuckey (alpha = 0.66) 8. Sine (half-sine window)
"""
