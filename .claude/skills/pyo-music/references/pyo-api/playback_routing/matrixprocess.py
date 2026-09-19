"""Objects that record into or read from a NewMatrix. All defined in pyo/lib/matrixprocess.py."""

__all__ = ['MatrixRec', 'MatrixRecLoop', 'MatrixPointer', 'MatrixMorph']

from pyo import MatrixRec
"""
MatrixRec(input, matrix, fadetime=0, delay=0)

MatrixRec records samples into a previously created NewMatrix.

See :py:class:`NewMatrix` to create an empty matrix.

The play method is not called at the object creation time. It starts
the recording into the matrix, row after row, until the matrix is full.
Calling the play method again restarts the recording and overwrites
previously recorded samples. The stop method stops the recording.
Otherwise, the default behaviour is to record through the end of the matrix.

Params:
    input    -- Audio signal to write in the matrix.
    matrix   -- The matrix where to write samples.
    fadetime -- Fade time at the beginning and the end of the recording in seconds. Defaults to 0.
    delay    -- Delay time, in samples, before the recording begins. Available at initialization time only. Defaults to 0.
"""

from pyo import MatrixRecLoop
"""
MatrixRecLoop(input, matrix)

MatrixRecLoop records samples in loop into a previously created NewMatrix.

See :py:class:`NewMatrix` to create an empty matrix.

MatrixRecLoop records samples into the matrix, row after row, until
the matrix is full and then loop back to the beginning.

Params:
    input  -- Audio signal to write in the matrix.
    matrix -- The matrix where to write samples.
"""

from pyo import MatrixPointer
"""
MatrixPointer(matrix, x, y, mul=1, add=0)

Matrix reader with control on the 2D pointer position.

Params:
    matrix -- Matrix containing the waveform samples.
    x      -- Normalized X position in the matrix between 0 and 1.
    y      -- Normalized Y position in the matrix between 0 and 1.
"""

from pyo import MatrixMorph
"""
MatrixMorph(input, matrix, sources)

Morphs between multiple PyoMatrixObjects.

Uses an index into a list of PyoMatrixObjects to morph between adjacent
matrices in the list. The resulting morphed function is written into the
`matrix` object at the beginning of each buffer size. The matrices in the
list and the resulting matrix must be equal in size.

Params:
    input   -- Morphing index between 0 and 1. 0 is the first matrix in the list and 1 is the last.
    matrix  -- The matrix where to write morphed function.
    sources -- List of matrices to interpolate from.
"""
