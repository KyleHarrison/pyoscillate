"""Bounded live waveform/spectrum frames of one running signal, for a display.

Frames are `(x, y)` display points bounded by the `WIDTH` x `HEIGHT` viewport
below (y down), not PCM samples or calibrated FFT bins.

Nothing here runs Python on the audio thread. Pyo's own `Scope` and `Spectrum`
call back into Python from inside the audio callback, so whenever the UI
thread holds the GIL (a Flet repaint, say) the audio thread waits for it and
the buffer underruns - a sharp, intermittent crackle. Instead a `TableRec`
records the signal into a table entirely in C, and `snapshot()` - called from
the UI thread on its own schedule - reads the finished table, then re-arms the
recorder for the next frame.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from pyo import Mix, NewTable, PyoObject, TableRec

Points = list[tuple[float, float]]


class LiveAnalyser:
    """One recorded frame of the left stream of a signal, turned into a
    waveform and a spectrum on demand.

    Never calls `.out()`, so attaching one never changes what is heard. At
    most one signal is monitored at a time: `attach()` retires the previous
    recorder first.
    """

    WIDTH = 256
    HEIGHT = 100
    WAVE_SECONDS = 0.05
    # the waveform is amplified for display only
    WAVE_GAIN = 5.0
    FFT_SIZE = 2048
    LOW_FREQ = 20.0
    HIGH_FREQ = 20000.0
    # spectrum floor (dB below full scale) drawn as the bottom of the plot
    FLOOR_DB = -90.0
    # retired recorders kept referenced for this many later attaches/detaches
    # so their native streams outlive the stop request
    RETIRED_KEPT = 4

    def __init__(self) -> None:
        self._wave: Points = []
        self._spectrum: Points = []
        self._inputs: tuple[PyoObject, ...] = ()
        self._source: PyoObject | None = None
        self._left: PyoObject | None = None
        self._table: NewTable | None = None
        self._recorder: TableRec | None = None
        self._rate = 44100.0
        self._retired: list[tuple[object, ...]] = []

    def monitors(self, signals: Sequence[PyoObject]) -> bool:
        """Whether exactly these signals (by identity - pyo overloads `==`)
        are what is attached now; an empty sequence means "detached"."""
        return len(signals) == len(self._inputs) and all(
            a is b for a, b in zip(signals, self._inputs)
        )

    def attach_sum(self, signals: Sequence[PyoObject]) -> None:
        """Monitor the sum of `signals` (stereo, so left sums with left)."""
        self.attach(Mix(list(signals), voices=2), inputs=tuple(signals))

    def attach(
        self,
        signal: PyoObject,
        *,
        inputs: tuple[PyoObject, ...] | None = None,
    ) -> None:
        """Monitor `signal`'s left stream, replacing any previous attachment.
        `inputs` names what `signal` was built from (default: itself) for
        `monitors()`."""
        self.detach()
        self._inputs = (signal,) if inputs is None else inputs
        self._source = signal
        self._left = signal[0]
        self._rate = float(signal.getServer().getSamplingRate())
        # long enough for the FFT window and the waveform's span
        frames = max(self.FFT_SIZE, int(self.WAVE_SECONDS * self._rate))
        self._table = NewTable(length=frames / self._rate)
        self._recorder = TableRec(self._left, self._table, fadetime=0)
        self._recorder.play()

    def detach(self) -> None:
        """Stop and forget the current recorder."""
        self._wave = []
        self._spectrum = []
        if self._recorder is not None and self._table is not None:
            self._recorder.stop()
            self._retired.append(
                (self._recorder, self._table, self._left, self._source)
            )
            del self._retired[: -self.RETIRED_KEPT]
        self._recorder = self._table = self._left = self._source = None
        self._inputs = ()

    def snapshot(self) -> tuple[Points, Points]:
        """The newest waveform and spectrum frames (empty if none yet).

        Reads the frame the recorder has finished since the last call and
        starts the next one. Call it from the UI thread, a few times a second:
        the recording takes well under that (one FFT window), so a frame is
        always complete by the next call.
        """
        if self._recorder is None or self._table is None:
            return [], []
        samples = np.asarray(self._table.getTable(), dtype=np.float64)
        self._recorder.play()
        if samples.size and np.any(samples):
            self._wave = self._waveform(samples)
            self._spectrum = self._spectrum_of(samples)
        return list(self._wave), list(self._spectrum)

    def _waveform(self, samples: np.ndarray) -> Points:
        span = int(self.WAVE_SECONDS * self._rate)
        window = samples[:span]
        picks = np.linspace(0, window.size - 1, self.WIDTH).astype(int)
        levels = np.clip(window[picks] * self.WAVE_GAIN, -1.0, 1.0)
        ys = self.HEIGHT / 2 - levels * self.HEIGHT / 2
        return [(float(x), float(y)) for x, y in zip(range(self.WIDTH), ys)]

    def _spectrum_of(self, samples: np.ndarray) -> Points:
        window = samples[: self.FFT_SIZE]
        if window.size < self.FFT_SIZE:
            window = np.pad(window, (0, self.FFT_SIZE - window.size))
        magnitude = np.abs(np.fft.rfft(window * np.hanning(self.FFT_SIZE)))
        # a full-scale sine reads 0 dB (a Hann window's gain is 1/2)
        decibels = 20 * np.log10(magnitude / (self.FFT_SIZE / 4) + 1e-12)
        freqs = np.fft.rfftfreq(self.FFT_SIZE, 1 / self._rate)
        log_freqs = np.geomspace(self.LOW_FREQ, self.HIGH_FREQ, self.WIDTH)
        shown = np.interp(log_freqs, freqs, decibels)
        height = np.clip((shown - self.FLOOR_DB) / -self.FLOOR_DB, 0.0, 1.0)
        ys = self.HEIGHT - height * self.HEIGHT
        return [(float(x), float(y)) for x, y in zip(range(self.WIDTH), ys)]
