"""Phase vocoder analysis/synthesis and PV-domain processors. All defined in pyo/lib/phasevoc.py."""

__all__ = ['PVAnal', 'PVSynth', 'PVAddSynth', 'PVTranspose', 'PVVerb', 'PVGate', 'PVCross', 'PVMult', 'PVMorph', 'PVFilter', 'PVDelay', 'PVBuffer', 'PVShift', 'PVAmpMod', 'PVFreqMod', 'PVBufLoops', 'PVBufTabLoops', 'PVMix']

from pyo import PVAnal
"""
PVAnal(input, size=1024, overlaps=4, wintype=2, callback=None)

Phase Vocoder analysis object.

PVAnal takes an input sound and performs the phase vocoder
analysis on it. This results in two streams, one for the bin's
magnitudes and the other for the bin's true frequencies. These
two streams are used by the PVxxx object family to transform
the input signal using spectral domain algorithms. The last
object in the phase vocoder chain must be a PVSynth to perform
the spectral to time domain conversion.

Params:
    input    -- Input signal to process.
    size     -- FFT size. Must be a power of two greater than 4. Defaults to 1024. The FFT size is the number of samples used in each analysis frame.
    overlaps -- The number of overlaped analysis block. Must be a power of two. Defaults to 4. More overlaps can greatly improved sound quality synthesis but it is also more CPU expensive.
    wintype  -- Shape of the envelope used to filter each input frame. Possible shapes are: 0. rectangular (no windowing) 1. Hamming 2. Hanning (default) 3. Bartlett (triangular) 4. Blackman 3-term 5. Blackman-Harris 4-term 6. Blackman-Harris 7-term 7. Tuckey (alpha = 0.66) 8. Sine (half-sine window)
    callback -- If not None (default), this function will be called with the result of the analysis at the end of every overlap. The function will receive two arguments, a list of floats for both the magnitudes and the frequencies. The signature is: callback(magnitudes, frequencies) If you analyse a multi-channel signal, you should pass a list of callables, one per channel to analyse.
"""

from pyo import PVSynth
"""
PVSynth(input, wintype=2, mul=1, add=0)

Phase Vocoder synthesis object.

PVSynth takes a PyoPVObject as its input and performed
the spectral to time domain conversion on it. This step
converts phase vocoder magnitude and true frequency's
streams back to a real signal.

Params:
    input   -- Phase vocoder streaming object to process.
    wintype -- Shape of the envelope used to filter each input frame. Possible shapes are: 0. rectangular (no windowing) 1. Hamming 2. Hanning (default) 3. Bartlett (triangular) 4. Blackman 3-term 5. Blackman-Harris 4-term 6. Blackman-Harris 7-term 7. Tuckey (alpha = 0.66) 8. Sine (half-sine window)
"""

from pyo import PVAddSynth
"""
PVAddSynth(input, pitch=1, num=100, first=0, inc=1, mul=1, add=0)

Phase Vocoder additive synthesis object.

PVAddSynth takes a PyoPVObject as its input and resynthesize
the real signal using the magnitude and true frequency's
streams to control amplitude and frequency envelopes of an
oscillator bank.

Params:
    input -- Phase vocoder streaming object to process.
    pitch -- Transposition factor. Defaults to 1.
    num   -- Number of oscillators used to synthesize the output sound. Defaults to 100.
    first -- The first bin to synthesize, starting from 0. Defaults to 0.
    inc   -- Starting from bin `first`, resynthesize bins `inc` apart. Defaults to 1.
"""

from pyo import PVTranspose
"""
PVTranspose(input, transpo=1)

Transpose the frequency components of a pv stream.

Params:
    input   -- Phase vocoder streaming object to process.
    transpo -- Transposition factor. Defaults to 1.
"""

from pyo import PVVerb
"""
PVVerb(input, revtime=0.75, damp=0.75)

Spectral domain reverberation.

Params:
    input   -- Phase vocoder streaming object to process.
    revtime -- Reverberation factor, between 0 and 1. Defaults to 0.75.
    damp    -- High frequency damping factor, between 0 and 1. 1 means no damping and 0 is the most damping. Defaults to 0.75.
"""

