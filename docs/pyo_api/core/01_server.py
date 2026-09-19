"""1. Server -- the audio engine.

One `Server` per program. It owns the audio device connection and the DSP
loop; every other pyo object needs a booted, started server to produce
sound.
"""

__all__ = ["Server"]

from pyo import Server

"""
Server(sr=44100, nchnls=2, buffersize=256, duplex=1, winhost="portaudio",
       audio="portaudio", jackname="pyo")

Main audio engine. Configure it, `.boot()` to open the audio device, then
`.start()` to begin processing.

Params:
    sr          -- Sampling rate in Hz. Default 44100.
    nchnls      -- Number of output channels. Default 2.
    buffersize  -- Number of samples per audio buffer (latency vs. stability
                   tradeoff). Default 256.
    duplex      -- 1 for input+output, 0 for output only. Default 1.
    winhost     -- Windows audio host API. Default "portaudio".
    audio       -- Audio backend ("portaudio", "jack", "coreaudio", "offline",
                   "offline_nb"). Default "portaudio".
    jackname    -- Client name when audio="jack". Default "pyo".

Key methods:
    boot()   -- Opens the audio stream.
    start()  -- Starts the DSP callback (sound begins).
    stop()   -- Stops the DSP callback.
    shutdown() -- Closes the audio stream.
"""
