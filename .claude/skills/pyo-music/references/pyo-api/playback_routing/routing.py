"""Routing -- route and position signals across channels: panning, mixing,
crossfading between sources. Not used by this project yet.
"""

__all__ = ["Mixer", "Pan", "SPan", "Selector", "Switch", "Binaural"]

from pyo import Mixer

"""
Mixer(outs=2, chnls=2, time=0.025)

Audio mixer -- routes any number of inputs to any number of outputs, each
with an independently controllable amplitude.

Params:
    outs  -- Number of output buses. Default 2.
    chnls -- Number of channels per bus. Default 2.
    time  -- Ramp time for amplitude changes, in seconds. Default 0.025.
"""

from pyo import Pan

"""
Pan(input, outs=2, pan=0, spread=0.5, mul=1, add=0)

Cosine panner across multiple output channels, with control over spread.

Params:
    input  -- Signal to pan.
    outs   -- Number of output channels. Default 2.
    pan    -- Pan position, 0-1. Default 0.
    spread -- Spread of the signal across channels, 0-1. Default 0.5.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import SPan

"""
SPan(input, outs=2, pan=0.5, mul=1, add=0)

Simple equal-power stereo panner.

Params:
    input -- Signal to pan.
    outs  -- Number of output channels. Default 2.
    pan   -- Pan position, 0-1. Default 0.5.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Selector

"""
Selector(inputs, voice=0, mul=1, add=0)

Interpolates between multiple input sources to produce a single output,
crossfading as `voice` changes.

Params:
    inputs -- List of input signals to select between.
    voice  -- Selector position (fractional values crossfade between
              neighbours). Default 0.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import Switch

"""
Switch(input, outs=2, voice=0, mul=1, add=0)

Routes a single input to one of several outputs, interpolating as `voice`
changes.

Params:
    input -- Signal to route.
    outs  -- Number of possible outputs. Default 2.
    voice -- Output position (fractional values crossfade). Default 0.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""

from pyo import Binaural

"""
Binaural(input, azimuth=0, elevation=0, mul=1, add=0)

Binaural 3D spatialization combining VBAP and HRTF, for headphone
listening.

Params:
    input     -- Signal to spatialize.
    azimuth   -- Horizontal angle in degrees, -180 to 180. Default 0.
    elevation -- Vertical angle in degrees, -40 to 90. Default 0.
    mul       -- Output multiplier. Default 1.
    add       -- Output additive value. Default 0.
"""
