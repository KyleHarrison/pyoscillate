"""Soundfile Players -- play back audio files from disk, with speed/pitch
control and marker-based looping. Not used by this project yet.
"""

__all__ = ['SfPlayer', 'SfMarkerLooper', 'SfMarkerShuffler']

from pyo import SfPlayer

"""
SfPlayer(path, speed=1, loop=False, offset=0, interp=2, mul=1, add=0)

Plays back a soundfile from disk; `speed` controls both playback rate and
pitch.

Params:
    path   -- Path to the soundfile.
    speed  -- Playback speed/transposition factor. Default 1.
    loop   -- Whether to loop playback. Default False.
    offset -- Starting position in the file, in seconds. Default 0.
    interp -- Interpolation method (0=none, 1=linear, 2=cosine, 3=cubic,
              4=spline). Default 2.
    mul    -- Output multiplier. Default 1.
    add    -- Output additive value. Default 0.
"""

from pyo import SfMarkerLooper

"""
SfMarkerLooper(path, speed=1, markers=0, mul=1, add=0)

Plays a soundfile, looping between marker points stored in the file's
AIFF/WAVE header.

Params:
    path    -- Path to the soundfile (must contain markers).
    speed   -- Playback speed/transposition factor. Default 1.
    markers -- Index of the marker pair to loop between. Default 0.
    mul     -- Output multiplier. Default 1.
    add     -- Output additive value. Default 0.
"""

from pyo import SfMarkerShuffler

"""
SfMarkerShuffler(path, speed=1, mul=1, add=0)

Plays a soundfile, jumping between its marker points in random order.

Params:
    path  -- Path to the soundfile (must contain markers).
    speed -- Playback speed/transposition factor. Default 1.
    mul   -- Output multiplier. Default 1.
    add   -- Output additive value. Default 0.
"""
