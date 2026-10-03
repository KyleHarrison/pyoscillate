"""Bounded live waveform/spectrum frames of one running signal, for a display.

Pyo's `Scope` and `Spectrum` call back with lists of `(x, y)` display
coordinates (not PCM samples or calibrated FFT bins), bounded by the
`WIDTH` x `HEIGHT` viewport below. Callbacks only store the newest frame
under a lock; the UI copies it out with `snapshot()` on its own schedule.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from threading import Lock

from pyo import Mix, PyoObject
from pyo.lib.analysis import Scope, Spectrum

Points = list[tuple[float, float]]


class LiveAnalyser:
    """One `Scope` + `Spectrum` pair on the left stream of a signal.

    Neither analyser calls `.out()`, so attaching one never changes what is
    heard. At most one pair is live at a time: `attach()` retires the previous
    pair first.
    """

    WIDTH = 256
    HEIGHT = 100
    WAVE_SECONDS = 0.05
    # explicit `setGain`: passing gain to the constructor does not scale
    WAVE_GAIN = 5.0
    FFT_SIZE = 2048
    POLL_SECONDS = 0.1
    LOW_FREQ = 20.0
    HIGH_FREQ = 20000.0
    # retired analysers kept referenced for this many later attaches/detaches
    # so their native streams outlive the stop request
    RETIRED_KEPT = 4

    def __init__(self) -> None:
        self._lock = Lock()
        self._generation = 0
        self._wave: Points = []
        self._spectrum: Points = []
        self._inputs: tuple[PyoObject, ...] = ()
        self._source: PyoObject | None = None
        self._left: PyoObject | None = None
        self._scope: Scope | None = None
        self._fft: Spectrum | None = None
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
        generation = self._generation
        self._scope = Scope(
            self._left,
            length=self.WAVE_SECONDS,
            function=partial(self._on_wave, generation),
        )
        self._scope.setWidth(self.WIDTH)
        self._scope.setHeight(self.HEIGHT)
        self._scope.setGain(self.WAVE_GAIN)
        self._fft = Spectrum(
            self._left,
            size=self.FFT_SIZE,
            function=partial(self._on_spectrum, generation),
        )
        self._fft.setWidth(self.WIDTH)
        self._fft.setHeight(self.HEIGHT)
        self._fft.setLowFreq(self.LOW_FREQ)
        self._fft.setHighFreq(self.HIGH_FREQ)
        self._fft.setFscaling(True)
        self._fft.setMscaling(True)
        self._fft.polltime(self.POLL_SECONDS)

    def detach(self) -> None:
        """Stop and forget the current analysers; late callbacks are ignored."""
        with self._lock:
            self._generation += 1
            self._wave = []
            self._spectrum = []
        if self._scope is not None and self._fft is not None:
            self._scope.stop()
            self._fft.stop()
            self._retired.append((self._scope, self._fft, self._left, self._source))
            del self._retired[: -self.RETIRED_KEPT]
        self._scope = self._fft = self._left = self._source = None
        self._inputs = ()

    def snapshot(self) -> tuple[Points, Points]:
        """Copies of the newest waveform and spectrum frames (empty if none)."""
        with self._lock:
            return list(self._wave), list(self._spectrum)

    def _on_wave(self, generation: int, data: list[Points]) -> None:
        with self._lock:
            if generation == self._generation and data:
                self._wave = list(data[0])

    def _on_spectrum(self, generation: int, data: list[Points]) -> None:
        with self._lock:
            if generation == self._generation and data:
                self._spectrum = list(data[0])
