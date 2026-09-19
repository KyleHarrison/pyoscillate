"""MIDI input objects -- note, controller, pitch bend, aftertouch, program change. All defined in pyo/lib/midi.py."""

__all__ = ['Midictl', 'CtlScan', 'CtlScan2', 'Notein', 'Bendin', 'Touchin', 'Programin', 'MidiAdsr', 'MidiDelAdsr', 'RawMidi', 'MidiLinseg']

from pyo import Midictl
"""
Midictl(ctlnumber, minscale=0, maxscale=1, init=0, channel=0, mul=1, add=0)

Get the current value of a Midi controller.

Get the current value of a controller and optionally map it
inside a specified range.

Params:
    ctlnumber -- Controller number.
    minscale  -- Low range value for mapping. Defaults to 0.
    maxscale  -- High range value for mapping. Defaults to 1.
    init      -- Initial value. Defaults to 0.
    channel   -- Midi channel. 0 means all channels. Defaults to 0.
"""

from pyo import CtlScan
"""
CtlScan(function, toprint=True)

Scan the Midi controller's number in input.

Scan the Midi controller's number in input and send it to
a standard python `function`. Useful to implement a MidiLearn
algorithm.

Params:
    function -- Function to be called. The function must be declared with an argument for the controller number in input. Ex.: def ctl_scan(ctlnum): print(ctlnum)
    toprint  -- If True, controller number and value will be printed to the console.
"""

from pyo import CtlScan2
"""
CtlScan2(function, toprint=True)

Scan the Midi channel and controller number in input.

Scan the Midi channel and controller number in input and send them
to a standard python `function`. Useful to implement a MidiLearn
algorithm.

Params:
    function -- Function to be called. The function must be declared with two arguments, one for the controller number and one for the midi channel. Ex.: def ctl_scan(ctlnum, midichnl): print(ctlnum, midichnl)
    toprint  -- If True, controller number and value will be printed to the console.
"""

from pyo import Notein
"""
Notein(poly=10, scale=0, first=0, last=127, channel=0, mul=1, add=0)

Generates Midi note messages.

From a Midi device, takes the notes in the range defined with
`first` and `last` parameters, and outputs up to `poly`
noteon - noteoff streams in the `scale` format (Midi, hertz
or transpo).

Params:
    poly    -- Number of streams of polyphony generated. Defaults to 10.
    scale   -- Pitch output format. 0. Midi 1. Hertz 2. transpo In the transpo mode, the default central key (the key where there is no transposition) is (`first` + `last`) / 2. The central key can be changed with the setCentralKey method.
    first   -- Lowest Midi value. Defaults to 0.
    last    -- Highest Midi value. Defaults to 127.
    channel -- Midi channel. 0 means all channels. Defaults to 0.
"""

from pyo import Bendin
"""
Bendin(brange=2, scale=0, channel=0, mul=1, add=0)

Get the current value of the pitch bend controller.

Get the current value of the pitch bend controller and optionally
maps it inside a specified range.

Params:
    brange  -- Bipolar range of the pitch bend in semitones. Defaults to 2. -brange <= value < brange.
    scale   -- Output format. Defaults to 0. 0. Midi 1. transpo. The transpo mode is useful if you want to transpose values that are in a frequency (Hz) format.
    channel -- Midi channel. 0 means all channels. Defaults to 0.
"""

from pyo import Touchin
"""
Touchin(minscale=0, maxscale=1, init=0, channel=0, mul=1, add=0)

Get the current value of an after-touch Midi controller.

Get the current value of an after-touch Midi controller and optionally
maps it inside a specified range.

Params:
    minscale -- Low range value for mapping. Defaults to 0.
    maxscale -- High range value for mapping. Defaults to 1.
    init     -- Initial value. Defaults to 0.
    channel  -- Midi channel. 0 means all channels. Defaults to 0.
"""

from pyo import Programin
"""
Programin(channel=0, mul=1, add=0)

Get the current value of a program change Midi controller.

Get the current value of a program change Midi controller.

Params:
    channel -- Midi channel. 0 means all channels. Defaults to 0.
"""

from pyo import MidiAdsr
"""
MidiAdsr(input, attack=0.01, decay=0.05, sustain=0.7, release=0.1, mul=1, add=0)

Midi triggered ADSR envelope generator.

Calculates the classical ADSR envelope using linear segments.
The envelope starts when it receives a positive value in input,
this value is used as the peak amplitude of the envelope. The
`sustain` parameter is a fraction of the peak value and sets
the real sustain value. A 0 in input (note off) starts the
release part of the envelope.

Params:
    input   -- Input signal used to trigger the envelope. A positive value sets the peak amplitude and starts the envelope. A 0 starts the release part of the envelope.
    attack  -- Duration of the attack phase in seconds. Defaults to 0.01.
    decay   -- Duration of the decay phase in seconds. Defaults to 0.05.
    sustain -- Amplitude of the sustain phase, as a fraction of the peak amplitude at the start of the envelope. Defaults to 0.7.
    release -- Duration of the release phase in seconds. Defaults to 0.1.
"""

from pyo import MidiDelAdsr
"""
MidiDelAdsr(input, delay=0, attack=0.01, decay=0.05, sustain=0.7, release=0.1, mul=1, add=0)

Midi triggered ADSR envelope generator with pre-delay.

Calculates the classical ADSR envelope using linear segments.
The envelope starts after `delay` seconds when it receives a
positive value in input, this value is used as the peak amplitude
of the envelope. The `sustain` parameter is a fraction of the
peak value and sets the real sustain value. A 0 in input (note off)
starts the release part of the envelope.

Params:
    input   -- Input signal used to trigger the envelope. A positive value sets the peak amplitude and starts the envelope. A 0 starts the release part of the envelope.
    delay   -- Duration of the delay phase, before calling the envelope in seconds. Defaults to 0.
    attack  -- Duration of the attack phase in seconds. Defaults to 0.01.
    decay   -- Duration of the decay phase in seconds. Defaults to 0.05.
    sustain -- Amplitude of the sustain phase, as a fraction of the peak amplitude at the start of the envelope. Defaults to 0.7.
    release -- Duration of the release phase in seconds. Defaults to 0.1.
"""

from pyo import RawMidi
"""
RawMidi(function)

Raw Midi handler.

This object calls a python function for each raw midi data
(status, data1, data2) event for further processing in Python.

Params:
    function -- Function to be called. The function must be declared with three arguments, one for the status byte and two for the data bytes. Ex.: def event(status, data1, data2): print(status, data1, data2)
"""

from pyo import MidiLinseg
"""
MidiLinseg(input, list, hold=1, mul=1, add=0)

Line segments trigger.

MidiLinseg starts reading a break-points line segments each time it
receives a positive value in its `input` parameter.

Params:
    input -- Input signal used to trigger the envelope. A positive value sets the peak amplitude and starts the envelope. A 0 starts the release part of the envelope.
    list  -- Points used to construct the line segments. Each tuple is a new point in the form (time, value). Times are given in seconds and must be in increasing order.
    hold  -- The point, starting at 0, acting as the sustain point. The envelope will hold this value as long as the input signal is positive. The release part is the remaining points. Defaults to 1.
"""
