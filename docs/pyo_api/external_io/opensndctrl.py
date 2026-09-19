"""Open Sound Control -- send/receive values over the network via OSC. Not
used by this project yet.
"""

__all__ = ['OscSend', 'OscReceive', 'OscDataSend']

from pyo import OscSend

"""
OscSend(input, port, address, host="127.0.0.1")

Sends a signal's values over the network via OSC.

Params:
    input   -- Signal whose values are sent.
    port    -- Destination UDP port.
    address -- OSC address pattern, e.g. "/synth/freq".
    host    -- Destination host. Default "127.0.0.1".
"""

from pyo import OscReceive

"""
OscReceive(port, address, mul=1, add=0)

Receives values over the network via OSC, exposing them as a PyoObject
signal.

Params:
    port    -- UDP port to listen on.
    address -- OSC address pattern to match, e.g. "/synth/freq".
    mul     -- Output multiplier. Default 1.
    add     -- Output additive value. Default 0.
"""

from pyo import OscDataSend

"""
OscDataSend(types, port, address, host="127.0.0.1")

Sends arbitrary typed data values (not audio-rate signals) over OSC.

Params:
    types   -- String describing the argument types, e.g. "iff" for
               int/float/float.
    port    -- Destination UDP port.
    address -- OSC address pattern.
    host    -- Destination host. Default "127.0.0.1".
"""
