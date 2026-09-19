"""High-level, Python-side event/instrument-scheduling framework (as opposed to the audio-rate trigger objects in triggers.py). All defined in pyo/lib/events.py."""

__all__ = ['EventGenerator', 'EventScale', 'MarkovGen', 'EventInstrument', 'DefaultInstrument', 'EventDummy', 'EventFilter', 'EventKey', 'EventSeq', 'EventSlide', 'EventIndex', 'EventMarkov', 'EventChoice', 'EventDrunk', 'EventNoise', 'EventCall', 'EventConditional', 'Events']

from pyo import EventGenerator
"""
EventGenerator()

Base class for all event generators.

This class contains the common behaviours of all event generators.

Each EventGenerator contains a particular algorithm that can produce a
sequence of values triggered by an Events mecanism for one of its arguments.

The EventGenerator allows very flexible control of the algorithm parameters.
It can be a single value, another EventGenerator or an audio signal (PyoObject).

Arithmetic operations are allowed on EventGenerator. An EventDummy is
then created to apply the operation to each value produced by the generator.

Arithmetic operators are:

    +: float, PyoObject or EventGenerator
        Addition.
    -: float, PyoObject or EventGenerator
        Substraction
    *: float, PyoObject or EventGenerator
        Multiplication
    /: float, PyoObject or EventGenerator
        Division
    %:  float, PyoObject or EventGenerator
        Modulo (remaining of the division)
    **: float, PyoObject or EventGenerator
        Exponent
    //: float, PyoObject or EventGenerator
        Quantizer (returns te nearest multiple of its argument)

EventGenerator has a number of filter methods that can be applied on
any generator to modify its output values. Available filter methods are:

    floor:
        Return an EventFilter computing the largest integer less than or
        equal to its input value.
    ceil:
        Return an EventFilter computing the smallest integer greater than
        or equal to its input value.
    round:
        Return an EventFilter computing the nearest integer to its input value.
    snap:
        Return an EventFilter which choose the nearest value of its input
        value in a list of choices.
    deviate:
        Return an EventFilter which randomly move, up or down, its input value.
    clip:
        Return an EventFilter which clips its input value between predefined
        limits.
    scale:
        Return an EventFilter which maps its input value, in the range 0 to 1,
        to an output range, with a scaling curve.
    rescale:
        Return an EventFilter which maps its input value, given in an input
        range, to an output range with a scaling curve.
    iftrue:
        Return an EventFilter which compares its input value to a comparison
        value and outputs it if the comparison is True.

"""

from pyo import EventScale
"""
EventScale(root='C', scale='major', first=4, octaves=2, type=0)

Musical scale builder.

EventScale constructs a list of pitches according to its arguments.

EventScale works similarly to list, ie. uses slicing with square brackets
to access data, with the first element at index 0.

It also accept the len() function, which returns the number of elements in
the scale.

Params:
    root    -- The base note (fundamental) of the scale. Possible values are: 'C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B'. Defaults to 'C'.
    scale   -- The scale name to construct. Possible scales are: 'major', 'minorH', 'minorM', 'ionian', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'aeolian', 'locrian', 'wholeTone', 'majorPenta', 'minorPenta', 'egyptian', 'majorBlues', 'minorBlues', 'minorHungarian'. Defaults to 'major'.
    first   -- The first octave of the generated scale, in multiple of 12. A value of 4, for a root of 'C' means the first note of the scale will be 48. Defaults to 4.
    octaves -- The number of octaves in the generated scale. Defaults to 2.
    type    -- The unit type in which the values are stored. Possible types are: 0: MIDI note 1: Hertz 2: octave.degree notation (MIDI note 48 is 4.00 in octave.degrees)
"""

from pyo import MarkovGen
"""
MarkovGen(lst, order=2)

"""

from pyo import EventInstrument
"""
EventInstrument(args)

Base class for an Events instrument. All attributes given to the Events
object can be accessed as self.attribute_name inside the instrument.

This base class constructs an envelope, named self.env, according to the
value given to 'envelope' (ex.: a LinTable object) or to 'attack', 'decay',
'sustain' and 'release' attributes of the event. The envelope is also
scaled by the value of self.amp, defined by 'amp', 'db' or 'midivel'
arguments of the Events object.

This base class also creates a self.freq variable based on 'freq', 'degree'
or 'midinote' arguments. This variable can be used in the instrument to
control the pitch of the sound.

All resources are automatically destroyed when the lifetime of the event
is over. The lifetime of the event is set as self.dur + self.tail ('dur'
or 'beat' and 'tail' arguments of Events).

"""

