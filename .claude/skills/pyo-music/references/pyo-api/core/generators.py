"""Oscillators and noise sources -- the raw signal generators. All defined in pyo/lib/generators.py."""

__all__ = ['Sine', 'FastSine', 'SineLoop', 'Phasor', 'Input', 'Noise', 'PinkNoise', 'BrownNoise', 'FM', 'CrossFM', 'Blit', 'Rossler', 'Lorenz', 'ChenLee', 'LFO', 'SumOsc', 'SuperSaw', 'RCOsc']

from pyo import Sine
"""
Sine(freq=1000, phase=0, mul=1, add=0)

A simple sine wave oscillator.

Params:
    freq  -- Frequency in cycles per second. Defaults to 1000.
    phase -- Phase of sampling, expressed as a fraction of a cycle (0 to 1). Defaults to 0.
"""

from pyo import FastSine
"""
FastSine(freq=1000, initphase=0.0, quality=1, mul=1, add=0)

A fast sine wave approximation using the formula of a parabola.

This object implements two sin approximations that are even faster
than a linearly interpolated table lookup. With `quality` set to 1,
the approximation is more accurate but also more expensive on the CPU
(still cheaper than a Sine object). With `quality` = 0, the algorithm
gives a worse approximation of the sin function but it is very fast
(and well suitable for generating LFO).

Params:
    freq      -- Frequency in cycles per second. Defaults to 1000.
    initphase -- Initial phase of the oscillator, between 0 and 1. Available at initialization time only. Defaults to 0.
    quality   -- Sets the approximation quality. 1 is more accurate but also more expensive on the CPU. 0 is a cheaper algorithm but is very fast. Defaults to 1.
"""

from pyo import SineLoop
"""
SineLoop(freq=1000, feedback=0, mul=1, add=0)

A simple sine wave oscillator with feedback.

The oscillator output, multiplied by `feedback`, is added to the position
increment and can be used to control the brightness of the oscillator.

Params:
    freq     -- Frequency in cycles per second. Defaults to 1000.
    feedback -- Amount of the output signal added to position increment, between 0 and 1. Controls the brightness. Defaults to 0.
"""

from pyo import Phasor
"""
Phasor(freq=100, phase=0, mul=1, add=0)

A simple phase incrementor.

Output is a periodic ramp from 0 to 1.

Params:
    freq  -- Frequency in cycles per second. Defaults to 100.
    phase -- Phase of sampling, expressed as a fraction of a cycle (0 to 1). Defaults to 0.
"""

from pyo import Input
"""
Input(chnl=0, mul=1, add=0)

Read from a numbered channel in an external audio signal.

Params:
    chnl -- Input channel to read from. Defaults to 0.
"""

from pyo import Noise
"""
Noise(mul=1, add=0)

A white noise generator.

"""

from pyo import PinkNoise
"""
PinkNoise(mul=1, add=0)

A pink noise generator.

Paul Kellet's implementation of pink noise generator.

This is an approximation to a -10dB/decade filter using a weighted sum
of first order filters. It is accurate to within +/-0.05dB above 9.2Hz
(44100Hz sampling rate).

"""

from pyo import BrownNoise
"""
BrownNoise(mul=1, add=0)

A brown noise generator.

The spectrum of a brown noise has a power density which decreases 6 dB
per octave with increasing frequency (density proportional to 1/f^2).

"""

from pyo import FM
"""
FM(carrier=100, ratio=0.5, index=5, mul=1, add=0)

A simple frequency modulation generator.

Implements frequency modulation synthesis based on Chowning's algorithm.

Params:
    carrier -- Carrier frequency in cycles per second. Defaults to 100.
    ratio   -- A factor that, when multiplied by the `carrier` parameter, gives the modulator frequency. Defaults to 0.5.
    index   -- The modulation index. This value multiplied by the modulator frequency gives the modulator amplitude. Defaults to 5.
"""

from pyo import CrossFM
"""
CrossFM(carrier=100, ratio=0.5, ind1=2, ind2=2, mul=1, add=0)

Cross frequency modulation generator.

Frequency modulation synthesis where the output of both oscillators
modulates the frequency of the other one.

Params:
    carrier -- Carrier frequency in cycles per second. Defaults to 100.
    ratio   -- A factor that, when multiplied by the `carrier` parameter, gives the modulator frequency. Defaults to 0.5.
    ind1    -- The carrier index. This value multiplied by the carrier frequency gives the carrier amplitude for modulating the modulation oscillator frequency. Defaults to 2.
    ind1    -- The modulation index. This value multiplied by the modulation frequency gives the modulation amplitude for modulating the carrier oscillator frequency. Defaults to 2.
"""

from pyo import Blit
"""
Blit(freq=100, harms=40, mul=1, add=0)

Band limited impulse train synthesis.

Impulse train generator with control over the number of harmonics
in the spectrum, which gives oscillators with very low aliasing.

Params:
    freq  -- Frequency in cycles per second. Defaults to 100.
    harms -- Number of harmonics in the generated spectrum. Defaults to 40.
"""

from pyo import Rossler
"""
Rossler(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)

Chaotic attractor for the Rossler system.

The Rossler attractor is a system of three non-linear ordinary differential
equations. These differential equations define a continuous-time dynamical
system that exhibits chaotic dynamics associated with the fractal properties
of the attractor.

Params:
    pitch -- Controls the speed, in the range 0 -> 1, of the variations. With values below 0.2, this object can be used as a low frequency oscillator (LFO) and above 0.2, it will generate a broad spectrum noise with harmonic peaks. Defaults to 0.25.
    chaos -- Controls the chaotic behavior, in the range 0 -> 1, of the oscillator. 0 means nearly periodic while 1 is totally chaotic. Defaults to 0.5. stereo, boolean, optional If True, 2 streams will be generated, one with the X variable signal of the algorithm and a second composed of the Y variable signal of the algorithm. These two signal are strongly related in their frequency spectrum but the Y signal is out-of-phase by approximatly 180 degrees. Useful to create alternating LFOs. Available at initialization only. Defaults to False.
"""

