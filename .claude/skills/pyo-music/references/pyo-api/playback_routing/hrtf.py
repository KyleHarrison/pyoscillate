"""Binaural/HRTF spatialization. Defined in pyo/lib/hrtf.py."""

__all__ = ['HRTFData', 'ImpulseResponseTables', 'HRTF', 'Binaural']

from pyo import HRTFData
"""
HRTFData(path=None, length=128)

"""

from pyo import ImpulseResponseTables
"""
ImpulseResponseTables(args, kwargs)

"""

from pyo import HRTF
"""
HRTF(input, azimuth=0.0, elevation=0.0, hrtfdata=None, mul=1, add=0)

Head-Related Transfert Function 3D spatialization.

HRTF describes how a given sound wave input is filtered by the
diffraction and reflection properties of the head, pinna, and
torso, before the sound reaches the transduction machinery of
the eardrum and inner ear.

This object takes a source signal and spatialises it in the 3D
space around a listener by convolving the source with stored
Head Related Impulse Response (HRIR) based filters. This works
under ideal listening context, ie. when listening with headphones.

HRTF generates two outpout streams per input stream.

Params:
    input     -- Input signal to process.
    azimuth   -- Position of the sound on the horizontal plane, between -180 and 180 degrees. Defaults to 0.
    elevation -- Position of the sound on the vertical plane, between -40 and 90 degrees. Defaults to 0.
    hrtfdata  -- Custom impulse responses dataset. Not used yet. Leave it to None.
"""

from pyo import Binaural
"""
Binaural(input, azimuth=0.0, elevation=0.0, azispan=0.0, elespan=0.0, mul=1, add=0)

Binaural 3D spatialization.

Binaural object provides a realtime 3D spatialization over two channels
by the mean of combining VBAP and HRTF algorithms.

VBAP is used to move the sound over a sixteen channels speaker setup
without artifact and its result signals are then processed with
Head-related Transfert Functions to mix them on a 3D sphere around a
virtual head.

This treatment is better perceived when listened with headphones!

Binaural generates two outpout streams per input stream.

Params:
    input     -- Input signal to process.
    azimuth   -- Position of the sound on the horizontal plane, between -180 and 180 degrees. Defaults to 0.
    elevation -- Position of the sound on the vertical plane, between 0 and 90 degrees. Defaults to 0.
    azispan   -- Spreading of the sound on the horizontal plane, between 0 and 1. Defaults to 0.
    elespan   -- Spreading of the sound on the vertical plane, between 0 and 1. Defaults to 0.
"""
