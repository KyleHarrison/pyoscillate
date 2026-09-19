"""2D buffer (matrix) storage. Defined in pyo/lib/matrix.py."""

__all__ = ['NewMatrix']

from pyo import NewMatrix
"""
NewMatrix(width, height, init=None)

Create a new matrix ready for recording.

Optionally, the matrix can be filled with the contents of the
`init` parameter.

See :py:class:`MatrixRec` to write samples in the matrix.

Params:
    width  -- Desired matrix width in samples.
    height -- Desired matrix height in samples.
    init   -- Initial matrix. Defaults to None.
"""
