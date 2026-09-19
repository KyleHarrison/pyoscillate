"""Open Sound Control (OSC) network send/receive objects. All defined in pyo/lib/opensndctrl.py."""

__all__ = ['OscSend', 'OscReceive', 'OscDataSend', 'OscDataReceive', 'OscListReceive']

from pyo import OscSend
"""
OscSend(input, port, address, host='127.0.0.1')

Sends values over a network via the Open Sound Control protocol.

Uses the OSC protocol to share values to other softwares or other
computers. Only the first value of each input buffersize will be
sent on the OSC port.

Params:
    input   -- Input signal.
    port    -- Port on which values are sent. Receiver should listen on the same port.
    address -- Address used on the port to identify values. Address is in the form of a Unix path (ex.: '/pitch').
    host    -- IP address of the target computer. The default, '127.0.0.1', is the localhost.
"""

from pyo import OscReceive
"""
OscReceive(port, address, mul=1, add=0)

Receives values over a network via the Open Sound Control protocol.

Uses the OSC protocol to receive values from other softwares or
other computers. Get a value at the beginning of each buffersize
and fill its buffer with it.

Params:
    port    -- Port on which values are received. Sender should output on the same port. Unlike OscSend object, there can be only one port per OscReceive object. Available at initialization time only.
    address -- Address used on the port to identify values. Address is in the form of a Unix path (ex.: '/pitch').
"""

from pyo import OscDataSend
"""
OscDataSend(types, port, address, host='127.0.0.1')

Sends data values over a network via the Open Sound Control protocol.

Uses the OSC protocol to share values to other softwares or other
computers. Values are sent on the form of a list containing `types`
elements.

Params:
    types   -- String specifying the types sequence of the message to be sent. Possible values are: - "i": integer - "h": long integer - "f": float - "d": double - "s" ; string - "b": blob (list of chars) - "m": MIDI packet (list of 4 bytes: [midi port, status, data1, data2]) - "c": char - "T": True - "F": False - "N": None (nil) The string "ssfi" indicates that the value to send will be a list containing two strings followed by a float and an integer.
    port    -- Port on which values are sent. Receiver should listen on the same port.
    address -- Address used on the port to identify values. Address is in the form of a Unix path (ex.: '/pitch').
    host    -- IP address of the target computer. The default, '127.0.0.1', is the localhost.
"""

from pyo import OscDataReceive
"""
OscDataReceive(port, address, function)

Receives data values over a network via the Open Sound Control protocol.

Uses the OSC protocol to receive data values from other softwares or
other computers. When a message is received, the function given at the
argument `function` is called with the current address destination in
argument followed by a tuple of values.

Params:
    port     -- Port on which values are received. Sender should output on the same port. Unlike OscDataSend object, there can be only one port per OscDataReceive object. Available at initialization time only.
    address  -- Address used on the port to identify values. Address is in the form of a Unix path (ex.: "/pitch"). There can be as many addresses as needed on a single port.
    function -- This function will be called whenever a message with a known address is received. there can be only one function per OscDataReceive object. Available at initialization time only.
"""

from pyo import OscListReceive
"""
OscListReceive(port, address, num=8, mul=1, add=0)

Receives list of values over a network via the Open Sound Control protocol.

Uses the OSC protocol to receive list of floating-point values from other
softwares or other computers. The list are converted into audio streams.
Get values at the beginning of each buffersize and fill buffers with them.

Params:
    port    -- Port on which values are received. Sender should output on the same port. Unlike OscSend object, there can be only one port per OscListReceive object. Available at initialization time only.
    address -- Address used on the port to identify values. Address is in the form of a Unix path (ex.: '/pitch').
    num     -- Length of the lists in input. The object will generate `num` audio streams per given address. Available at initialization time only. This value can't be a list. That means all addresses managed by an OscListReceive object are of the same length. Defaults to 8.
"""