from pyo import DefaultInstrument
"""
DefaultInstrument(args)

The default instrument, playing a stereo RC oscillator, used when
'instr' attribute is not defined for an Events object.

"""

from pyo import EventDummy
"""
EventDummy(generator1, generator2, type)

An EventGenerator created internally to handle arithmetic on Events.

"""

from pyo import EventFilter
"""
EventFilter(generator, type, args)

An EventGenerator created internally to handle simple filter on Events.

"""

from pyo import EventKey
"""
EventKey(key, master=None)

An EventGenerator that allow to retrieve the value of another parameter.

EventKey returns the current value of another parameter of the Events
object where it is used. From there, other processes can be applied
(arithmetics, filters) to transform this value.

EventKey can also read parameter values from another Events object when
one is passed as `master` argument.

Params:
    key    -- The name of the parameter to read from.
    master -- The Events object from which to read the parameter value. If None (the default), the current Events object is used.
"""

from pyo import EventSeq
"""
EventSeq(values, occurrences=inf, stopEventsWhenDone=True)

Plays through an entire list of values many times.

EventSeq will loop over its list of values a number of times
defined by the occurrences argument.

Params:
    values             -- List of values to loop over. Values in list can be floats, PyoObject or other EventGenerator.
    occurrences        -- Number of times the sequence is entirely played in loop. Defaults to inf (infinite).
    stopEventsWhenDone -- If True, the Events playback will stop if this generator reaches its end. If False, the Events will ignore this signal and probably get None as value for the given parameter. It's the user responsability to handle this case correctly. Defaults to True.
"""

from pyo import EventSlide
"""
EventSlide(values, segment, step, startpos=0, wraparound=True, occurrences=inf, stopEventsWhenDone=True)

Plays overlapping segments from a list of values.

EventSlide will play a segment of length `segment` from startpos,
then another segment with a start position incremented by `step`,
and so on.

Params:
    values             -- List of values to read. Values in list can be floats, PyoObject or other EventGenerator.
    segment            -- Number of values of each segment.
    step               -- How far to step the start of each segment from the previous. A negative value will step backward.
    startpos           -- The start position of the first segment. A negative value sets the position backward starting from the end of the list. Defaults to 0.
    wraparound         -- If 'wraparound' if True, indexing wraps around if goes past the beginning or the end of the list. If False, the playback stops if it goes outside the list bounds. Defaults to True.
    occurrences        -- Number of entire segments to play. Defaults to inf (infinite).
    stopEventsWhenDone -- If True, the Events playback will stop if this generator reaches its end. If False, the Events will ignore this signal and probably get None as value for the given parameter. It's the user responsability to handle this case correctly. Defaults to True.
"""

from pyo import EventIndex
"""
EventIndex(values, index, occurrences=inf, stopEventsWhenDone=True)

Plays values from a list based on a position index.

Params:
    values             -- List of values to read. Values in list can be floats, PyoObject or other EventGenerator.
    index              -- Position to read in the list, starting at 0.
    occurrences        -- Number of values to play. Defaults to inf (infinite).
    stopEventsWhenDone -- If True, the Events playback will stop if this generator reaches its end. If False, the Events will ignore this signal and probably get None as value for the given parameter. It's the user responsability to handle this case correctly. Defaults to True.
"""

from pyo import EventMarkov
"""
EventMarkov(values, order=2, occurrences=inf, stopEventsWhenDone=True)

Applies a Markov algorithm to a list of values.

A Markov chain is a stochastic model describing a sequence of possible events
in which the probability of each event depends only on the state attained in
the previous events.

Params:
    values             -- Original list of values.
    order              -- Order of the Markov chain, between 1 and 10. Determines how many past values will be used to build the probability table for the next note. Defaults to 2.
    occurrences        -- Number of values to play. Defaults to inf (infinite).
    stopEventsWhenDone -- If True, the Events playback will stop if this generator reaches its end. If False, the Events will ignore this signal and probably get None as value for the given parameter. It's the user responsability to handle this case correctly. Defaults to True.
"""

