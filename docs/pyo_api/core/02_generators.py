"""2. Signal generators (sources) -- things that produce a raw waveform.

These are your starting sound: oscillators, wavetable players, and noise
sources. Everything downstream (envelopes, filters, dynamics) shapes what
one of these objects produces.
"""

__all__ = ["Sine", "Osc", "LFO", "SuperSaw", "FM", "Noise", "PinkNoise", "BrownNoise"]

from pyo import Sine

"""
Sine(freq=1000, phase=0, mul=1, add=0)

A simple sine wave oscillator.

Params:
    freq  -- Frequency in Hz. Default 1000.
    phase -- Phase of sampling, between 0 and 1. Default 0.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Osc

"""
Osc(table, freq=1000, phase=0, interp=2, mul=1, add=0)

Reads a PyoTableObject's waveform at a given frequency, looping it like a
wavetable oscillator.

Params:
    table  -- The PyoTableObject to read (see 03_tables.py).
    freq   -- Playback frequency in Hz. Default 1000.
    phase  -- Phase of sampling, between 0 and 1. Default 0.
    interp -- Interpolation method (0=none, 1=linear, 2=cosine, 3=cubic).
              Default 2.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import LFO

"""
LFO(freq=100, sharp=0.5, type=0, mul=1, add=0)

Band-limited low frequency oscillator with several wave shapes (saw, square,
triangle, pulse, bipolar pulse, sample-and-hold, modulated sine). Despite
the name it can run at audio rate too -- see 07_modulators.py for its
continuous-modulator role.

Params:
    freq  -- Frequency in Hz. Default 100.
    sharp -- Sharpness factor, 0-1, shapes the waveform's edge. Default 0.5.
    type  -- Waveform type (0=saw up ... 7=modulated sine). Default 0.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import SuperSaw

"""
SuperSaw(freq=100, detune=0.5, bal=0.7, mul=1, add=0)

Roland JP-8000 "Supersaw" emulator: seven detuned sawtooth oscillators
mixed together for a thick, chorused lead/pad sound.

Params:
    freq   -- Base frequency in Hz. Default 100.
    detune -- Depth of the detuning, 0-1. Default 0.5.
    bal    -- Balance between center and detuned oscillators, 0-1.
              Default 0.7.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import FM

"""
FM(carrier=100, ratio=0.5, index=5, mul=1, add=0)

A simple frequency modulation generator (one carrier, one modulator).

Params:
    carrier -- Carrier frequency in Hz. Default 100.
    ratio   -- Modulator/carrier frequency ratio. Default 0.5.
    index   -- Modulation index (brightness of the FM timbre). Default 5.
    mul     -- Output multiplier. Default 1.
    add     -- Output additive value. Default 0.
"""

from pyo import Noise

"""
Noise(mul=1, add=0)

A white noise generator.

Params:
    mul -- Output multiplier. Default 1.
    add -- Output additive value. Default 0.
"""

from pyo import PinkNoise

"""
PinkNoise(mul=1, add=0)

A pink noise generator (equal energy per octave -- darker than white noise).

Params:
    mul -- Output multiplier. Default 1.
    add -- Output additive value. Default 0.
"""

from pyo import BrownNoise

"""
BrownNoise(mul=1, add=0)

A brown/red noise generator (random walk -- darker still than pink noise).

Params:
    mul -- Output multiplier. Default 1.
    add -- Output additive value. Default 0.
"""
