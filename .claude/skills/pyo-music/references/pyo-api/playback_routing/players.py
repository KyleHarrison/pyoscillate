"""Soundfile playback objects. All defined in pyo/lib/players.py."""

__all__ = ['SfPlayer', 'SfMarkerShuffler', 'SfMarkerLooper']

from pyo import SfPlayer
"""
SfPlayer(path, speed=1, loop=False, offset=0, interp=2, mul=1, add=0)

Soundfile player.

Reads audio data from a file using one of several available interpolation
types. User can alter its pitch with the `speed` attribute. The object
takes care of sampling rate conversion to match the Server sampling
rate setting.

Params:
    path   -- Full path name of the sound to read.
    speed  -- Transpose the pitch of input sound by this factor. Defaults to 1. 1 is the original pitch, lower values play sound slower, and higher values play sound faster. Negative values results in playing sound backward. Although the `speed` attribute accepts audio rate signal, its value is updated only once per buffer size.
    loop   -- If set to True, sound will play in loop. Defaults to False.
    offset -- Time in seconds of input sound to be skipped, assuming speed = 1. If the object is already playing (and play() is implicitly called at the object creation), this value will be effective only on the next loop point. Defaults to 0.
    interp -- Interpolation type. Defaults to 2. 1. no interpolation 2. linear 3. cosinus 4. cubic
"""

from pyo import SfMarkerShuffler
"""
SfMarkerShuffler(path, speed=1, interp=2, mul=1, add=0)

AIFF with markers soundfile shuffler.

Reads audio data from a AIFF file using one of several available
interpolation types. User can alter its pitch with the `speed`
attribute. The object takes care of sampling rate conversion to
match the Server sampling rate setting.

The reading pointer randomly choose a marker (from the MARK chunk
in the header of the AIFF file) as its starting point and reads
the samples until it reaches the following marker. Then, it choose
another marker and reads from the new position and so on...

Params:
    path   -- Full path name of the sound to read. Can't e changed after initialization.
    speed  -- Transpose the pitch of input sound by this factor. Defaults to 1. 1 is the original pitch, lower values play sound slower, and higher values play sound faster. Negative values results in playing sound backward. Although the `speed` attribute accepts audio rate signal, its value is updated only once per buffer size.
    interp -- Choice of the interpolation method. Defaults to 2. 1. no interpolation 2. linear 3. cosinus 4. cubic
"""

from pyo import SfMarkerLooper
"""
SfMarkerLooper(path, speed=1, mark=0, interp=2, mul=1, add=0)

AIFF with markers soundfile looper.

Reads audio data from a AIFF file using one of several available
interpolation types. User can alter its pitch with the `speed`
attribute. The object takes care of sampling rate conversion to
match the Server sampling rate setting.

The reading pointer loops a specific marker (from the MARK chunk
in the header of the AIFF file) until it received a new integer
in the `mark` attribute.

Params:
    path   -- Full path name of the sound to read.
    speed  -- Transpose the pitch of input sound by this factor. Defaults to 1. 1 is the original pitch, lower values play sound slower, and higher values play sound faster. Negative values results in playing sound backward. Although the `speed` attribute accepts audio rate signal, its value is updated only once per buffer size.
    mark   -- Integer denoting the marker to loop, in the range 0 -> len(getMarkers()). Defaults to 0.
    interp -- Choice of the interpolation method. Defaults to 2. 1. no interpolation 2. linear 3. cosinus 4. cubic
"""