from pyo import PVGate
"""
PVGate(input, thresh=-20, damp=0.0, inverse=False)

Spectral gate.

Params:
    input   -- Phase vocoder streaming object to process.
    thresh  -- Threshold factor in dB. Bins below that threshold will be scaled by `damp` factor. Defaults to -20.
    damp    -- Damping factor for low amplitude bins. Defaults to 0.
    inverse -- If True, the damping factor will be applied to the bins with amplitude above the given threshold. If False, the damping factor is applied to bins with amplitude below the given threshold. Defaults to False.
"""

from pyo import PVCross
"""
PVCross(input, input2, fade=1)

Performs cross-synthesis between two phase vocoder streaming object.

The amplitudes from `input` and `input2` (scaled by `fade` argument)
are applied to the frequencies of `input`.

Params:
    input  -- Phase vocoder streaming object to process. Frequencies from this pv stream are used to compute the output signal.
    input2 -- Phase vocoder streaming object which gives the second set of magnitudes. Frequencies from this pv stream are not used.
    fade   -- Scaling factor for the output amplitudes, between 0 and 1. 0 means amplitudes from `input` and 1 means amplitudes from `input2`. Defaults to 1.
"""

from pyo import PVMult
"""
PVMult(input, input2)

Multiply magnitudes from two phase vocoder streaming object.

Params:
    input  -- Phase vocoder streaming object to process. Frequencies from this pv stream are used to compute the output signal.
    input2 -- Phase vocoder streaming object which gives the second set of magnitudes. Frequencies from this pv stream are not used.
"""

from pyo import PVMorph
"""
PVMorph(input, input2, fade=0.5)

Performs spectral morphing between two phase vocoder streaming object.

According to `fade` argument, the amplitudes from `input` and `input2`
are interpolated linearly while the frequencies are interpolated
exponentially.

Params:
    input  -- Phase vocoder streaming object which gives the first set of magnitudes and frequencies.
    input2 -- Phase vocoder streaming object which gives the second set of magnitudes and frequencies.
    fade   -- Scaling factor for the output amplitudes and frequencies, between 0 and 1. 0 is `input` and 1 in `input2`. Defaults to 0.5.
"""

from pyo import PVFilter
"""
PVFilter(input, table, gain=1, mode=0)

Spectral filter.

PVFilter filters frequency components of a pv stream
according to the shape drawn in the table given in
argument.

Params:
    input -- Phase vocoder streaming object to process.
    table -- Table containing the filter shape. If the table length is smaller than fftsize/2, remaining bins will be set to 0.
    gain  -- Gain of the filter applied to the input spectrum. Defaults to 1.
    mode  -- Table scanning mode. Defaults to 0. If 0, bin indexes outside table size are set to 0. If 1, bin indexes are scaled over table length.
"""

from pyo import PVDelay
"""
PVDelay(input, deltable, feedtable, maxdelay=1.0, mode=0)

Spectral delays.

PVDelay applies different delay times and feedbacks for
each bin of a phase vocoder analysis. Delay times and
feedbacks are specified with PyoTableObjects.

Params:
    input     -- Phase vocoder streaming object to process.
    deltable  -- Table containing delay times, as integer multipliers of the FFT hopsize (fftsize / overlaps). If the table length is smaller than fftsize/2, remaining bins will be set to 0.
    feedtable -- Table containing feedback values, between -1 and 1. If the table length is smaller than fftsize/2, remaining bins will be set to 0.
    maxdelay  -- Maximum delay time in seconds. Available at initialization time only. Defaults to 1.0.
    mode      -- Tables scanning mode. Defaults to 0. If 0, bin indexes outside table size are set to 0. If 1, bin indexes are scaled over table length.
"""

from pyo import PVBuffer
"""
PVBuffer(input, index, pitch=1.0, length=1.0)

Phase vocoder buffer and playback with transposition.

PVBuffer keeps `length` seconds of pv analysis in memory
and gives control on playback position and transposition.

Params:
    input  -- Phase vocoder streaming object to process.
    index  -- Playback position, as audio stream, normalized between 0 and 1.
    pitch  -- Transposition factor. Defaults to 1.
    length -- Memory length in seconds. Defaults to 1.0.
"""

