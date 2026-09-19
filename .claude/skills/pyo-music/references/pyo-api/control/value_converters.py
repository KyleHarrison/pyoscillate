"""Value Converters (SLMap) -- map a 0-1 control range (e.g. a GUI slider)
onto a parameter's useful range. Not used by this project yet.
"""

__all__ = ['SLMap', 'SLMapFreq', 'SLMapQ']

from pyo import SLMap

"""
SLMap(min, max, scale="lin", name="", init=0, res="float", dataOnly=False)

Base class describing how a control slider maps onto a parameter's real
range -- used to drive pyo's built-in GUI sliders/controllers.

Params:
    min      -- Minimum value of the mapped range.
    max      -- Maximum value of the mapped range.
    scale    -- Mapping curve, "lin" or "log". Default "lin".
    name     -- Parameter name shown in the GUI. Default "".
    init     -- Initial value. Default 0.
    res      -- Value resolution, "float" or "int". Default "float".
    dataOnly -- If True, used only for data storage, not GUI control.
                Default False.
"""

from pyo import SLMapFreq

"""
SLMapFreq(init=1000)

Preset SLMap for frequency parameters -- logarithmic scale, sensible
min/max for audio frequencies.

Params:
    init -- Initial frequency value in Hz. Default 1000.
"""

from pyo import SLMapQ

"""
SLMapQ(init=1)

Preset SLMap for filter resonance/Q parameters -- logarithmic scale,
sensible min/max for Q factors.

Params:
    init -- Initial Q value. Default 1.
"""
