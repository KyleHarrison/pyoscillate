"""7. Modulators (continuous, non-triggered) -- run forever, feeding another
object's parameter to make it wobble/sweep continuously.

These plug into the same parameter slots as trig-reactive objects
(05_trig_reactive.py) -- the difference is purely whether the modulation is
event-driven (one-shot, gated) or free-running (cyclical, ungated).
`LFO` and `Sine` (02_generators.py) are reused here at sub-audio rate; the
strange attractors below only make sense in this continuous-modulator role.
"""

__all__ = ['Rossler', 'Lorenz']

from pyo import Rossler

"""
Rossler(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)

Chaotic attractor for the Rossler system -- a smoothly wandering,
never-repeating control signal, useful as an "organic" LFO substitute.

Params:
    pitch  -- Speed of the variation. Default 0.25.
    chaos  -- Amount of chaotic behaviour, 0-1. Default 0.5.
    stereo -- If True, generates two decorrelated streams. Default False.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import Lorenz

"""
Lorenz(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)

Chaotic attractor for the Lorenz system -- same role as Rossler, different
(more angular) character of wander.

Params:
    pitch  -- Speed of the variation. Default 0.25.
    chaos  -- Amount of chaotic behaviour, 0-1. Default 0.5.
    stereo -- If True, generates two decorrelated streams. Default False.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""
