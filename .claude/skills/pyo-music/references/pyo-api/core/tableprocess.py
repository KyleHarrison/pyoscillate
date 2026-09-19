"""Objects that read, write, or scan wavetables/soundfiles into an audio signal (table-driven oscillators, granular players, table recorders). All defined in pyo/lib/tableprocess.py."""

__all__ = ['Osc', 'OscLoop', 'OscTrig', 'OscBank', 'TableRead', 'Pulsar', 'Pointer', 'Pointer2', 'TableIndex', 'Lookup', 'TableRec', 'TableWrite', 'TableMorph', 'Granulator', 'TrigTableRec', 'Looper', 'TablePut', 'TableFill', 'Granule', 'TableScale', 'Particle', 'Particle2', 'TableScan']

from pyo import Osc
"""
Osc(table, freq=1000, phase=0, interp=2, mul=1, add=0)

A simple oscillator reading a waveform table.

Params:
    table  -- Table containing the waveform samples.
    freq   -- Frequency in cycles per second. Defaults to 1000.
    phase  -- Phase of sampling, expressed as a fraction of a cycle (0 to 1). Defaults to 0.
    interp -- Choice of the interpolation method. Defaults to 2. 1. no interpolation 2. linear 3. cosinus 4. cubic
"""

from pyo import OscLoop
"""
OscLoop(table, freq=1000, feedback=0, mul=1, add=0)

A simple oscillator with feedback reading a waveform table.

OscLoop reads a waveform table with linear interpolation and feedback control.
The oscillator output, multiplied by `feedback`, is added to the position
increment and can be used to control the brightness of the oscillator.

Params:
    table    -- Table containing the waveform samples.
    freq     -- Frequency in cycles per second. Defaults to 1000.
    feedback -- Amount of the output signal added to position increment, between 0 and 1. Controls the brightness. Defaults to 0.
"""

from pyo import OscTrig
"""
OscTrig(table, trig, freq=1000, phase=0, interp=2, mul=1, add=0)

An oscillator reading a waveform table with sample accurate reset signal.

Params:
    table  -- Table containing the waveform samples.
    trig   -- Trigger signal. Reset the table pointer position to zero on each trig.
    freq   -- Frequency in cycles per second. Defaults to 1000.
    phase  -- Phase of sampling, expressed as a fraction of a cycle (0 to 1). Defaults to 0.
    interp -- Choice of the interpolation method. Defaults to 2. 1. no interpolation 2. linear 3. cosinus 4. cubic
"""

from pyo import OscBank
"""
OscBank(table, freq=100, spread=1, slope=0.9, frndf=1, frnda=0, arndf=1, arnda=0, num=24, fjit=False, mul=1, add=0)

Any number of oscillators reading a waveform table.

OscBank mixes the output of any number of oscillators. The frequencies
of each oscillator is controlled with two parameters, the base frequency
`freq` and a coefficient of expansion `spread`. Frequencies are computed
with the following formula (`n` is the order of the partial):

f_n = freq + freq * spread * n

The frequencies and amplitudes can be modulated by two random generators
with interpolation (each partial have a different set of randoms).

Params:
    table  -- Table containing the waveform samples.
    freq   -- Base frequency in cycles per second. Defaults to 100.
    spread -- Coefficient of expansion used to compute partial frequencies. If `spread` is 0, all partials will be at the base frequency. A value of 1 will generate integer harmonics, a value of 2 will skip even harmonics and non-integer values will generate different series of inharmonic frequencies. Defaults to 1.
    slope  -- specifies the multiplier in the series of amplitude coefficients. This is a power series: the nth partial will have an amplitude of (slope ** n), i.e. strength values trace an exponential curve. Defaults to 1.
    frndf  -- Frequency, in cycle per second, of the frequency modulations. Defaults to 1.
    frnda  -- Maximum frequency deviation (positive and negative) in portion of the partial frequency. A value of 1 means that the frequency can drift from 0 Hz to twice the partial frequency. A value of 0 deactivates the frequency deviations. Defaults to 0.
    arndf  -- Frequency, in cycle per second, of the amplitude modulations. Defaults to 1.
    arnda  -- Amount of amplitude deviation. 0 deactivates the amplitude modulations and 1 gives full amplitude modulations. Defaults to 0.
    num    -- Number of oscillators. Available at initialization only. Defaults to 24.
    fjit   -- If True, a small jitter is added to the frequency of each partial. For a large number of oscillators and a very small `spread`, the periodicity between partial frequencies can cause very strange artefact. Adding a jitter breaks the periodicity. Defaults to False.
"""

