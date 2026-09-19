"""Signal analysis/follower objects -- envelope followers, pitch/onset detection, spectral display. All defined in pyo/lib/analysis.py."""

__all__ = ['Follower', 'Follower2', 'ZCross', 'Yin', 'Centroid', 'AttackDetector', 'Spectrum', 'Scope', 'PeakAmp', 'RMS']

from pyo import Follower
"""
Follower(input, freq=20, mul=1, add=0)

Envelope follower.

Output signal is the continuous mean amplitude of an input signal.

Params:
    input -- Input signal to process.
    freq  -- Cutoff frequency of the filter in hertz. Default to 20.
"""

from pyo import Follower2
"""
Follower2(input, risetime=0.01, falltime=0.1, mul=1, add=0)

Envelope follower with different attack and release times.

Output signal is the continuous mean amplitude of an input signal.

Params:
    input    -- Input signal to process.
    risetime -- Time to reach upward value in seconds. Default to 0.01.
    falltime -- Time to reach downward value in seconds. Default to 0.1.
"""

from pyo import ZCross
"""
ZCross(input, thresh=0.0, mul=1, add=0)

Zero-crossing counter.

Output signal is the number of zero-crossing occured during each
buffer size, normalized between 0 and 1.

Params:
    input  -- Input signal to process.
    thresh -- Minimum amplitude difference allowed between adjacent samples to be included in the zeros count. Defaults to 0.
"""

from pyo import Yin
"""
Yin(input, tolerance=0.2, minfreq=40, maxfreq=1000, cutoff=1000, winsize=1024, mul=1, add=0)

Pitch tracker using the Yin algorithm.

Pitch tracker using the Yin algorithm based on the implementation in C of aubio.
This algorithm was developped by A. de Cheveigne and H. Kawahara and published in

de Cheveigne, A., Kawahara, H. (2002) 'YIN, a fundamental frequency estimator for
speech and music', J. Acoust. Soc. Am. 111, 1917-1930.

The audio output of the object is the estimated frequency, in Hz, of the input sound.

Params:
    input     -- Input signal to process.
    tolerance -- Parameter for minima selection, between 0 and 1. Defaults to 0.2.
    minfreq   -- Minimum estimated frequency in Hz. Frequency below this threshold will be ignored. Defaults to 40.
    maxfreq   -- Maximum estimated frequency in Hz. Frequency above this threshold will be ignored. Defaults to 1000.
    cutoff    -- Cutoff frequency, in Hz, of the lowpass filter applied on the input sound. Defaults to 1000. The lowpass filter helps the algorithm to detect the fundamental frequency by filtering higher harmonics.
    winsize   -- Size, in samples, of the analysis window. Must be higher that two period of the lowest desired frequency. Available at initialization time only. Defaults to 1024.
"""

from pyo import Centroid
"""
Centroid(input, size=1024, mul=1, add=0)

Computes the spectral centroid of an input signal.

Output signal is the spectral centroid, in Hz, of the input signal.
It indicates where the "center of mass" of the spectrum is. Perceptually,
it has a robust connection with the impression of "brightness" of a sound.

Centroid does its computation with two overlaps, so a new output value
comes every half of the FFT window size.

Params:
    input -- Input signal to process.
    size  -- Size, as a power-of-two, of the FFT used to compute the centroid. Available at initialization time only. Defaults to 1024.
"""

from pyo import AttackDetector
"""
AttackDetector(input, deltime=0.005, cutoff=10, maxthresh=3, minthresh=-30, reltime=0.1, mul=1, add=0)

Audio signal onset detection.

AttackDetector analyses an audio signal in input and output a trigger each
time an onset is detected. An onset is a sharp amplitude rising while the
signal had previously fall below a minimum threshold. Parameters must be
carefully tuned depending on the nature of the analysed signal and the level
of the background noise.

Params:
    input     -- Input signal to process.
    deltime   -- Delay time, in seconds, between previous and current rms analysis to compare. Defaults to 0.005.
    cutoff    -- Cutoff frequency, in Hz, of the amplitude follower's lowpass filter. Defaults to 10. Higher values are more responsive and also more likely to give false onsets.
    maxthresh -- Attack threshold in positive dB (current rms must be higher than previous rms + maxthresh to be reported as an attack). Defaults to 3.0.
    minthresh -- Minimum threshold in dB (signal must fall below this threshold to allow a new attack to be detected). Defaults to -30.0.
    reltime   -- Time, in seconds, to wait before reporting a new attack. Defaults to 0.1.
"""

from pyo import Spectrum
"""
Spectrum(input, size=1024, wintype=2, function=None, wintitle='Spectrum')

Spectrum analyzer and display.

Spectrum measures the magnitude of an input signal versus frequency
within a user defined range. It can show both magnitude and frequency
on linear or logarithmic scale.

Params:
    input    -- Input signal to process.
    size     -- FFT size. Must be a power of two greater than 4. The FFT size is the number of samples used in each analysis frame. Defaults to 1024.
    wintype  -- Shape of the envelope used to filter each input frame. Possible shapes are : 0. rectangular (no windowing) 1. Hamming 2. Hanning 3. Bartlett (triangular) 4. Blackman 3-term 5. Blackman-Harris 4-term 6. Blackman-Harris 7-term 7. Tuckey (alpha = 0.66) 8. Sine (half-sine window)
    function -- If set, this function will be called with magnitudes (as list of lists, one list per channel). Useful if someone wants to save the analysis data into a text file. Defaults to None.
    wintitle -- GUI window title. Defaults to "Spectrum".
"""

from pyo import Scope
"""
Scope(input, length=0.05, gain=0.67, function=None, wintitle='Scope')

Oscilloscope - audio waveform display.

Oscilloscopes are used to observe the change of an electrical
signal over time.

Params:
    input    -- Input signal to process.
    length   -- Length, in seconds, of the displayed window. Can't be a list. Defaults to 0.05.
    gain     -- Linear gain applied to the signal to be displayed. Can't be a list. Defaults to 0.67.
    function -- If set, this function will be called with samples (as list of lists, one list per channel). Useful if someone wants to save the analysis data into a text file. Defaults to None.
    wintitle -- GUI window title. Defaults to "Scope".
"""

from pyo import PeakAmp
"""
PeakAmp(input, function=None, mul=1, add=0)

Peak amplitude follower.

Output signal is the continuous peak amplitude of an input signal.
A new peaking value is computed every buffer size. If `function`
argument is not None, it should be a function that will be called
periodically with a variable-length argument list containing
the peaking values of all object's streams. Useful for meter drawing.
Function definition must look like this:

"""

from pyo import RMS
"""
RMS(input, function=None, mul=1, add=0)

Returns the RMS (Root-Mean-Square) value of a signal.

Output signal is the continuous rms of an input signal. A new rms
value is computed every buffer size. If `function` argument is not
None, it should be a function that will be called periodically
with a variable-length argument list containing the rms values
of all object's streams. Useful for meter drawing. Function
definition must look like this:

"""
