"""Audio Signal Analysis -- measure a signal instead of generating or
shaping one (amplitude, pitch, brightness, onsets). Not used by this
project yet.
"""

__all__ = ['Follower', 'Yin', 'RMS', 'Centroid', 'AttackDetector']

from pyo import Follower

"""
Follower(input, freq=10, mul=1, add=0)

Envelope follower -- outputs the continuous mean amplitude of an input
signal, useful for envelope-linked modulation of other parameters.

Params:
    input -- Signal to track.
    freq  -- Cutoff frequency of the internal smoothing filter, in Hz.
             Default 10.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Yin

"""
Yin(input, tolerance=0.2, minfreq=40, maxfreq=1000, cutoff=1000,
    mul=1, add=0)

Pitch tracker using the Yin algorithm -- estimates the fundamental
frequency of an input signal.

Params:
    input     -- Signal to analyze.
    tolerance -- Threshold controlling sensitivity of pitch detection.
                 Default 0.2.
    minfreq   -- Lowest frequency to detect, in Hz. Default 40.
    maxfreq   -- Highest frequency to detect, in Hz. Default 1000.
    cutoff    -- Cutoff frequency of an internal smoothing filter, in Hz.
                 Default 1000.
    mul       -- Output multiplier. Default 1.
    add       -- Output additive value. Default 0.
"""

from pyo import RMS

"""
RMS(input, mul=1, add=0)

Returns the RMS (root-mean-square) value of a signal -- an overall
loudness measure.

Params:
    input -- Signal to analyze.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Centroid

"""
Centroid(input, mul=1, add=0)

Computes the spectral centroid of a signal -- a rough measure of
perceived brightness.

Params:
    input -- Signal to analyze.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import AttackDetector

"""
AttackDetector(input, deltime=0.005, cutoff=10, maxthresh=3, minthresh=-30,
                reltime=0.1, mul=1, add=0)

Detects onsets/attacks in an audio signal by watching for a sharp rise in
amplitude.

Params:
    deltime   -- Delta time between amplitude comparisons, in seconds.
                 Default 0.005.
    cutoff    -- Cutoff frequency of an internal smoothing filter, in Hz.
                 Default 10.
    maxthresh -- Maximum threshold in dB for an attack to register.
                 Default 3.
    minthresh -- Minimum threshold in dB for an attack to register.
                 Default -30.
    reltime   -- Minimum time between two detected attacks, in seconds.
                 Default 0.1.
    mul       -- Output multiplier. Default 1.
    add       -- Output additive value. Default 0.
"""