from pyo import TableRead
"""
TableRead(table, freq=1, loop=0, interp=2, mul=1, add=0)

Simple waveform table reader.

Read sampled sound from a table, with optional looping mode.

The play() method starts the playback and is not called at the
object creation time.

Params:
    table  -- Table containing the waveform samples.
    freq   -- Frequency in cycles per second. Defaults to 1.
    loop   -- Looping mode, 0 means off, 1 means on. Defaults to 0.
    interp -- Choice of the interpolation method. Defaults to 2. 1. no interpolation 2. linear 3. cosinus 4. cubic
"""

from pyo import Pulsar
"""
Pulsar(table, env, freq=100, frac=0.5, phase=0, interp=2, mul=1, add=0)

Pulsar synthesis oscillator.

Pulsar synthesis produces a train of sound particles called pulsars
that can make rhythms or tones, depending on the fundamental frequency
of the train. Varying the `frac` parameter changes the portion of the
period assigned to the waveform and the portion of the period assigned
to its following silence, but maintain the overall pulsar period. This
results in an effect much like a sweeping band-pass filter.

Params:
    table  -- Table containing the waveform samples.
    env    -- Table containing the envelope samples.
    freq   -- Frequency in cycles per second. Defaults to 100.
    frac   -- Fraction of the whole period (0 -> 1) given to the waveform. The rest will be filled with zeros. Defaults to 0.5.
    phase  -- Phase of sampling, expressed as a fraction of a cycle (0 to 1). Defaults to 0.
    interp -- Choice of the interpolation method. Defaults to 2. 1. no interpolation 2. linear 3. cosinus 4. cubic
"""

from pyo import Pointer
"""
Pointer(table, index, mul=1, add=0)

Table reader with control on the pointer position.

Params:
    table -- Table containing the waveform samples.
    index -- Normalized position in the table between 0 and 1.
"""

from pyo import Pointer2
"""
Pointer2(table, index, interp=4, autosmooth=True, mul=1, add=0)

High quality table reader with control on the pointer position.

Params:
    table      -- Table containing the waveform samples.
    index      -- Normalized position in the table between 0 and 1.
    interp     -- Choice of the interpolation method. Defaults to 4. 1. no interpolation 2. linear 3. cosinus 4. cubic
    autosmooth -- If True, a lowpass filter, following the pitch, is applied on the output signal to reduce the quantization noise produced by very low transpositions. Defaults to True.
"""

from pyo import TableIndex
"""
TableIndex(table, index, mul=1, add=0)

Table reader by sample position without interpolation.

Params:
    table -- Table containing the samples.
    index -- Position in the table, as integer audio stream, between 0 and table's size - 1.
"""

from pyo import Lookup
"""
Lookup(table, index, mul=1, add=0)

Uses table to do waveshaping on an audio signal.

Lookup uses a table to apply waveshaping on an input signal
`index`. The index must be between -1 and 1, it is automatically
scaled between 0 and len(table)-1 and is used as a position
pointer in the table.

Params:
    table -- Table containing the transfert function.
    index -- Audio signal, between -1 and 1, internally converted to be used as the index position in the table.
"""

from pyo import TableRec
"""
TableRec(input, table, fadetime=0)

TableRec is for writing samples into a previously created table.

See `NewTable` to create an empty table.

The play method is not called at the object creation time. It starts
the recording into the table until the table is full. Calling the
play method again restarts the recording and overwrites previously
recorded samples. The stop method stops the recording. Otherwise, the
default behaviour is to record through the end of the table.

Params:
    input    -- Audio signal to write in the table.
    table    -- The table where to write samples.
    fadetime -- Fade time at the beginning and the end of the recording in seconds. Defaults to 0.
"""

from pyo import TableWrite
"""
TableWrite(input, pos, table, mode=0, maxwindow=1024)

TableWrite writes samples into a previously created table.

See `NewTable` to create an empty table.

TableWrite takes samples from its `input` stream and writes
them at a normalized or raw position given by the `pos` stream.
Position must be an audio stream, ie. a PyoObject. This
object allows fast recording of values coming from an X-Y
pad into a table object.

Params:
    input     -- Audio signal to write in the table.
    pos       -- Audio signal specifying the position where to write the `input` samples. It is a normalized position (in the range 0 to 1) in mode=0 or the raw position (in samples) for any other value of mode.
    table     -- The table where to write samples.
    mode      -- Sets the writing pointer mode. If 0, the position must be normalized between 0 (beginning of the table) and 1 (end of the table). For any other value, the position must be in samples between 0 and the length of the table. Available at initialization time only.
    maxwindow -- Maximum length, in samples, of the interpolated window when the position is moving fast. Useful to avoid interpolation over the entire table if using a circular writing position. Available at initialization time only. Defaults to 1024.
"""

