"""Utility/conversion objects -- scaling, sample-and-hold, recording, unit conversions (MIDI/dB/Hz). All defined in pyo/lib/utils.py."""

__all__ = ['Clean_objects', 'Print', 'Snap', 'Interp', 'SampHold', 'Record', 'Denorm', 'ControlRec', 'ControlRead', 'NoteinRec', 'NoteinRead', 'DBToA', 'AToDB', 'Scale', 'CentsToTranspo', 'TranspoToCents', 'MToF', 'FToM', 'MToT', 'Between', 'TrackHold', 'Resample']

from pyo import Clean_objects
"""
Clean_objects(time, args)

Stops and deletes PyoObjects after a given amount of time.

The start() method starts the thread timer (must be called).

Params:
    time -- Time, in seconds, to wait before calling stop on the given objects and deleting them.
    args -- Objects to delete. As much as desired, separated by commas.
"""

from pyo import Print
"""
Print(input, method=0, interval=0.25, message='')

Print PyoObject's current value.

Params:
    input    -- Input signal to filter.
    method   -- There is two methods to set when a value is printed (Defaults to 0): 0. at a periodic interval. 1. everytime the value changed.
    interval -- Interval, in seconds, between each print. Used by method 0. Defaults to 0.25.
    message  -- Message to print before the current value. Defaults to "".
"""

from pyo import Snap
"""
Snap(input, choice, scale=0, mul=1, add=0)

Snap input values on a user's defined midi scale.

Snap takes an audio input of floating-point values from 0
to 127 and output the nearest value in the `choice` parameter.
`choice` can be defined on any number of octaves and the real
snapping values will be automatically expended. The object
will take care of the input octave range. According to `scale`
parameter, output can be in midi notes, hertz or transposition
factor (centralkey = 60).

Params:
    input  -- Incoming Midi notes as an audio stream.
    choice -- Possible values, as midi notes, for output.
    scale  -- Pitch output format. 0. MIDI (default) 1. Hertz 2. transposition factor In the transpo mode, the central key (the key where there is no transposition) is 60.
"""

from pyo import Interp
"""
Interp(input, input2, interp=0.5, mul=1, add=0)

Interpolates between two signals.

Params:
    input  -- First input signal.
    input2 -- Second input signal.
    interp -- Averaging value. 0 means only first signal, 1 means only second signal. Default to 0.5.
"""

from pyo import SampHold
"""
SampHold(input, controlsig, value=0.0, mul=1, add=0)

Performs a sample-and-hold operation on its input.

SampHold performs a sample-and-hold operation on its input according
to the value of `controlsig`. If `controlsig` equals `value`, the input
is sampled and held until next sampling.

Params:
    input      -- Input signal.
    controlsig -- Controls when to sample the signal.
    value      -- Sampling target value. Default to 0.0.
"""

from pyo import Record
"""
Record(input, filename, chnls=2, fileformat=0, sampletype=0, buffering=4, quality=0.4)

Writes input sound in an audio file on the disk.

`input` parameter must be a valid PyoObject or an addition of
PyoObjects, parameters can't be in list format.

Params:
    input      -- Input signal to record.
    filename   -- Full path of the file to create.
    chnls      -- Number of channels in the audio file. Defaults to 2.
    fileformat -- Format type of the audio file. Defaults to 0. Record will first try to set the format from the filename extension. If it's not possible, it uses the fileformat parameter. Supported formats are: 0. WAV - Microsoft WAV format (little endian) {.wav, .wave} 1. AIFF - Apple/SGI AIFF format (big endian) {.aif, .aiff} 2. AU - Sun/NeXT AU format (big endian) {.au} 3. RAW - RAW PCM data {no extension} 4. SD2 - Sound Designer 2 {.sd2} 5. FLAC - FLAC lossless file format {.flac} 6. CAF - Core Audio File format {.caf} 7. OGG - Xiph OGG container {.ogg}
    sampletype -- Bit depth encoding of the audio file. SD2 and FLAC only support 16 or 24 bit int. Supported types are: 0. 16 bits int (default) 1. 24 bits int 2. 32 bits int 3. 32 bits float 4. 64 bits float 5. U-Law encoded 6. A-Law encoded
    buffering  -- Number of bufferSize to wait before writing samples to disk. High buffering uses more memory but improves performance. Defaults to 4.
    quality    -- The encoding quality value, between 0.0 (lowest quality) and 1.0 (highest quality). This argument has an effect only with FLAC and OGG compressed formats. Defaults to 0.4.
"""