from pyo import Lorenz
"""
Lorenz(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)

Chaotic attractor for the Lorenz system.

The Lorenz attractor is a system of three non-linear ordinary differential
equations. These differential equations define a continuous-time dynamical
system that exhibits chaotic dynamics associated with the fractal properties
of the attractor.

Params:
    pitch -- Controls the speed, in the range 0 -> 1, of the variations. With values below 0.2, this object can be used as a low frequency oscillator (LFO) and above 0.2, it will generate a broad spectrum noise with harmonic peaks. Defaults to 0.25.
    chaos -- Controls the chaotic behavior, in the range 0 -> 1, of the oscillator. 0 means nearly periodic while 1 is totally chaotic. Defaults to 0.5 stereo, boolean, optional If True, 2 streams will be generated, one with the X variable signal of the algorithm and a second composed of the Y variable signal of the algorithm. These two signal are strongly related in their frequency spectrum but the Y signal is out-of-phase by approximatly 180 degrees. Useful to create alternating LFOs. Available at initialization only. Defaults to False.
"""

from pyo import ChenLee
"""
ChenLee(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)

Chaotic attractor for the Chen-Lee system.

The ChenLee attractor is a system of three non-linear ordinary differential
equations. These differential equations define a continuous-time dynamical
system that exhibits chaotic dynamics associated with the fractal properties
of the attractor.

Params:
    pitch -- Controls the speed, in the range 0 -> 1, of the variations. With values below 0.2, this object can be used as a low frequency oscillator (LFO) and above 0.2, it will generate a broad spectrum noise with harmonic peaks. Defaults to 0.25.
    chaos -- Controls the chaotic behavior, in the range 0 -> 1, of the oscillator. 0 means nearly periodic while 1 is totally chaotic. Defaults to 0.5 stereo, boolean, optional If True, 2 streams will be generated, one with the X variable signal of the algorithm and a second composed of the Y variable signal of the algorithm. These two signal are strongly related in their frequency spectrum but the Y signal is slightly out-of-phase. Useful to create alternating LFOs. Available at initialization only. Defaults to False.
"""

from pyo import LFO
"""
LFO(freq=100, sharp=0.5, type=0, mul=1, add=0)

Band-limited Low Frequency Oscillator with different wave shapes.

Params:
    freq  -- Oscillator frequency in cycles per second. The frequency is internally clamped between 0.00001 and sr/4. Defaults to 100.
    sharp -- Sharpness factor between 0 and 1. Sharper waveform results in more harmonics in the spectrum. Defaults to 0.5.
    type  -- Waveform type. eight possible values : 0. Saw up (default) 1. Saw down 2. Square 3. Triangle 4. Pulse 5. Bipolar pulse 6. Sample and hold 7. Modulated Sine
"""

from pyo import SumOsc
"""
SumOsc(freq=100, ratio=0.5, index=0.5, mul=1, add=0)

Discrete summation formulae to produce complex spectra.

This object implements a discrete summation formulae taken from
the paper 'The synthesis of complex audio spectra by means of
discrete summation formulae' by James A. Moorer. The formulae
used is of this form:

(sin(theta) - a * sin(theta - beta)) / (1 + a**2 - 2 * a * cos(beta))

where 'theta' and 'beta' are periodic functions and 'a' is
the modulation index, providing control over the damping of
the partials.

The resulting sound is related to the family of modulation
techniques but this formulae express 'one-sided' spectra,
useful to avoid aliasing from the negative frequencies.

Params:
    freq  -- Base frequency in cycles per second. Defaults to 100.
    ratio -- A factor used to stretch or compress the partial serie by manipulating the frequency of the modulation oscillator. Integer ratios give harmonic spectra. Defaults to 0.5.
    index -- Damping of successive partials, between 0 and 1. With a value of 0.5, each partial is 6dB lower than the previous partial. Defaults to 0.5.
"""

from pyo import SuperSaw
"""
SuperSaw(freq=100, detune=0.5, bal=0.7, mul=1, add=0)

Roland JP-8000 Supersaw emulator.

This object implements an emulation of the Roland JP-8000 Supersaw algorithm.
The shape of the waveform is produced from 7 sawtooth oscillators detuned
against each other over a period of time. It allows control over the depth
of the detuning and the balance between central and sideband oscillators.

Params:
    freq   -- Frequency in cycles per second. Defaults to 100.
    detune -- Depth of the detuning, between 0 and 1. 0 means all oscillators are tuned to the same frequency and 1 means sideband oscillators are at maximum detuning regarding the central frequency. Defaults to 0.5.
    bal    -- Balance between central oscillator and sideband oscillators. A value of 0 outputs only the central oscillator while a value of 1 gives a mix of all oscillators with the central one lower than the sidebands. Defaults to 0.7.
"""

from pyo import RCOsc
"""
RCOsc(freq=100, sharp=0.25, mul=1, add=0)

Waveform aproximation of a RC circuit.

A RC circuit is a capacitor and a resistor in series, giving a logarithmic
growth followed by an exponential decay.

Params:
    freq  -- Frequency in cycles per second. Defaults to 100.
    sharp -- Slope of the attack and decay of the waveform, between 0 and 1. A value of 0 gives a triangular waveform and 1 gives almost a square wave. Defaults to 0.25.
"""