from pyo import PVShift
"""
PVShift(input, shift=0)

Spectral domain frequency shifter.

PVShift linearly moves the analysis bins by the amount, in Hertz,
specified by the the `shift` argument.

Params:
    input -- Phase vocoder streaming object to process.
    shift -- Frequency shift factor. Defaults to 0.
"""

from pyo import PVAmpMod
"""
PVAmpMod(input, basefreq=1, spread=0, shape=0)

Performs frequency independent amplitude modulations.

PVAmpMod modulates the magnitude of each bin of a pv
stream with an independent oscillator. `basefreq` and
`spread` are used to derive the frequency of each
modulating oscillator.

Internally, the following operations are applied to
derive oscillator frequencies (`i` is the bin number):

    spread = spread * 0.001 + 1.0

    f_i = basefreq * pow(spread, i)

Params:
    input    -- Phase vocoder streaming object to process.
    basefreq -- Base modulation frequency, in Hertz. Defaults to 1.
    spread   -- Spreading factor for oscillator frequencies, between -1 and 1. 0 means every oscillator has the same frequency.
    shape    -- Modulation oscillator waveform. Possible shapes are: 0. Sine (default) 1. Sawtooth 2. Ramp (inverse sawtooth) 3. Square 4. Triangle 5. Brown Noise 6. Pink Noise 7. White Noise
"""

from pyo import PVFreqMod
"""
PVFreqMod(input, basefreq=1, spread=0, depth=0.1, shape=0)

Performs frequency independent frequency modulations.

PVFreqMod modulates the frequency of each bin of a pv
stream with an independent oscillator. `basefreq` and
`spread` are used to derive the frequency of each
modulating oscillator.

Internally, the following operations are applied to
derive oscillator frequencies (`i` is the bin number):

    spread = spread * 0.001 + 1.0

    f_i = basefreq * pow(spread, i)

Params:
    input    -- Phase vocoder streaming object to process.
    basefreq -- Base modulation frequency, in Hertz. Defaults to 1.
    spread   -- Spreading factor for oscillator frequencies, between -1 and 1. 0 means every oscillator has the same frequency.
    depth    -- Amplitude of the modulating oscillators, between 0 and 1. Defaults to 0.1.
    shape    -- Modulation oscillator waveform. Possible shapes are: 0. Sine (default) 1. Sawtooth 2. Ramp (inverse sawtooth) 3. Square 4. Triangle 5. Brown Noise 6. Pink Noise 7. White Noise
"""

from pyo import PVBufLoops
"""
PVBufLoops(input, low=1.0, high=1.0, mode=0, length=1.0)

Phase vocoder buffer with bin independent speed playback.

PVBufLoops keeps `length` seconds of pv analysis in memory
and gives control on playback position independently for
every frequency bin.

Params:
    input  -- Phase vocoder streaming object to process.
    low    -- Lowest bin speed factor. Defaults to 1.0.
    high   -- Highest bin speed factor. Defaults to 1.0.
    mode   -- Speed distribution algorithm. Available algorithms are: 0. linear, line between `low` and `high` (default) 1. exponential, exponential line between `low` and `high` 2. logarithmic, logarithmic line between `low` and `high` 3. random, uniform random between `low` and `high` 4. rand expon min, exponential random from `low` to `high` 5. rand expon max, exponential random from `high` to `low` 6. rand bi-expon, bipolar exponential random between `low` and `high`
    length -- Memory length in seconds. Available at initialization time only. Defaults to 1.0.
"""

from pyo import PVBufTabLoops
"""
PVBufTabLoops(input, speed, length=1.0)

Phase vocoder buffer with bin independent speed playback.

PVBufTabLoops keeps `length` seconds of pv analysis in memory
and gives control on playback position, using a PyoTableObject,
independently for every frequency bin.

Params:
    input  -- Phase vocoder streaming object to process.
    speed  -- Table which specify the speed of bin playback readers.
    length -- Memory length in seconds. Available at initialization time only. Defaults to 1.0.
"""

from pyo import PVMix
"""
PVMix(input, input2)

Mix the most prominent components from two phase vocoder streaming objects.

Params:
    input  -- Phase vocoder streaming object 1.
    input2 -- Phase vocoder streaming object 2.
"""
