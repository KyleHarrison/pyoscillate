"""Filters -- band-shaping, resonant, and IR-based processors. All defined in pyo/lib/filters.py."""

__all__ = ['Biquad', 'Biquadx', 'Biquada', 'EQ', 'Tone', 'Atone', 'Port', 'DCBlock', 'BandSplit', 'FourBand', 'MultiBand', 'Hilbert', 'Allpass', 'Allpass2', 'Phaser', 'Vocoder', 'IRWinSinc', 'IRAverage', 'IRPulse', 'IRFM', 'SVF', 'SVF2', 'Average', 'Reson', 'Resonx', 'ButLP', 'ButHP', 'ButBP', 'ButBR', 'MoogLP', 'ComplexRes']

from pyo import Biquad
"""
Biquad(input, freq=1000, q=1, type=0, mul=1, add=0)

A sweepable general purpose biquadratic digital filter.

Params:
    input -- Input signal to process.
    freq  -- Cutoff or center frequency of the filter. Defaults to 1000.
    q     -- Q of the filter, defined (for bandpass filters) as freq/bandwidth. Should be between 1 and 500. Defaults to 1.
    type  -- Filter type. Five possible values : 0. lowpass (default) 1. highpass 2. bandpass 3. bandstop 4. allpass
"""

from pyo import Biquadx
"""
Biquadx(input, freq=1000, q=1, type=0, stages=4, mul=1, add=0)

A multi-stages sweepable general purpose biquadratic digital filter.

Biquadx is equivalent to a filter consisting of more layers of Biquad
with the same arguments, serially connected. It is faster than using
a large number of instances of the Biquad object, It uses less memory
and allows filters with sharper cutoff.

Params:
    input  -- Input signal to process.
    freq   -- Cutoff or center frequency of the filter. Defaults to 1000.
    q      -- Q of the filter, defined (for bandpass filters) as freq/bandwidth. Should be between 1 and 500. Defaults to 1.
    type   -- Filter type. Five possible values : 0. lowpass (default) 1. highpass 2. bandpass 3. bandstop 4. allpass
    stages -- The number of filtering stages in the filter stack. Defaults to 4.
"""

from pyo import Biquada
"""
Biquada(input, b0=0.005066, b1=0.010132, b2=0.005066, a0=1.070997, a1=-1.979735, a2=0.929003, mul=1, add=0)

A general purpose biquadratic digital filter (floating-point arguments).

A digital biquad filter is a second-order recursive linear filter, containing
two poles and two zeros. Biquada is a "Direct Form 1" implementation of a Biquad
filter:

y[n] = ( b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2] ) / a0

This object is directly controlled via the six coefficients, as floating-point
values or audio stream, of the filter. There is no clipping of the values given as
coefficients, so, unless you know what you do, it is recommended to use the Biquad
object, which is controlled with frequency, Q and type arguments.

The default values of the object give a lowpass filter with a 1000 Hz cutoff frequency.

Params:
    input -- Input signal to process.
    b0    -- Amplitude of the current sample. Defaults to 0.005066.
    b1    -- Amplitude of the first input sample delayed. Defaults to 0.010132.
    b2    -- Amplitude of the second input sample delayed. Defaults to 0.005066.
    a0    -- Overall gain coefficient. Defaults to 1.070997.
    a1    -- Amplitude of the first output sample delayed. Defaults to -1.979735.
    a2    -- Amplitude of the second output sample delayed. Defaults to 0.929003.
"""

from pyo import EQ
"""
EQ(input, freq=1000, q=1, boost=-3.0, type=0, mul=1, add=0)

Equalizer filter.

EQ is a biquadratic digital filter designed for equalization. It
provides peak/notch and lowshelf/highshelf filters for building
parametric equalizers.

Params:
    input -- Input signal to process.
    freq  -- Cutoff or center frequency of the filter. Defaults to 1000.
    q     -- Q of the filter, defined as freq/bandwidth. Should be between 1 and 500. Defaults to 1.
    boost -- Gain, expressed in dB, to add or remove at the center frequency. Default to -3.
    type  -- Filter type. Three possible values : 0. peak/notch (default) 1. lowshelf 2. highshelf
"""

from pyo import Tone
"""
Tone(input, freq=1000, mul=1, add=0)

A first-order recursive low-pass filter with variable frequency response.

Params:
    input -- Input signal to process.
    freq  -- Cutoff frequency of the filter in hertz. Default to 1000.
"""