from pyo import TableMorph
"""
TableMorph(input, table, sources)

Morphs between multiple PyoTableObjects.

Uses an index into a list of PyoTableObjects to morph between adjacent
tables in the list. The resulting morphed function is written into the
`table` object at the beginning of each buffer size. The tables in the
list and the resulting table must be equal in size.

Params:
    input   -- Morphing index between 0 and 1. 0 is the first table in the list and 1 is the last.
    table   -- The table where to write morphed waveform.
    sources -- List of tables to interpolate from.
"""

from pyo import Granulator
"""
Granulator(table, env, pitch=1, pos=0, dur=0.1, grains=8, basedur=0.1, mul=1, add=0)

Granular synthesis generator.

Params:
    table   -- Table containing the waveform samples.
    env     -- Table containing the grain envelope.
    pitch   -- Overall pitch of the granulator. This value transpose the pitch of all grains. Defaults to 1.
    pos     -- Pointer position, in samples, in the waveform table. Each grain sampled the current value of this stream at the beginning of its envelope and hold it until the end of the grain. Defaults to 0.
    dur     -- Duration, in seconds, of the grain. Each grain sampled the current value of this stream at the beginning of its envelope and hold it until the end of the grain. Defaults to 0.1.
    grains  -- Number of grains. Defaults to 8.
    basedur -- Base duration used to calculate the speed of the pointer to read the grain at its original pitch. By changing the value of the `dur` parameter, transposition per grain can be generated. Defaults to 0.1.
"""

from pyo import TrigTableRec
"""
TrigTableRec(input, trig, table, fadetime=0)

TrigTableRec is for writing samples into a previously created table.

See `NewTable` to create an empty table.

Each time a "trigger" is received in the `trig` input, TrigTableRec
starts the recording into the table until the table is full.

Params:
    input    -- Audio signal to write in the table.
    trig     -- Audio signal sending triggers.
    table    -- The table where to write samples.
    fadetime -- Fade time at the beginning and the end of the recording in seconds. Defaults to 0.
"""

from pyo import Looper
"""
Looper(table, pitch=1, start=0, dur=1.0, xfade=20, mode=1, xfadeshape=0, startfromloop=False, interp=2, autosmooth=False, mul=1, add=0)

Crossfading looper.

Looper reads audio from a PyoTableObject and plays it back in a loop with
user-defined pitch, start time, duration and crossfade time. The `mode`
argument allows the user to choose different looping modes.

Params:
    table         -- Table containing the waveform samples.
    pitch         -- Transposition factor. 1 is normal pitch, 0.5 is one octave lower, 2 is one octave higher. Negative values are not allowed. Defaults to 1.
    start         -- Starting point, in seconds, of the loop, updated only once per loop cycle. Defaults to 0.
    dur           -- Duration, in seconds, of the loop, updated only once per loop cycle. Defaults to 1.
    xfade         -- Percent of the loop time used to crossfade readers, updated only once per loop cycle and clipped between 0 and 50. Defaults to 20.
    mode          -- Loop modes. Defaults to 1. 0. no loop 1. forward 2. backward 3. back-and-forth
    xfadeshape    -- Crossfade envelope shape. Defaults to 0. 0. linear 1. equal power 2. sigmoid
    startfromloop -- If True, reading will begin directly at the loop start point. Otherwise, it begins at the beginning of the table. Defaults to False.
    interp        -- Choice of the interpolation method. Defaults to 2. 1. no interpolation 2. linear 3. cosinus 4. cubic
    autosmooth    -- If True, a lowpass filter, following the pitch, is applied on the output signal to reduce the quantization noise produced by very low transpositions. Defaults to False.
"""

from pyo import TablePut
"""
TablePut(input, table)

Writes values, without repetitions, from an audio stream into a table.

See :py:class:`DataTable` to create an empty table.

TablePut takes an audio input and writes values into a table, typically
a DataTable, but only when value changes. This allow to record only new
values, without repetitions.

The play method is not called at the object creation time. It starts
the recording into the table until the table is full. Calling the
play method again restarts the recording and overwrites previously
recorded values. The stop method stops the recording. Otherwise, the
default behaviour is to record through the end of the table.

Params:
    input -- Audio signal to write in the table.
    table -- The table where to write values.
"""

