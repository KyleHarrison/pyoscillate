"""Spectral and modulation measurements of a window of samples.

The correlates a perceptual test reads beyond `features`: how much energy sits
in a band, where the strongest partial is, how peaked the spectrum is around a
pitch, and how far the level or the pitch swings. Like `features`, they
measure and never decide.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import ClassVar

import numpy as np


@dataclass(frozen=True)
class Spectrum:
    """The power spectrum of a window of samples, Hann-windowed and
    zero-padded so a partial lands within a fraction of a hertz."""

    power: np.ndarray
    freqs: np.ndarray

    PADDING: ClassVar[int] = 8

    @classmethod
    def of(cls, samples: np.ndarray, sample_rate: int) -> Spectrum:
        size = cls.PADDING * len(samples)
        power = np.abs(np.fft.rfft(samples * np.hanning(len(samples)), size)) ** 2
        return cls(power, np.fft.rfftfreq(size, 1 / sample_rate))

    def band(self, low: float, high: float) -> float:
        """The power between `low` and `high` Hz."""
        return float(self.power[(self.freqs >= low) & (self.freqs < high)].sum())

    def share(self, low: float, high: float) -> float:
        """The fraction of the power between `low` and `high` Hz."""
        return self.band(low, high) / float(self.power.sum())

    def centroid(self) -> float:
        return float((self.power * self.freqs).sum() / self.power.sum())

    def peak_near(self, freq: float, width: float) -> float:
        """The strongest power within `width` Hz of `freq`."""
        return float(self.power[abs(self.freqs - freq) <= width].max())

    def floor_near(self, freq: float, width: float) -> float:
        """The median power within `width` Hz of `freq`: the level of the
        spectrum around a partial, whatever the partial is doing."""
        return float(np.median(self.power[abs(self.freqs - freq) <= width]))

    def partial_levels(self, freq: float, count: int, width: float = 4.0) -> np.ndarray:
        """The level in dB of each of the first `count` multiples of `freq`,
        each the strongest power within `width` Hz of it."""
        return np.array(
            [
                10 * np.log10(self.peak_near(freq * n, width))
                for n in range(1, count + 1)
            ]
        )

    def peak_frequency(self, low: float, high: float) -> float:
        """The frequency of the strongest partial between `low` and `high` Hz,
        interpolated between bins."""
        inside = np.flatnonzero((self.freqs >= low) & (self.freqs < high))
        index = int(inside[np.argmax(self.power[inside])])
        left, centre, right = np.log(self.power[index - 1 : index + 2] + 1e-30)
        offset = 0.5 * (left - right) / (left - 2 * centre + right)
        return float(self.freqs[index] + offset * (self.freqs[1] - self.freqs[0]))


class Wobble:
    """How far a stretch of samples swings in level or in pitch."""

    @staticmethod
    def level(samples: np.ndarray, sample_rate: int, window: float = 0.01) -> float:
        """The swing of the level: the spread between the loudest and the
        quietest `window` seconds, as a fraction of the mean."""
        size = round(window * sample_rate)
        count = len(samples) // size
        rms = np.sqrt((samples[: count * size].reshape(count, size) ** 2).mean(axis=1))
        return float((rms.max() - rms.min()) / rms.mean())

    @staticmethod
    def level_rate(
        samples: np.ndarray,
        sample_rate: int,
        window: float = 0.01,
        low: float = 0.5,
        high: float = 15.0,
    ) -> float:
        """The speed, in Hz, at which the level swings: the strongest rate
        between `low` and `high` in the envelope of `window`-second frames."""
        size = round(window * sample_rate)
        count = len(samples) // size
        rms = np.sqrt((samples[: count * size].reshape(count, size) ** 2).mean(axis=1))
        padded = 16 * count
        power = np.abs(np.fft.rfft((rms - rms.mean()) * np.hanning(count), padded))
        rates = np.fft.rfftfreq(padded, window)
        inside = (rates >= low) & (rates <= high)
        return float(rates[inside][np.argmax(power[inside])])

    @staticmethod
    def pitch(
        samples: np.ndarray,
        sample_rate: int,
        low: float,
        high: float,
        window: float = 0.06,
    ) -> float:
        """The swing of the pitch in cents: the strongest partial between
        `low` and `high` Hz, tracked over `window`-second frames, from its
        lowest to its highest."""
        size = round(window * sample_rate)
        pitches = [
            Spectrum.of(samples[start : start + size], sample_rate).peak_frequency(
                low, high
            )
            for start in range(0, len(samples) - size + 1, size // 2)
        ]
        return 1200 * math.log2(max(pitches) / min(pitches))