from pyo import Denorm
"""
Denorm(input, mul=1, add=0)

Mixes low level noise to an input signal.

Mixes low level (~1e-24 for floats, and ~1e-60 for doubles) noise to a an input signal.
Can be used before IIR filters and reverbs to avoid denormalized numbers which may
otherwise result in significantly increased CPU usage.

Params:
    input -- Input signal to process.
"""

from pyo import ControlRec
"""
ControlRec(input, filename, rate=1000, dur=0.0)

Records control values and writes them in a text file.

`input` parameter must be a valid PyoObject managing any number
of streams, other parameters can't be in list format. The user
must call the `write` method to create text files on the disk.

Each line in the text files contains two values, the absolute time
in seconds and the sampled value.

The play() method starts the recording and is not called at the
object creation time.

Params:
    input    -- Input signal to sample.
    filename -- Full path (without extension) used to create the files. "_000" will be added to file's names with increasing digits according to the number of streams in input. The same filename can be passed to a ControlRead object to read all related files.
    rate     -- Rate at which the input values are sampled. Defaults to 1000.
    dur      -- Duration of the recording, in seconds. If 0.0, the recording won't stop until the end of the performance. If greater than 0.0, the `stop` method is automatically called at the end of the recording.
"""

from pyo import ControlRead
"""
ControlRead(filename, rate=1000, loop=False, interp=2, mul=1, add=0)

Reads control values previously stored in text files.

Read sampled sound from a table, with optional looping mode.

Params:
    filename -- Full path (without extension) used to create the files. Usually the same filename as the one given to a ControlRec object to record automation. The directory will be scaned and all files named "filename_xxx" will add a new stream in the object.
    rate     -- Rate at which the values are sampled. Defaults to 1000.
    loop     -- Looping mode, False means off, True means on. Defaults to False.
    interp   -- Choice of the interpolation method. 1. no interpolation 2. linear (default) 3. cosinus 4. cubic
"""

from pyo import NoteinRec
"""
NoteinRec(input, filename)

Records Notein inputs and writes them in a text file.

`input` parameter must be a Notein object managing any number
of streams, other parameters can't be in list format. The user
must call the `write` method to create text files on the disk.

Each line in the text files contains three values, the absolute time
in seconds, the Midi pitch and the normalized velocity.

The play() method starts the recording and is not called at the
object creation time.

Params:
    input    -- Notein signal to sample.
    filename -- Full path (without extension) used to create the files. "_000" will be added to file's names with increasing digits according to the number of streams in input. The same filename can be passed to a NoteinRead object to read all related files.
"""

from pyo import NoteinRead
"""
NoteinRead(filename, loop=False, mul=1, add=0)

Reads Notein values previously stored in text files.

Params:
    filename -- Full path (without extension) used to create the files. Usually the same filename as the one given to a NoteinRec object to record automation. The directory will be scaned and all files named "filename_xxx" will add a new stream in the object.
    loop     -- Looping mode, False means off, True means on. Defaults to False.
"""

from pyo import DBToA
"""
DBToA(input, mul=1, add=0)

Returns the amplitude equivalent of a decibel value.

Returns the amplitude equivalent of a decibel value, 0 dB = 1.
The `input` values are internally clipped to -120 dB so -120 dB
returns 0.

Params:
    input -- Input signal, decibel value.
"""

from pyo import AToDB
"""
AToDB(input, mul=1, add=0)

Returns the decibel equivalent of an amplitude value.

Returns the decibel equivalent of an amplitude value, 1 = 0 dB.
The `input` values are internally clipped to 0.000001 so values
less than or equal to 0.000001 return -120 dB.

Params:
    input -- Input signal, amplitude value.
"""

