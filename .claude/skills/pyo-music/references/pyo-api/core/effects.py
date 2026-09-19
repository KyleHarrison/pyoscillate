"""Effects processors -- distortion, delay, reverb, chorus, pitch shift. All defined in pyo/lib/effects.py."""

__all__ = ['Disto', 'Delay', 'SDelay', 'Waveguide', 'AllpassWG', 'Freeverb', 'Convolve', 'WGVerb', 'Chorus', 'Harmonizer', 'Delay1', 'STRev', 'SmoothDelay', 'FreqShift']

from pyo import Disto
"""
Disto(input, drive=0.75, slope=0.5, mul=1, add=0)

Kind of Arc tangent distortion.

Apply a kind of arc tangent distortion with controllable drive, followed
by a one pole lowpass filter, to the input signal.

As of version 0.8.0, this object use a simple but very efficient (4x
faster than tanh or atan2 functions) waveshaper formula.

The waveshaper algorithm is:

    y[n] = (1 + k) * x[n] / (1 + k * abs(x[n]))

where:

    k = (2 * drive) / (1 - drive)

Params:
    input -- Input signal to process.
    drive -- Amount of distortion applied to the signal, between 0 and 1. Defaults to 0.75.
    slope -- Slope of the lowpass filter applied after distortion, between 0 and 1. Defaults to 0.5.
"""

from pyo import Delay
"""
Delay(input, delay=0.25, feedback=0, maxdelay=1, mul=1, add=0)

Sweepable recursive delay.

Params:
    input    -- Input signal to delayed.
    delay    -- Delay time in seconds. Defaults to 0.25.
    feedback -- Amount of output signal sent back into the delay line. Defaults to 0.
    maxdelay -- Maximum delay length in seconds. Available only at initialization. Defaults to 1.
"""

from pyo import SDelay
"""
SDelay(input, delay=0.25, maxdelay=1, mul=1, add=0)

Simple delay without interpolation.

Params:
    input    -- Input signal to delayed.
    delay    -- Delay time in seconds. Defaults to 0.25.
    maxdelay -- Maximum delay length in seconds. Available only at initialization. Defaults to 1.
"""

from pyo import Waveguide
"""
Waveguide(input, freq=100, dur=10, minfreq=20, mul=1, add=0)

Basic waveguide model.

This waveguide model consisting of one delay-line with a simple
lowpass filtering and lagrange interpolation.

Params:
    input   -- Input signal to process.
    freq    -- Frequency, in cycle per second, of the waveguide (i.e. the inverse of delay time). Defaults to 100.
    dur     -- Duration, in seconds, for the waveguide to drop 40 dB below it's maxima. Defaults to 10.
    minfreq -- Minimum possible frequency, used to initialized delay length. Available only at initialization. Defaults to 20.
"""

from pyo import AllpassWG
"""
AllpassWG(input, freq=100, feed=0.95, detune=0.5, minfreq=20, mul=1, add=0)

Out of tune waveguide model with a recursive allpass network.

This waveguide model consisting of one delay-line with a 3-stages recursive
allpass filter which made the resonances of the waveguide out of tune.

Params:
    input   -- Input signal to process.
    freq    -- Frequency, in cycle per second, of the waveguide (i.e. the inverse of delay time). Defaults to 100.
    feed    -- Amount of output signal (between 0 and 1) sent back into the delay line. Defaults to 0.95.
    detune  -- Control the depth of the allpass delay-line filter, i.e. the depth of the detuning. Should be in the range 0 to 1. Defaults to 0.5.
    minfreq -- Minimum possible frequency, used to initialized delay length. Available only at initialization. Defaults to 20.
"""

from pyo import Freeverb
"""
Freeverb(input, size=0.5, damp=0.5, bal=0.5, mul=1, add=0)

Implementation of Jezar's Freeverb.

Freeverb is a reverb unit generator based on Jezar's public domain
C++ sources, composed of eight parallel comb filters, followed by four
allpass units in series. Filters on each stream are slightly detuned
in order to create multi-channel effects.

Params:
    input -- Input signal to process.
    size  -- Controls the length of the reverb, between 0 and 1. A higher value means longer reverb. Defaults to 0.5.
    damp  -- High frequency attenuation, between 0 and 1. A higher value will result in a faster decay of the high frequency range. Defaults to 0.5.
    bal   -- Balance between wet and dry signal, between 0 and 1. 0 means no reverb. Defaults to 0.5.
"""

from pyo import Convolve
"""
Convolve(input, table, size, mul=1, add=0)

Implements filtering using circular convolution.

A circular convolution is defined as the integral of the product of two
functions after one is reversed and shifted.

Params:
    input -- Input signal to process.
    table -- Table containning the impulse response.
    size  -- Length, in samples, of the convolution. Available at initialization time only. If the table changes during the performance, its size must egal or greater than this value. If greater only the first `size` samples will be used.
"""

