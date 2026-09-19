"""8. Filters & effects -- process an existing signal.

Take a signal in, transform it (spectrally or texturally), pass a modified
signal out. Sits downstream of a generator, upstream of dynamics/output.
"""

__all__ = ['Biquad', 'Tone', 'Disto', 'Freeverb', 'Delay', 'Chorus']

from pyo import Biquad

"""
Biquad(input, freq=1000, q=1, type=0, mul=1, add=0)

A sweepable general-purpose biquadratic filter (lowpass/highpass/bandpass/
bandstop/allpass/etc, selected by `type`).

Params:
    input -- Input signal to filter.
    freq  -- Cutoff/center frequency in Hz. Default 1000.
    q     -- Resonance/Q factor. Default 1.
    type  -- Filter type (0=lowpass, 1=highpass, 2=bandpass, ...). Default 0.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Tone

"""
Tone(input, freq=1000, mul=1, add=0)

A first-order recursive lowpass filter -- gentle high-frequency rolloff.

Params:
    input -- Input signal to filter.
    freq  -- Cutoff frequency in Hz. Default 1000.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Disto

"""
Disto(input, drive=0.75, slope=0.5, mul=1, add=0)

Arc-tangent style distortion/waveshaping.

Params:
    input -- Input signal to distort.
    drive -- Amount of distortion, 0-1. Default 0.75.
    slope -- Lowpass slope applied after distortion, 0-1. Default 0.5.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Freeverb

"""
Freeverb(input, size=0.5, damp=0.5, bal=0.5, mul=1, add=0)

Implementation of Jezar's Freeverb algorithm -- a classic comb/allpass
reverb.

Params:
    input -- Input signal to reverberate.
    size  -- Room size, 0-1. Default 0.5.
    damp  -- High-frequency damping of the tail, 0-1. Default 0.5.
    bal   -- Dry/wet balance, 0 (dry) to 1 (wet). Default 0.5.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Delay

"""
Delay(input, delay=0.25, feedback=0, maxdelay=1, mul=1, add=0)

Sweepable recursive (feedback) delay line.

Params:
    input    -- Input signal to delay.
    delay    -- Delay time in seconds. Default 0.25.
    feedback -- Amount of output fed back into the delay, 0-1. Default 0.
    maxdelay -- Maximum delay time the line can be swept to. Default 1.
    mul      -- Output multiplier. Default 1.
    add      -- Output additive value. Default 0.
"""

from pyo import Chorus

"""
Chorus(input, depth=1, feedback=0.25, bal=0.5, mul=1, add=0)

Eight modulated delay lines run in parallel to create a chorus effect.

Params:
    input    -- Input signal to process.
    depth    -- Modulation depth of the delay lines, 0-5. Default 1.
    feedback -- Feedback amount, 0-1. Default 0.25.
    bal      -- Dry/wet balance, 0 (dry) to 1 (wet). Default 0.5.
    mul      -- Output multiplier. Default 1.
    add      -- Output additive value. Default 0.
"""