from pyo import EventChoice
"""
EventChoice(values, occurrences=inf, stopEventsWhenDone=True)

Plays values randomly chosen from a list.

Params:
    values             -- List of possible values to read. Values in list can be floats, PyoObject or other EventGenerator.
    occurrences        -- Number of values to play. Defaults to inf (infinite).
    stopEventsWhenDone -- If True, the Events playback will stop if this generator reaches its end. If False, the Events will ignore this signal and probably get None as value for the given parameter. It's the user responsability to handle this case correctly. Defaults to True.
"""

from pyo import EventDrunk
"""
EventDrunk(values, maxStep=2, occurrences=inf, stopEventsWhenDone=True)

Performs a random walk over a list of values.

A random walk is a stochastic process that consists of a succession of
random steps, within a distance of +/- `maxStep` from the previous state.

Params:
    values             -- List of values to read. Values in list can be floats, PyoObject or other EventGenerator.
    maxStep            -- Determine the larger step the walk can do between two successive events. A negative 'maxStep' is the same but repetition are not allowed. Defaults to 2.
    occurrences        -- Number of values to play. Defaults to inf (infinite).
    stopEventsWhenDone -- If True, the Events playback will stop if this generator reaches its end. If False, the Events will ignore this signal and probably get None as value for the given parameter. It's the user responsability to handle this case correctly. Defaults to True.
"""

from pyo import EventNoise
"""
EventNoise(type=0, occurrences=inf, stopEventsWhenDone=True)

Return a random value between -1.0 and 1.0.

EventNoise returns a random value between -1.0 and 1.0, based on one of
three common noise generators, white, pink (1/f) and brown (1/f^2).

Params:
    type               -- The type of noise used to generate the random sequence. Available types are:
    0                  -- 
    1                  -- 
    2                  -- 
    occurrences        -- Number of values to play. Defaults to inf (infinite).
    stopEventsWhenDone -- If True, the Events playback will stop if this generator reaches its end. If False, the Events will ignore this signal and probably get None as value for the given parameter. It's the user responsability to handle this case correctly. Defaults to True.
"""

from pyo import EventCall
"""
EventCall(function, args, kwargs)

Calls a function, with any number of arguments, and uses its return value.

EventCall can call any function (built-in, from a module or user-defined)
and use its return as the value for the Events's parameter where it is used.
The function *must* return a single number.

Params:
    function           -- The function to call, which should return the value to use.
    args               -- Any number of arguments to pass to the function call. If given a PyoObject or an EventGenerator, these will be resolved for each event and the result passed, as number, to the function.
    occurrences        -- Number of values to play. Defaults to inf (infinite).
    stopEventsWhenDone -- If True, the Events playback will stop if this generator reaches its end. If False, the Events will ignore this signal and probably get None as value for the given parameter. It's the user responsability to handle this case correctly. Defaults to True.
"""

from pyo import EventConditional
"""
EventConditional(condition, iftrue, iffalse, occurrences=inf, stopEventsWhenDone=True)

Executes one generator or the other depending on the result of a condition.

EventConditional takes three values or generators as arguments and if the
value of `condition` is True (anything that python considers True), the
`iftrue` argument is used to produce the value for the event, otherwise
th `iffalse` argument is used.

Params:
    condition          -- Conditional value. True for everything python considers True.
    iftrue             -- Output value if the condition is True.
    iffalse            -- Output value if the condition is False.
    occurrences        -- Number of values to play. Defaults to inf (infinite).
    stopEventsWhenDone -- If True, the Events playback will stop if this generator reaches its end. If False, the Events will ignore this signal and probably get None as value for the given parameter. It's the user responsability to handle this case correctly. Defaults to True.
"""

