"""10. Output -- send a signal to the speakers, or just run an object.

Not a class of its own: `.out()` and `.play()` are methods every
PyoObject inherits. Trace any patch backward from `.out()` to read it.
"""

__all__ = ['PyoObject']

from pyo import PyoObject

"""
PyoObject.out(chnl=0, inc=1, dur=0, delay=0)

Starts the object's processing AND sends its signal to the speakers.

Params:
    chnl  -- First physical output channel to write to. Default 0.
    inc   -- Channel increment between the object's streams. Default 1.
    dur   -- Duration before auto-stop, in seconds; 0 means indefinitely.
             Default 0.
    delay -- Delay before starting, in seconds. Default 0.
"""

"""
PyoObject.play(dur=0, delay=0)

Starts the object's internal processing WITHOUT sending audio to the
speakers -- used for triggers/envelopes/control objects that only exist to
drive other objects' parameters.

Params:
    dur   -- Duration before auto-stop, in seconds; 0 means indefinitely.
             Default 0.
    delay -- Delay before starting, in seconds. Default 0.
"""

"""
PyoObject.stop(wait=0)

Stops the object's processing.

Params:
    wait -- Time to fade out before stopping, in seconds. Default 0.
"""