from pyo import Scale
"""
Scale(input, inmin=0, inmax=1, outmin=0, outmax=1, exp=1, mul=1, add=0)

Maps an input range of audio values to an output range.

Scale maps an input range of audio values to an output range.
The ranges can be specified with `min` and `max` reversed for
invert-mapping. If specified, the mapping can also be exponential.

Params:
    input  -- Input signal to process.
    inmin  -- Minimum input value. Defaults to 0.
    inmax  -- Maximum input value. Defaults to 1.
    outmin -- Minimum output value. Defaults to 0.
    outmax -- Maximum output value. Defaults to 1.
    exp    -- Exponent value, specifies the nature of the scaling curve. Values between 0 and 1 give a reversed curve. Defaults to 1.0.
"""

from pyo import CentsToTranspo
"""
CentsToTranspo(input, mul=1, add=0)

Returns the transposition factor equivalent of a given cents value.

Returns the transposition factor equivalent of a given cents value, 0 cents = 1.

Params:
    input -- Input signal, cents value.
"""

from pyo import TranspoToCents
"""
TranspoToCents(input, mul=1, add=0)

Returns the cents value equivalent of a transposition factor.

Returns the cents value equivalent of a transposition factor, 1 = 0 cents.

Params:
    input -- Input signal, transposition factor.
"""

from pyo import MToF
"""
MToF(input, mul=1, add=0)

Returns the frequency (Hz) equivalent to a midi note.

Returns the frequency (Hz) equivalent to a midi note,
60 = 261.62556530066814 Hz.

Params:
    input -- Input signal as midi note.
"""

from pyo import FToM
"""
FToM(input, mul=1, add=0)

Returns the midi note equivalent to a frequency in Hz.

Returns the midi note equivalent to a frequency in Hz,
440.0 (hz) = 69.

Params:
    input -- Input signal as frequency in Hz.
"""

from pyo import MToT
"""
MToT(input, centralkey=60.0, mul=1, add=0)

Returns the transposition factor equivalent to a midi note.

Returns the transposition factor equivalent to a midi note. If the midi
note equal the `centralkey` argument, the output is 1.0.

Params:
    input      -- Input signal as midi note.
    centralkey -- The midi note that returns a transposition factor of 1, that is to say no transposition. Defaults to 60.
"""

from pyo import Between
"""
Between(input, min=-1.0, max=1.0, mul=1, add=0)

Informs when an input signal is contained in a specified range.

Outputs a value of 1.0 if the input signal is greater or egal
than `min` and less than `max`. Otherwise, outputs a value of 0.0.

Params:
    input -- Input signal to process.
    min   -- Minimum range value. Defaults to 0.
    max   -- Maximum range value. Defaults to 1.
"""

from pyo import TrackHold
"""
TrackHold(input, controlsig, value=0.0, mul=1, add=0)

Performs a track-and-hold operation on its input.

TrackHold lets pass the signal in `input` without modification but hold
a sample according to the value of `controlsig`. If `controlsig` equals
`value`, the input is sampled and held, otherwise, it passes thru.

Params:
    input      -- Input signal.
    controlsig -- Controls when to sample the signal.
    value      -- Sampling target value. Default to 0.0.
"""

from pyo import Resample
"""
Resample(input, mode=1, mul=1, add=0)

Realtime upsampling or downsampling of an audio signal.

This object should be used in the context of a resampling block
created with the Server's methods `beginResamplingBlock` and
`EndResamplingBlock`.

If used inside the block, it will resample its input signal according
to the resampling factor given to `beginResamplingFactor`. If the factor
is a negative value, the new virtual sampling rate will be
`current sr / abs(factor)`. If the factor is a postive value, the new
virtual sampling rate will be `current sr * factor`.

If used after `endResamplingBlock`, it will resample its input signal
to the current sampling rate of the server.

The `mode` argument specifies the interpolation/decimation mode used
internally.

Params:
    input -- Input signal to resample.
    mode  -- The interpolation/decimation mode. Defaults to 1. For the upsampling process, possible values are: - 0: zero-padding - 1: sample-and-hold - 2 or higher: the formula `mode * resampling factor` gives the FIR lowpass kernel length used to interpolate. For the downsampling process, possible values are: - 0 or 1: discard extra samples - 2 or higher: the formula `mode * abs(resampling factor)` gives the FIR lowpass kernel length used for the decimation.
"""