from pyo import Atone
"""
Atone(input, freq=1000, mul=1, add=0)

A first-order recursive high-pass filter with variable frequency response.

Params:
    input -- Input signal to process.
    freq  -- Cutoff frequency of the filter in hertz. Default to 1000.
"""

from pyo import Port
"""
Port(input, risetime=0.05, falltime=0.05, init=0, mul=1, add=0)

Exponential portamento.

Perform an exponential portamento on an audio signal with
different rising and falling times.

Params:
    input    -- Input signal to process.
    risetime -- Time to reach upward value in seconds. Defaults to 0.05.
    falltime -- Time to reach downward value in seconds. Defaults to 0.05.
    init     -- Initial state of the internal memory. Available at intialization time only. Defaults to 0.
"""

from pyo import DCBlock
"""
DCBlock(input, mul=1, add=0)

Implements the DC blocking filter.

Params:
    input -- Input signal to process.
"""

from pyo import BandSplit
"""
BandSplit(input, num=6, min=20, max=20000, q=1, mul=1, add=0)

Splits an input signal into multiple frequency bands.

The input signal will be separated into `num` bands between `min`
and `max` frequencies using second-order bandpass filters. Each
band will then be assigned to an independent audio stream.
Useful for multiband processing.

Params:
    input -- Input signal to process.
    num   -- Number of frequency bands created. Available at initialization time only. Defaults to 6.
    min   -- Lowest frequency. Available at initialization time only. Defaults to 20.
    max   -- Highest frequency. Available at initialization time only. Defaults to 20000.
    q     -- Q of the filters, defined as center frequency / bandwidth. Should be between 1 and 500. Defaults to 1.
"""

from pyo import FourBand
"""
FourBand(input, freq1=150, freq2=500, freq3=2000, mul=1, add=0)

Splits an input signal into four frequency bands.

The input signal will be separated into 4 bands around `freqs`
arguments using fourth-order Linkwitz-Riley lowpass and highpass
filters. Each band will then be assigned to an independent audio
stream. The sum of the four bands reproduces the same signal as
the `input`. Useful for multiband processing.

Params:
    input -- Input signal to process.
    freq1 -- First crossover frequency. First band will contain signal from 0 Hz to `freq1` Hz. Defaults to 150.
    freq2 -- Second crossover frequency. Second band will contain signal from `freq1` Hz to `freq2`. `freq2` is the lower limit of the third band signal. Defaults to 500.
    freq3 -- Third crossover frequency. It's the upper limit of the third band signal and fourth band will contain signal from `freq3` to sr/2. Defaults to 2000.
"""

from pyo import MultiBand
"""
MultiBand(input, num=8, mul=1, add=0)

Splits an input signal into multiple frequency bands.

The input signal will be separated into `num` logarithmically spaced
frequency bands using fourth-order Linkwitz-Riley lowpass and highpass
filters. Each band will then be assigned to an independent audio
stream. The sum of all bands reproduces the same signal as the `input`.
Useful for multiband processing.

User-defined frequencies can be assigned with the `setFrequencies()` method.

Params:
    input -- Input signal to process.
    num   -- Number of frequency bands created, between 2 and 16. Available at initialization time only. Defaults to 8.
"""

from pyo import Hilbert
"""
Hilbert(input, mul=1, add=0)

Hilbert transform.

Hilbert is an IIR filter based implementation of a broad-band 90 degree
phase difference network. The outputs of hilbert have an identical
frequency response to the input (i.e. they sound the same), but the two
outputs have a constant phase difference of 90 degrees, plus or minus some
small amount of error, throughout the entire frequency range. The outputs
are in quadrature.

Hilbert is useful in the implementation of many digital signal processing
techniques that require a signal in phase quadrature. The real part corresponds
to the cosine output of hilbert, while the imaginary part corresponds to the
sine output. The two outputs have a constant phase difference throughout the
audio range that corresponds to the phase relationship between cosine and sine waves.

Params:
    input -- Input signal to process.
"""