from pyo import TableFill
"""
TableFill(input, table)

Continuously fills a table with incoming samples.

See :py:class:`DataTable` or :py:class:`NewTable` to create an empty table.

TableFill takes an audio input and writes values into a PyoTableObject,
samples by samples. It wraps around the table length when reaching the end
of the table.

Calling the play method reset the writing position to 0.

Params:
    input -- Audio signal to write in the table.
    table -- The table where to write values.
"""

from pyo import Granule
"""
Granule(table, env, dens=50, pitch=1, pos=0, dur=0.1, mul=1, add=0)

Another granular synthesis generator.

As of pyo 0.7.4, users can call the `setSync` method to change the
granulation mode (either synchronous or asynchronous) of the object.

Params:
    table -- Table containing the waveform samples.
    env   -- Table containing the grain envelope.
    dens  -- Density of grains per second. Defaults to 50.
    pitch -- Pitch of the grains. A new grain gets the current value of `pitch` as its reading speed. Defaults to 1.
    pos   -- Pointer position, in samples, in the waveform table. Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 0.
    dur   -- Duration, in seconds, of the grain. Each grain samples the current value of this stream at the beginning of its envelope and hold it until the end of the grain. Defaults to 0.1.
"""

from pyo import TableScale
"""
TableScale(table, outtable, mul=1, add=0)

Scales all the values contained in a PyoTableObject.

TableScale scales the values of `table` argument according
to `mul` and `add` arguments and writes the new values in
`outtable`.

Params:
    table    -- Table containing the original values.
    outtable -- Table where to write the scaled values.
"""

from pyo import Particle
"""
Particle(table, env, dens=50, pitch=1, pos=0, dur=0.1, dev=0.01, pan=0.5, chnls=1, mul=1, add=0)

A full control granular synthesis generator.

Params:
    table -- Table containing the waveform samples.
    env   -- Table containing the grain envelope.
    dens  -- Density of grains per second. Defaults to 50.
    pitch -- Pitch of the grains. Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 1.
    pos   -- Pointer position, in samples, in the waveform table. Each grain sampled the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 0.
    dur   -- Duration, in seconds, of the grain. Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 0.1.
    dev   -- Maximum deviation of the starting time of the grain, between 0 and 1 (relative to the current duration of the grain). Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 0.01.
    pan   -- Panning factor of the grain (if chnls=1, this value is skipped). Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 0.5.
    chnls -- Number of output channels per audio stream (if chnls=2 and a stereo sound table is given at the table argument, the objet will create 4 output streams, 2 per table channel). Available at initialization only. Defaults to 1.
"""

from pyo import Particle2
"""
Particle2(table, env, dens=50, pitch=1, pos=0, dur=0.1, dev=0.01, pan=0.5, filterfreq=18000, filterq=0.7, filtertype=0, chnls=1, mul=1, add=0)

An even more full control granular synthesis generator.

This granulator object offers all the same controls as the
Particle object with additionally an independently controllable
filter per grain. The filters use the same implementation as the
Biquad object.

Params:
    table      -- Table containing the waveform samples.
    env        -- Table containing the grain envelope.
    dens       -- Density of grains per second. Defaults to 50.
    pitch      -- Pitch of the grains. Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 1.
    pos        -- Pointer position, in samples, in the waveform table. Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 0.
    dur        -- Duration, in seconds, of the grain. Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 0.1.
    dev        -- Maximum deviation of the starting time of the grain, between 0 and 1 (relative to the current duration of the grain). Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 0.01.
    pan        -- Panning factor of the grain (if chnls=1, this value is skipped). Each grain samples the current value of this stream at the beginning of its envelope and holds it until the end of the grain. Defaults to 0.5.
    filterfreq -- Center or cutoff frequency of the grain filter. Each grain samples the current value of this stream at the beginning of its envelope and hold it until the end of the grain. Defaults to 18000.
    filterq    -- Q of the grain filter. Each grain samples the current value of this stream at the beginning of its envelope and hold it until the end of the grain. Defaults to 0.7.
    filtertype -- Type of the grain filter. Each grain samples the current value of this stream at the beginning of its envelope and hold it until the end of the grain. Thw value is rounded to the nearest integer. Possible values are: 0. lowpass (default) 1. highpass 2. bandpass 3. bandstop 4. allpass
    chnls      -- Number of output channels per audio stream (if chnls=2 and a stereo sound table is given at the table argument, the objet will create 4 output streams, 2 per table channel). Available at initialization only. Defaults to 1.
"""

from pyo import TableScan
"""
TableScan(table, mul=1, add=0)

Reads the content of a table in loop, without interpolation.

A simple table reader, sample by sample, with wrap-around when
reaching the end of the table.

Params:
    table -- Table containing the waveform samples.
"""
