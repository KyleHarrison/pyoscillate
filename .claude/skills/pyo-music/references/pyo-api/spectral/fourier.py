"""Fast Fourier Transform -- convert a signal to/from the frequency domain
for spectral processing. Foundation for the higher-level Phase Vocoder
category (see pvoc.py). Not used by this project yet.
"""

__all__ = ['FFT', 'IFFT', 'PolToCar', 'CvlVerb']

from pyo import FFT

"""
FFT(input, size=1024, overlaps=4, wintype=2)

Analyzes an input signal, producing real/imaginary spectral frames.

Params:
    input    -- Signal to analyze.
    size     -- FFT size in samples (power of 2). Default 1024.
    overlaps -- Number of overlapped analysis windows. Default 4.
    wintype  -- Windowing function (0=rectangular, 1=Hamming, 2=Hanning,
                ...). Default 2.
"""

from pyo import IFFT

"""
IFFT(inreal, inimag, size=1024, overlaps=4, wintype=2)

Converts real/imaginary spectral frames back into a time-domain audio
signal.

Params:
    inreal   -- Real part input (e.g. from FFT).
    inimag   -- Imaginary part input (e.g. from FFT).
    size     -- FFT size in samples, must match the source FFT. Default 1024.
    overlaps -- Number of overlapped windows, must match the source FFT.
                Default 4.
    wintype  -- Windowing function used for reconstruction. Default 2.
"""

from pyo import PolToCar

"""
PolToCar(mag, ang)

Converts polar (magnitude, angle) spectral data to cartesian
(real, imaginary) form.

Params:
    mag -- Magnitude input stream.
    ang -- Angle input stream.
"""

from pyo import CvlVerb

"""
CvlVerb(input, imp=3, size=1024, bal=0.25, mul=1, add=0)

Convolution-based reverb, convolving the input with a built-in or supplied
impulse response.

Params:
    input -- Signal to reverberate.
    imp   -- Impulse response selector (int) or path to a soundfile.
             Default 3.
    size  -- Partition size for the convolution, in samples. Default 1024.
    bal   -- Dry/wet balance, 0 (dry) to 1 (wet). Default 0.25.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""