from pyo import Allpass
"""
Allpass(input, delay=0.01, feedback=0, maxdelay=1, mul=1, add=0)

Delay line based allpass filter.

Allpass is based on the combination of feedforward and feedback comb
filter. This kind of filter is often used in simple digital reverb
implementations.

Params:
    input    -- Input signal to process.
    delay    -- Delay time in seconds. Defaults to 0.01.
    feedback -- Amount of output signal sent back into the delay line. Defaults to 0.
    maxdelay -- Maximum delay length in seconds. Available only at initialization. Defaults to 1.
"""

from pyo import Allpass2
"""
Allpass2(input, freq=1000, bw=100, mul=1, add=0)

Second-order phase shifter allpass.

This kind of filter is used in phaser implementation. The signal
of this filter, when added to original sound, creates a notch in
the spectrum at frequencies that are in phase opposition.

Params:
    input -- Input signal to process.
    freq  -- Center frequency of the filter. Defaults to 1000.
    bw    -- Bandwidth of the filter in Hertz. Defaults to 100.
"""

from pyo import Phaser
"""
Phaser(input, freq=1000, spread=1.1, q=10, feedback=0, num=8, mul=1, add=0)

Multi-stages second-order phase shifter allpass filters.

Phaser implements `num` number of second-order allpass filters.

Params:
    input    -- Input signal to process.
    freq     -- Center frequency of the first notch. Defaults to 1000.
    spread   -- Spreading factor for upper notch frequencies. Defaults to 1.1.
    q        -- Q of the filter as center frequency / bandwidth. Defaults to 10.
    feedback -- Amount of output signal which is fed back into the input of the allpass chain. Defaults to 0.
    num      -- The number of allpass stages in series. Defines the number of notches in the spectrum. Defaults to 8. Available at initialization only.
"""

from pyo import Vocoder
"""
Vocoder(input, input2, freq=60, spread=1.25, q=20, slope=0.5, stages=24, mul=1, add=0)

Applies the spectral envelope of a first sound to the spectrum of a second sound.

The vocoder is an analysis/synthesis system, historically used to reproduce
human speech. In the encoder, the first input (spectral envelope) is passed
through a multiband filter, each band is passed through an envelope follower,
and the control signals from the envelope followers are communicated to the
decoder. The decoder applies these (amplitude) control signals to corresponding
filters modifying the second source (exciter).

Params:
    input  -- Spectral envelope. Gives the spectral properties of the bank of filters. For best results, this signal must have a dynamic spectrum, both for amplitudes and frequencies.
    input2 -- Exciter. Spectrum to filter. For best results, this signal must have a broadband spectrum with few amplitude variations.
    freq   -- Center frequency of the first band. This is the base frequency used to compute the upper bands. Defaults to 60.
    spread -- Spreading factor for upper band frequencies. Each band is `freq * pow(order, spread)`, where order is the harmonic rank of the band. Defaults to 1.25.
    q      -- Q of the filters as `center frequency / bandwidth`. Higher values imply more resonance around the center frequency. Defaults to 20.
    slope  -- Time response of the envelope follower. Lower values mean smoother changes, while higher values mean a better time accuracy. Defaults to 0.5.
    stages -- The number of bands in the filter bank. Defines the number of notches in the spectrum. Defaults to 24.
"""

from pyo import IRWinSinc
"""
IRWinSinc(input, freq=1000, bw=500, type=0, order=256, mul=1, add=0)

Windowed-sinc filter using circular convolution.

IRWinSinc uses circular convolution to implement standard filters like
lowpass, highpass, bandreject and bandpass with very flat passband
response and sharp roll-off. User can defined the length, in samples,
of the impulse response, also known as the filter kernel.

Params:
    input -- Input signal to process.
    freq  -- Frequency cutoff for lowpass and highpass and center frequency for bandjrect and bandpass filters, expressed in Hz. Defaults to 1000.
    bw    -- Bandwidth, expressed in Hertz, for bandreject and bandpass filters. Defaults to 500.
    type  -- Filter type. Four possible values : 0. lowpass (default) 1. highpass 2. bandreject 3. bandpass
    order -- Length, in samples, of the filter kernel used for convolution. Available at initialization time only. Defaults to 256. This value must be even. Higher is the order and sharper is the roll-off of the filter, but it is also more expensive to compute.
"""

