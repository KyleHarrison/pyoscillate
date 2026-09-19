"""Value Converters (Map/SLMap) -- map a 0-1 control range (e.g. a GUI slider) onto a parameter's useful range. All defined in pyo/lib/_maps.py."""

__all__ = ['Map', 'SLMap', 'SLMapFreq', 'SLMapMul', 'SLMapPhase', 'SLMapPan', 'SLMapQ', 'SLMapDur']

from pyo import Map
"""
Map(min, max, scale)

Converts value between 0 and 1 on various scales.

Base class for Map objects.

Params:
    min   -- Lowest value of the range.
    max   -- Highest value of the range.
    scale -- Method used to scale the input value on the specified range.
"""

from pyo import SLMap
"""
SLMap(min, max, scale, name, init, res='float', ramp=0.025, dataOnly=False)

Base Map class used to manage control sliders.

Derived from Map class, a few parameters are added for sliders
initialization.

Params:
    min      -- Smallest value of the range.
    max      -- Highest value of the range.
    scale    -- Method used to scale the input value on the specified range.
    name     -- Name of the attributes the slider is affected to.
    init     -- Initial value. Specified in the real range, not between 0 and 1. Use `set` method to retreive the normalized corresponding value.
    res      -- Sets the resolution of the slider. Defaults to 'float'.
    ramp     -- Ramp time, in seconds, used to smooth the signal sent from slider to object's attribute. Defaults to 0.025.
    dataOnly -- Set this argument to True if the parameter does not accept audio signal as control but discrete values. If True, label will be marked with a star symbol (*). Defaults to False.
"""

from pyo import SLMapFreq
"""
SLMapFreq(init=1000)

SLMap with normalized values for a 'freq' slider.

Params:
    init -- Initial value. Specified in the real range, not between 0 and 1. Defaults to 1000.
"""

from pyo import SLMapMul
"""
SLMapMul(init=1.0)

SLMap with normalized values for a 'mul' slider.

Params:
    init -- Initial value. Specified in the real range, not between 0 and 1. Defaults to 1.
"""

from pyo import SLMapPhase
"""
SLMapPhase(init=0.0)

SLMap with normalized values for a 'phase' slider.

Params:
    init -- Initial value. Specified in the real range, not between 0 and 1. Defaults to 0.
"""

from pyo import SLMapPan
"""
SLMapPan(init=0.0)

SLMap with normalized values for a 'pan' slider.

Params:
    init -- Initial value. Specified in the real range, not between 0 and 1. Defaults to 0.
"""

from pyo import SLMapQ
"""
SLMapQ(init=1.0)

SLMap with normalized values for a 'q' slider.

Params:
    init -- Initial value. Specified in the real range, not between 0 and 1. Defaults to 1.
"""

from pyo import SLMapDur
"""
SLMapDur(init=1.0)

SLMap with normalized values for a 'dur' slider.

Params:
    init -- Initial value. Specified in the real range, not between 0 and 1. Defaults to 1.
"""
