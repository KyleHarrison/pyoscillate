"""4. Triggers / event sources -- things that fire discrete pulses.

These don't make sound; they make *timing events* that other objects react
to (see 05_trig_reactive.py).
"""

__all__ = ['Metro', 'Beat', 'Trig']

from pyo import Metro

"""
Metro(time=1, poly=1)

Generates isochronous (steady clock) trigger signals.

Params:
    time -- Time between triggers, in seconds. Default 1.
    poly -- Number of streams generated, for overlapping voices without
            click artifacts. Default 1.
"""

from pyo import Beat

"""
Beat(time=0.125, taps=16, w1=100, w2=50, w3=25, poly=1)

Generates algorithmic trigger patterns with three weighted accent levels,
useful for building rhythmic/percussive patterns.

Params:
    time -- Time between the smallest subdivision, in seconds. Default 0.125.
    taps -- Number of steps in the pattern. Default 16.
    w1   -- Probability weight for the strongest accent. Default 100.
    w2   -- Probability weight for the medium accent. Default 50.
    w3   -- Probability weight for the weakest accent. Default 25.
    poly -- Number of streams generated. Default 1.
"""

from pyo import Trig

"""
Trig()

Sends a single trigger the moment it's created/played. Useful for kicking
off a one-shot envelope or event without a recurring clock.
"""
