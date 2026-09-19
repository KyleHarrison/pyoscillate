"""Phase Vocoder -- higher-level spectral manipulation (time-stretch,
pitch-shift, cross-synthesis) built on top of the Fast Fourier Transform
category (see fourier.py). Not used by this project yet.
"""

__all__ = ["PVAnal", "PVSynth", "PVTranspose", "PVMorph"]

from pyo import PVAnal

"""
PVAnal(input, size=1024, overlaps=4, wintype=2, callback=None)

Phase vocoder analysis object -- the entry point of a PV chain, producing a
`PVStream` for PV-aware objects downstream.

Params:
    input    -- Signal to analyze.
    size     -- FFT size in samples (power of 2). Default 1024.
    overlaps -- Number of overlapped analysis windows. Default 4.
    wintype  -- Windowing function. Default 2.
    callback -- Optional function called with (magnitudes, frequencies) each
                frame. Default None.
"""

from pyo import PVSynth

"""
PVSynth(input, wintype=2, mul=1, add=0)

Phase vocoder synthesis object -- converts a PV stream back to an audio
signal, the counterpart to PVAnal.

Params:
    input   -- A PVStream (e.g. from PVAnal or another PV object).
    wintype -- Windowing function for resynthesis. Default 2.
    mul     -- Output multiplier. Default 1.
    add     -- Output additive value. Default 0.
"""

from pyo import PVTranspose

"""
PVTranspose(input, transpo=1)

Transposes the frequency components of a PV stream without changing its
duration.

Params:
    input   -- A PVStream to transpose.
    transpo -- Transposition factor (1 = no change). Default 1.
"""

from pyo import PVMorph

"""
PVMorph(input, input2, fade=0)

Morphs between two PV streams' magnitude and frequency content.

Params:
    input  -- First PVStream.
    input2 -- Second PVStream.
    fade   -- Morph position, 0 (all input) to 1 (all input2). Default 0.
"""