from pyo import IRAverage
"""
IRAverage(input, order=256, mul=1, add=0)

Moving average filter using circular convolution.

IRAverage uses circular convolution to implement an average filter. This
filter is designed to reduce the noise in the input signal while keeping
as much as possible the step response of the original signal. User can
defined the length, in samples, of the impulse response, also known as
the filter kernel. This controls the ratio of removed noise vs the fidelity
of the original step response.

Params:
    input -- Input signal to process.
    order -- Length, in samples, of the filter kernel used for convolution. Available at initialization time only. Defaults to 256. This value must be even. A high order will reduced more noise and will have a higher damping effect on the step response, but it is also more expensive to compute.
"""

from pyo import IRPulse
"""
IRPulse(input, freq=500, bw=2500, type=0, order=256, mul=1, add=0)

Comb-like filter using circular convolution.

IRPulse uses circular convolution to implement standard comb-like
filters consisting of an harmonic series with fundamental `freq` and
a comb filter with the first notch at `bw` frequency. The `type`
parameter defines variations of this pattern. User can defined the length,
in samples, of the impulse response, also known as the filter kernel.

Params:
    input -- Input signal to process.
    freq  -- Fundamental frequency of the spikes in the filter's spectrum, expressed in Hertz. Defaults to 500.
    bw    -- Frequency, expressed in Hertz, of the first notch in the comb filtering. Defaults to 2500.
    type  -- Filter type. Four possible values : 0. Pulse & comb (default) 1. Pulse & comb & lowpass 2. Pulse (odd harmonics) & comb 3. Pulse (odd harmonics) & comb & lowpass
    order -- Length, in samples, of the filter kernel used for convolution. Available at initialization time only. Defaults to 256. This value must be even. Higher is the order and sharper is the roll-off of the filter, but it is also more expensive to compute.
"""

from pyo import IRFM
"""
IRFM(input, carrier=1000, ratio=0.5, index=3, order=256, mul=1, add=0)

Filters a signal with a frequency modulation spectrum using circular convolution.

IRFM uses circular convolution to implement filtering with a frequency
modulation spectrum. User can defined the length, in samples, of the
impulse response, also known as the filter kernel. The higher the `order`,
the narrower the bandwidth around each of the FM components.

Params:
    input   -- Input signal to process.
    carrier -- Carrier frequency in cycles per second. Defaults to 1000.
    ratio   -- A factor that, when multiplied by the `carrier` parameter, gives the modulator frequency. Defaults to 0.5.
    index   -- The modulation index. This value multiplied by the modulator frequency gives the modulator amplitude. Defaults to 3.
    order   -- Length, in samples, of the filter kernel used for convolution. Available at initialization time only. Defaults to 256. This value must be even. Higher is the order and sharper is the roll-off of the filter, but it is also more expensive to compute.
"""

from pyo import SVF
"""
SVF(input, freq=1000, q=1, type=0, mul=1, add=0)

Fourth-order state variable filter allowing continuous change of the filter type.

Params:
    input -- Input signal to process.
    freq  -- Cutoff or center frequency of the filter. Defaults to 1000. Because this filter becomes unstable at higher frequencies, the `freq` parameter is limited to one-sixth of the sampling rate.
    q     -- Q of the filter, defined (for bandpass filters) as freq/bandwidth. Should be between 0.5 and 50. Defaults to 1.
    type  -- This value, in the range 0 to 1, controls the filter type crossfade on the continuum lowpass-bandpass-highpass. - 0.0 = lowpass (default) - 0.5 = bandpass - 1.0 = highpass
"""

from pyo import SVF2
"""
SVF2(input, freq=1000, q=1, shelf=-3, type=0, mul=1, add=0)

Second-order state variable filter allowing continuous change of the filter type.

This 2-pole multimode filter is described in the book "The Art of VA Filter Design"
by Vadim Zavalishin (version 2.1.0 when this object was created).

Several filter types are available with continuous change between them. The default
order (controlled with the `type` argument) is:

    - lowpass
    - bandpass
    - highpass
    - highshelf
    - bandshelf
    - lowshelf
    - notch
    - peak
    - allpass
    - unit gain bandpass

The filter types order can be changed with the `setOrder` method. The first filter type
is always copied at the end of the order list so we can create a glitch-free loop of
filter types with a Phasor given as `type` argument. Ex.:

"""

from pyo import Average
"""
Average(input, size=10, mul=1, add=0)

Moving average filter.

As the name implies, the moving average filter operates by averaging a number
of points from the input signal to produce each point in the output signal.
In spite of its simplicity, the moving average filter is optimal for
a common task: reducing random noise while retaining a sharp step response.

Params:
    input -- Input signal to process.
    size  -- Filter kernel size, which is the number of samples used in the moving average. Default to 10.
"""

