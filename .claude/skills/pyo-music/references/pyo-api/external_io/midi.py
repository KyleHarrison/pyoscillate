"""Midi Handling -- read MIDI note/controller/pitch-bend input from an
external device. Not used by this project yet.
"""

__all__ = ["Notein", "Midictl", "Bendin", "MidiAdsr"]

from pyo import Notein

"""
Notein(poly=10, scale=0, first=0, last=127, channel=0, mul=1, add=0)

Generates MIDI note messages (pitch, velocity, note-on/off) from an
incoming MIDI note stream, across `poly` simultaneous voices.

Params:
    poly    -- Number of note streams (voices) to generate. Default 10.
    scale   -- Output scaling for pitch (0=MIDI, 1=Hz, 2=transposition
               factor). Default 0.
    first   -- Lowest MIDI note number accepted. Default 0.
    last    -- Highest MIDI note number accepted. Default 127.
    channel -- MIDI channel to listen on, 0 = all channels. Default 0.
    mul     -- Output multiplier. Default 1.
    add     -- Output additive value. Default 0.
"""

from pyo import Midictl

"""
Midictl(ctlnumber=1, minscale=0, maxscale=1, init=0, channel=0,
         mul=1, add=0)

Reads the current value of a MIDI continuous controller, scaled to a
useful range.

Params:
    ctlnumber -- MIDI controller number to read. Default 1.
    minscale  -- Output value when the controller is at 0. Default 0.
    maxscale  -- Output value when the controller is at 127. Default 1.
    init      -- Initial value before any MIDI message arrives. Default 0.
    channel   -- MIDI channel to listen on, 0 = all channels. Default 0.
    mul       -- Output multiplier. Default 1.
    add       -- Output additive value. Default 0.
"""

from pyo import Bendin

"""
Bendin(brange=2, scale=0, channel=0, mul=1, add=0)

Reads the current value of the MIDI pitch bend controller.

Params:
    brange  -- Bend range in semitones. Default 2.
    scale   -- Output scaling (0=semitones, 1=transposition factor).
               Default 0.
    channel -- MIDI channel to listen on, 0 = all channels. Default 0.
    mul     -- Output multiplier. Default 1.
    add     -- Output additive value. Default 0.
"""

from pyo import MidiAdsr

"""
MidiAdsr(input, attack=0.01, decay=0.05, sustain=0.707, release=0.1, mul=1)

ADSR envelope generator triggered directly by MIDI note-on/note-off
messages (from e.g. Notein), rather than a Trig stream.

Params:
    input   -- A Notein "trigon"/"trigoff" pair driving the envelope.
    attack  -- Attack time, in seconds. Default 0.01.
    decay   -- Decay time, in seconds. Default 0.05.
    sustain -- Sustain level, 0-1. Default 0.707.
    release -- Release time, in seconds. Default 0.1.
    mul     -- Output multiplier. Default 1.
"""
