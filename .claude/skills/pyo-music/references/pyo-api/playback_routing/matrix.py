"""Matrix Processing / Matrices -- the 2D equivalent of Tables (see
../core/03_tables.py); store and read 2D data (e.g. sonograms) for
granular/scanned synthesis. Not used by this project yet.
"""

__all__ = ['NewMatrix', 'MatrixPointer', 'MatrixRec', 'MatrixMorph']

from pyo import NewMatrix

"""
NewMatrix(width, height, init=None)

Creates an empty 2D matrix ready for recording.

Params:
    width  -- Matrix width in samples.
    height -- Matrix height in samples.
    init   -- Optional list of lists to initialize the matrix with.
              Default None.
"""

from pyo import MatrixPointer

"""
MatrixPointer(matrix, x, y, mul=1, add=0)

Reads a matrix's content at a 2D pointer position.

Params:
    matrix -- The PyoMatrixObject to read.
    x      -- Horizontal read position, 0-1.
    y      -- Vertical read position, 0-1.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import MatrixRec

"""
MatrixRec(input, matrix, fadetime=0)

Records a signal into a previously created NewMatrix.

Params:
    input    -- Signal to record.
    matrix   -- Destination NewMatrix.
    fadetime -- Fade in/out time at the recording boundaries, in seconds.
                Default 0.
"""

from pyo import MatrixMorph

"""
MatrixMorph(input, matrix, sources)

Morphs between multiple matrices based on a control signal.

Params:
    input   -- Morph position signal, indexing into `sources`.
    matrix  -- Destination matrix that receives the morphed content.
    sources -- List of source matrices to morph between.
"""