from pyo import Events
"""
Events(args)

Sequencing user-defined events to form musical phrases.

The Events object is the primary tool in the events framework. It uses
generators (derived from EventGenerator) as value for its arguments to
build a sequence of events, each of them with their own parameters.

Each time Events needs to produce a new event, it collects values from
the generators given to its arguments, builds a parameter dictionary
and gives it to a new instance of the audio instrument referenced to
its 'instr' argument.

The object produces new events until one of its generators reaches the
end of its sequence.

Events is a child of the dictionary class, which means that every argument
given at its initialization will become a new key (with its associated
value) in its memory. These keys will serve to create the parameter
dictionary passed to the audio instrument instance playing this event.
Inside the instrument instance, the value associated to these keys will
be retrieved as instance's attributes, with the syntax self.key_name.

The user can create as many new keys as needed to control its instrument,
but there is already a number of pre-defined keys for which Events will
do some processing and build useful parameters. Here is the list, grouped
by themes, of pre-defined keys to overwrite:

**Instrument**
    - instr: class, optional
        Reference to a custom class with which the events will be played.
        Defaults to DefaultInstrument.
    - signal: string, optional
        Name of the attribute in the instrument defintion retrieved as the
        output signal of the Events object. The sig() method returns the
        sum, as an audio signal, of all active instances. This can be useful
        to do post-processing on the signal produced by the events. Defaults
        to None.

**Constants**
    - bpm: int, optional
        Beat-Per-Minute value used by the `beat` key to compute event's duration.
        Defaults to 120.
    - outs: int, optional
        Number of output channels in the audio signal returned by the sig() method.
        This value should match the number of audio streams produced by the instrument.
        Defaults to 2.

**Duration keys**
    - dur: float, PyoObject or EventGenerator, optional
        Duration, in seconds, before the next event. Defaults to 1.
    - beat: float, PyoObject or EventGenerator, optional
        Duration, in beat value, before the next event (1 beat = quarter note at BPM).
        If defined, this value will be used to compute the duration in seconds for the
        `dur` key. Defaults to None.
    - durmul: float, PyoObject or EventGenerator, optional
        Event duration multiplier (only affects the duration of the event's lifetime,
        not the time to wait before the next event). Defaults to 1.
    - tail: float, PyoObject or EventGenerator, optional
        Duration, in seconds, to wait before deleting the instrument's instance when
        its envelope has ended. Useful to let a reverb tail to finish before cleaning-up
        the instance. Defaults to 2.

**Amplitude keys**
    - amp: float, PyoObject or EventGenerator, optional
        Linear gain for the event (1 is nominal gain). Defaults to 0.7.
    - dB: float, PyoObject or EventGenerator, optional
        Gain, in decibels, for the event. If defined, this value will be used to compute
        the linear gain for the `amp` key. Defaults to None.
    - midivel: float, PyoObject or EventGenerator, optional
        Midi velocity, between 0 and 127, for the event. If defined, this value will be
        used to compute the linear gain for the `amp` key. Defaults to None.

**Envelope keys**
    - envelope: PyoTableObject, optional
        User-defined envelope as a PyoTableObject. If defined, this will be the envelope
        created for the event. Defaults to None.
    - attack: float, PyoObject or EventGenerator, optional
        Rising time, in seconds, of an ASR or ADSR envelope. This envelope is created if
        `envelope` is None. Defaults to 0.005.
    - decay: float, PyoObject or EventGenerator, optional
        If defined, its the decay time, in seconds, of an ADSR envelope, otherwise the
        envelope will be an ASR (Attack - Sustain - Release). Defaults to None.
    - sustain: float, PyoObject or EventGenerator, optional
        Sustain linear gain of an ADSR or ASR envelope. Defaults to 0.7.
    - release: float, PyoObject or EventGenerator, optional
        Release time, in seconds, of an ASR or ADSR envelope. This envelope is created if
        `envelope` is None. Defaults to 0.05.

**Pitch keys**
    - freq: float, PyoObject or EventGenerator, optional
        Frequency, in cycle per seconds, for the event. Defaults to 250.
    - midinote: float, PyoObject or EventGenerator, optional
        Midi pitch, between 0 and 127, for the event. If defined, this value will be used
        to compute the frequency in cycles per second for the `freq` key. Defaults to None.
    - degree: float, PyoObject or EventGenerator, optional
        Octave.degree pitch notation (ex.: 6.00, 6.04, 6.07). If defined, this value will be
        used to compute the frequency in cycles per second for the `freq` key. Defaults to None.
    - transpo: float, PyoObject or EventGenerator, optional
        Transposition, in midi note value (-12 is an octave lower), automatically computed in
        the value of the `freq` key. Defaults to 0.

**Ending keys**
    - atend: python callable, optional
        If defined, a function to call when all events are played. This can be useful to sequence
        multiple Events objects. Defaults to None

"""
