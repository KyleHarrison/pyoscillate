"""Controller listeners -- background threads that dispatch MIDI/OSC input
without blocking the audio callback. Not used by this project yet.
"""

__all__ = ['MidiListener', 'OscListener']

from pyo import MidiListener

"""
MidiListener(function, mgr=None)

Self-contained MIDI listener thread -- calls a Python function with each
raw incoming MIDI event, independent of the audio graph.

Params:
    function -- Python callable invoked with each MIDI event.
    mgr      -- Optional MidiDispatcher to share a device connection with.
                Default None.
"""

from pyo import OscListener

"""
OscListener(function, port, address)

Self-contained OSC listener thread -- calls a Python function with each
matching incoming OSC message, independent of the audio graph.

Params:
    function -- Python callable invoked with each matching OSC message.
    port     -- UDP port to listen on.
    address  -- OSC address pattern to match.
"""
