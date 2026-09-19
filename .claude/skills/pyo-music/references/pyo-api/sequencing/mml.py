"""Music Macro Language evaluator -- generates sequences from MML notation
strings. Not used by this project yet.
"""

__all__ = ["MML"]

from pyo import MML

"""
MML(music="", voices=1, loop=False, poly=1)

Generates music sequences based on MML (Music Macro Language) notation --
a compact text notation for specifying notes, rests, and durations
(similar to old chiptune trackers).

Params:
    music  -- MML notation string. Default "".
    voices -- Number of simultaneous MML voices/tracks. Default 1.
    loop   -- Whether to loop the sequence. Default False.
    poly   -- Number of streams generated per voice. Default 1.
"""
