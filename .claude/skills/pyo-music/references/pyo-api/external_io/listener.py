"""Background-thread listeners for raw MIDI/OSC events (as opposed to the audio-rate midi.py/opensndctrl.py objects). All defined in pyo/lib/listener.py."""

__all__ = ['MidiListener', 'MidiDispatcher', 'OscListener']

from pyo import MidiListener
"""
MidiListener(function, mididev=-1, reportdevice=False)

Self-contained midi listener thread.

This object allows to setup a Midi server that is independent
of the audio server (mainly to be able to receive Midi data even
when the audio server is stopped). Although it runs in a separated
thread, the same device can't be used by this object and the audio
server at the same time. It is adviced to call the deactivateMidi()
method on the audio server to avoid conflicts.

Params:
    function     -- Function that will be called when a new midi event is available. This function is called with the incoming midi data as arguments. The signature of the function must be: def myfunc(status, data1, data2)
    mididev      -- Sets the midi input device (see `pm_list_devices()` for the available devices). The default, -1, means the system default device. A number greater than the highest portmidi device index will open all available input devices. Specific devices can be set with a list of integers.
    reportdevice -- If True, the device ID will be reported as a fourth argument to the callback. The signature will then be: def myfunc(status, data1, data2, id) Available at initialization only. Defaults to False.
"""

from pyo import MidiDispatcher
"""
MidiDispatcher(mididev=-1)

Self-contained midi dispatcher thread.

This object allows to setup a Midi server that is independent
of the audio server (mainly to be able to send Midi data even
when the audio server is stopped). Although it runs in a separated
thread, the same device can't be used by this object and the audio
server at the same time. It is adviced to call the deactivateMidi()
method on the audio server to avoid conflicts.

Use the `send` method to send midi event to connected devices.

Use the `sendx` method to send sysex event to connected devices.

Params:
    mididev -- Sets the midi output device (see `pm_list_devices()` for the available devices). The default, -1, means the system default device. A number greater than the highest portmidi device index will open all available input devices. Specific devices can be set with a list of integers.
"""

from pyo import OscListener
"""
OscListener(function, port=9000)

Self-contained OSC listener thread.

This object allows to setup an OSC server that is independent
of the audio server (mainly to be able to receive OSC data even
when the audio server is stopped).

Params:
    function -- Function that will be called when a new OSC event is available. This function is called with the incoming address and values as arguments. The signature of the function must be:: def myfunc(address, *args)
    port     -- The OSC port on which the values are received. Defaults to 9000.
"""