from pyo import Reson
"""
Reson(input, freq=1000, q=1, mul=1, add=0)

A second-order resonant bandpass filter.

Reson implements a classic resonant bandpass filter, as described in:

Dodge, C., Jerse, T., "Computer Music, Synthesis, Composition and Performance".

Reson uses less CPU than the equivalent filter with a Biquad object.

Params:
    input -- Input signal to process.
    freq  -- Center frequency of the filter. Defaults to 1000.
    q     -- Q of the filter, defined as freq/bandwidth. Should be between 1 and 500. Defaults to 1.
"""

from pyo import Resonx
"""
Resonx(input, freq=1000, q=1, stages=4, mul=1, add=0)

A multi-stages second-order resonant bandpass filter.

Resonx implements a stack of the classic resonant bandpass filter, as described in:

Dodge, C., Jerse, T., "Computer Music, Synthesis, Composition and Performance".

Resonx is equivalent to a filter consisting of more layers of Reson
with the same arguments, serially connected. It is faster than using
a large number of instances of the Reson object, it uses less memory
and allows filters with sharper cutoff.

Params:
    input  -- Input signal to process.
    freq   -- Center frequency of the filter. Defaults to 1000.
    q      -- Q of the filter, defined as freq/bandwidth. Should be between 1 and 500. Defaults to 1.
    stages -- The number of filtering stages in the filter stack. Defaults to 4.
"""

from pyo import ButLP
"""
ButLP(input, freq=1000, mul=1, add=0)

A second-order Butterworth lowpass filter.

ButLP implements a second-order IIR Butterworth lowpass filter,
which has a maximally flat passband and a very good precision and
stopband attenuation.

Params:
    input -- Input signal to process.
    freq  -- Cutoff frequency of the filter in hertz. Default to 1000.
"""

from pyo import ButHP
"""
ButHP(input, freq=1000, mul=1, add=0)

A second-order Butterworth highpass filter.

ButHP implements a second-order IIR Butterworth highpass filter,
which has a maximally flat passband and a very good precision and
stopband attenuation.

Params:
    input -- Input signal to process.
    freq  -- Cutoff frequency of the filter in hertz. Default to 1000.
"""

from pyo import ButBP
"""
ButBP(input, freq=1000, q=1, mul=1, add=0)

A second-order Butterworth bandpass filter.

ButBP implements a second-order IIR Butterworth bandpass filter,
which has a maximally flat passband and a very good precision and
stopband attenuation.

Params:
    input -- Input signal to process.
    freq  -- Center frequency of the filter. Defaults to 1000.
    q     -- Q of the filter, defined as freq/bandwidth. Should be between 1 and 500. Defaults to 1.
"""

from pyo import ButBR
"""
ButBR(input, freq=1000, q=1, mul=1, add=0)

A second-order Butterworth band-reject filter.

ButBR implements a second-order IIR Butterworth band-reject filter,
which has a maximally flat passband and a very good precision and
stopband attenuation.

Params:
    input -- Input signal to process.
    freq  -- Center frequency of the filter. Defaults to 1000.
    q     -- Q of the filter, defined as freq/bandwidth. Should be between 1 and 500. Defaults to 1.
"""

from pyo import MoogLP
"""
MoogLP(input, freq=1000, res=0, mul=1, add=0)

A fourth-order resonant lowpass filter.

Digital approximation of the Moog VCF, giving a decay of 24dB/oct.

Params:
    input -- Input signal to process.
    freq  -- Cutoff frequency of the filter. Defaults to 1000.
    res   -- Amount of Resonance of the filter, usually between 0 (no resonance) and 1 (medium resonance). Self-oscillation occurs when the resonance is >= 1. Can go up to 10. Defaults to 0.
"""

from pyo import ComplexRes
"""
ComplexRes(input, freq=1000, decay=0.25, mul=1, add=0)

Complex one-pole resonator filter.

ComplexRes implements a resonator derived from a complex
multiplication, which is very similar to a digital filter.

Params:
    input -- Input signal to process.
    freq  -- Center frequency of the filter. Defaults to 1000.
    decay -- Decay time, in seconds, for the filter's response. Defaults to 0.25.
"""
