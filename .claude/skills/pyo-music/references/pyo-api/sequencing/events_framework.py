"""Events framework -- higher-level declarative note-sequencing system,
built on top of Event Sequencing (event_sequencing.py) and Triggers
(../core/04_triggers.py). Not used by this project yet.
"""

__all__ = ['Events', 'EventSeq', 'EventMarkov', 'EventScale']

from pyo import Events

"""
Events(**args)

Sequences user-defined events (each a dict of EventGenerator parameters,
e.g. pitch/dur/amp) into musical phrases. The top-level object of the
Events framework; keyword arguments describe each parameter as an
EventGenerator (EventSeq, EventChoice, etc.).

Params:
    **args -- Keyword arguments, each an EventGenerator describing how that
              parameter evolves across triggered events (e.g.
              pitch=EventSeq([60, 64, 67])).
"""

from pyo import EventSeq

"""
EventSeq(value=[0], occurrences=1, ...)

An EventGenerator that plays through an entire list of values, in order,
`occurrences` times before repeating/stopping.

Params:
    value       -- List of values to sequence through. Default [0].
    occurrences -- Number of times to repeat the full list. Default 1.
"""

from pyo import EventMarkov

"""
EventMarkov(states, order=1, initState=None, ...)

An EventGenerator that applies a Markov-chain algorithm to a list of
values, picking each next value based on transition probabilities.

Params:
    states    -- List of possible values (Markov chain states).
    order     -- Order of the Markov chain. Default 1.
    initState -- Optional starting state index. Default None.
"""

from pyo import EventScale

"""
EventScale(root=60, scale=0, first=0, length=8, ...)

Musical scale builder for the Events framework -- generates a list of MIDI
note numbers from a root note and scale type.

Params:
    root   -- Root MIDI note number. Default 60.
    scale  -- Scale type index (e.g. 0=major, 1=minor, ...). Default 0.
    first  -- Starting degree of the scale. Default 0.
    length -- Number of notes to generate. Default 8.
"""