from pyo import WGVerb
"""
WGVerb(input, feedback=0.5, cutoff=5000, bal=0.5, mul=1, add=0)

8 delay lines mono FDN reverb.

8 delay lines FDN reverb, with feedback matrix based upon physical
modeling scattering junction of 8 lossless waveguides of equal
characteristic impedance.

Params:
    input    -- Input signal to process.
    feedback -- Amount of output signal sent back into the delay lines. Defaults to 0.5. 0.6 gives a good small "live" room sound, 0.8 a small hall, and 0.9 a large hall.
    cutoff   -- cutoff frequency of simple first order lowpass filters in the feedback loop of delay lines, in Hz. Defaults to 5000.
    bal      -- Balance between wet and dry signal, between 0 and 1. 0 means no reverb. Defaults to 0.5.
"""

from pyo import Chorus
"""
Chorus(input, depth=1, feedback=0.25, bal=0.5, mul=1, add=0)

8 modulated delay lines chorus processor.

A chorus effect occurs when individual sounds with roughly the same timbre and
nearly (but never exactly) the same pitch converge and are perceived as one.

Params:
    input    -- Input signal to process.
    depth    -- Chorus depth, between 0 and 5. Defaults to 1.
    feedback -- Amount of output signal sent back into the delay lines. Defaults to 0.25.
    bal      -- Balance between wet and dry signals, between 0 and 1. 0 means no chorus. Defaults to 0.5.
"""

from pyo import Harmonizer
"""
Harmonizer(input, transpo=-7.0, feedback=0, winsize=0.1, mul=1, add=0)

Generates harmonizing voices in synchrony with its audio input.

Params:
    input    -- Input signal to process.
    transpo  -- Transposition factor in semitone. Defaults to -7.0.
    feedback -- Amount of output signal sent back into the delay line. Defaults to 0.
    winsize  -- Window size in seconds (max = 1.0). Defaults to 0.1.
"""

from pyo import Delay1
"""
Delay1(input, mul=1, add=0)

Delays a signal by one sample.

Params:
    input -- Input signal to process.
"""

from pyo import STRev
"""
STRev(input, inpos=0.5, revtime=1, cutoff=5000, bal=0.5, roomSize=1, firstRefGain=-3, mul=1, add=0)

Stereo reverb.

Stereo reverb based on WGVerb (8 delay line FDN reverb). A mono
input will produce two audio streams, left and right channels.
Therefore, a stereo input will produce four audio streams, left
and right channels for each input channel. Position of input
streams can be set with the `inpos` argument. To achieve a stereo
reverb, delay line lengths are slightly differents on both channels,
but also, pre-delays length and filter cutoff of both channels will
be affected to reflect the input position.

Params:
    input        -- Input signal to process.
    inpos        -- Position of the source, between 0 and 1. 0 means fully left and 1 means fully right. Defaults to 0.5.
    revtime      -- Duration, in seconds, of the reverberated sound, defined as the time needed to the sound to drop 40 dB below its peak. Defaults to 1.
    cutoff       -- cutoff frequency, in Hz, of a first order lowpass filters in the feedback loop of delay lines. Defaults to 5000.
    bal          -- Balance between wet and dry signal, between 0 and 1. 0 means no reverb. Defaults to 0.5.
    roomSize     -- Delay line length scaler, between 0.25 and 4. Values higher than 1 make the delay lines longer and simulate larger rooms. Defaults to 1.
    firstRefGain -- Gain, in dB, of the first reflexions of the room. Defaults to -3.
"""

from pyo import SmoothDelay
"""
SmoothDelay(input, delay=0.25, feedback=0, crossfade=0.05, maxdelay=1, mul=1, add=0)

Artifact free sweepable recursive delay.

SmoothDelay implements a delay line that does not produce
clicks or pitch shifting when the delay time is changing.

Params:
    input     -- Input signal to delayed.
    delay     -- Delay time in seconds. Defaults to 0.25.
    feedback  -- Amount of output signal sent back into the delay line. Defaults to 0.
    crossfade -- Crossfade time, in seconds, between overlaped readers. Defaults to 0.05.
    maxdelay  -- Maximum delay length in seconds. Available only at initialization. Defaults to 1.
"""

from pyo import FreqShift
"""
FreqShift(input, shift=100, mul=1, add=0)

Frequency shifting using single sideband amplitude modulation.

Shifting frequencies means that the input signal can be detuned,
where the harmonic components of the signal are shifted out of
harmonic alignment with each other, e.g. a signal with harmonics at
100, 200, 300, 400 and 500 Hz, shifted up by 50 Hz, will have harmonics
at 150, 250, 350, 450, and 550 Hz.

Params:
    input -- Input signal to process.
    shift -- Amount of shifting in Hertz. Defaults to 100.
"""
