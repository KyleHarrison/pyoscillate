"""Music Macro Language (MML) string-driven sequencer. Defined in pyo/lib/mmlmusic.py."""

__all__ = ['MMLParser', 'MML']

from pyo import MMLParser
"""
MMLParser(text, voices=1)

"""

from pyo import MML
"""
MML(music, voices=1, loop=False, poly=1, updateAtEnd=False)

Generates music sequences based on a custom MML notation.

Music Macro Language (MML) is a music description language used in
sequencing music on computer and video game systems.

Params:
    music       -- The new music code to parse. If the string is a valid path to a text file, the file is opened and its content is taken as the music code.
    voices      -- The number of voices in the music code. This number is used to initialize the internal voices that will play the sequences. Defaults to 1.
    loop        -- If True, the playback will start again when the music reaches its end, otherwise the object just stops to send triggers. Defaults to False.
    poly        -- Per voice polyphony. Denotes how many independent streams are generated per voice by the object, allowing overlapping processes. Available only at initialization. Defaults to 1.
    updateAtEnd -- If True, voices will update their internal sequence only when the current one reaches its end, no matter when the `music` argument is changed. If False, sequences are updated immediately. Defaults to False.
"""
