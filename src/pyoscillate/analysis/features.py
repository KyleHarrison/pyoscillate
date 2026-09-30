"""Measurable correlates of a rendered patch.

These are the correlates named in the pyo-music timbre-descriptor reference:
level and clipping for loudness, onset and decay time for envelope, and
spectral centroid for brightness. Zero-crossing rate is kept as a cheap
cross-check; it tracks brightness on noisy material but not on tonal voices.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

import numpy as np

from pyoscillate.analysis.render import Render

FRAME_SECONDS = 0.005
SILENCE_DB = -90.0
# an onset is the envelope rising through this level below the render's loudest frame
ONSET_BELOW_PEAK_DB = 30.0
# the envelope must fall this far below a hit's peak before it counts as ended
DECAY_BELOW_PEAK_DB = 40.0


def to_db(value: float) -> float:
    return float(20 * np.log10(value)) if value > 0 else SILENCE_DB


def _rms(samples: np.ndarray) -> float:
    return float(np.sqrt(np.mean(samples**2))) if samples.size else 0.0


@dataclass(frozen=True)
class Hit:
    """One articulated event: onset, envelope peak, and where its tail ends."""

    onset: float
    peak_db: float
    # seconds from onset until the envelope falls DECAY_BELOW_PEAK_DB under the peak
    decay_time: float
    rms_db: float
    # power-weighted mean frequency of the hit - the brightness correlate
    centroid: float
    zero_crossing_rate: float


@dataclass(frozen=True)
class Features:
    peak: float
    rms_db: float
    clip_fraction: float
    hits: tuple[Hit, ...]


def envelope(render: Render, frame_seconds: float = FRAME_SECONDS) -> np.ndarray:
    """RMS level in dB per frame."""
    size = max(1, round(frame_seconds * render.sample_rate))
    count = -(-render.samples.size // size)
    padded = np.zeros(count * size)
    padded[: render.samples.size] = render.samples
    rms = np.sqrt(np.mean(padded.reshape(count, size) ** 2, axis=1))
    with np.errstate(divide="ignore"):
        return np.maximum(20 * np.log10(rms), SILENCE_DB)


def spectral_centroid(samples: np.ndarray, sample_rate: int) -> float:
    if not samples.size:
        return 0.0
    power = np.abs(np.fft.rfft(samples * np.hanning(samples.size))) ** 2
    total = power.sum()
    if total == 0:
        return 0.0
    frequencies = np.fft.rfftfreq(samples.size, 1 / sample_rate)
    return float((frequencies * power).sum() / total)


def features(render: Render, *, ceiling: float = 1.0) -> Features:
    samples = render.samples
    return Features(
        peak=float(np.max(np.abs(samples))) if samples.size else 0.0,
        rms_db=to_db(_rms(samples)),
        clip_fraction=float(np.mean(np.abs(samples) >= ceiling * 0.999))
        if samples.size
        else 0.0,
        hits=tuple(_hits(render)),
    )


def _hits(render: Render) -> list[Hit]:
    levels = envelope(render)
    if not levels.size:
        return []
    threshold = levels.max() - ONSET_BELOW_PEAK_DB
    frame = round(FRAME_SECONDS * render.sample_rate)
    hits = []
    index = 0
    while index < levels.size:
        if levels[index] < threshold or (index and levels[index - 1] >= threshold):
            index += 1
            continue
        start = index
        # the peak is the loudest frame before the envelope next dips under the onset threshold
        end = start
        while end < levels.size and levels[end] >= threshold:
            end += 1
        peak_index = start + int(np.argmax(levels[start:end]))
        # a quiet hit's floor can sit below the silence clamp, which the
        # clamped envelope would then never cross; silence ends a tail too
        floor = max(levels[peak_index] - DECAY_BELOW_PEAK_DB, SILENCE_DB)
        tail = peak_index
        while tail < levels.size and levels[tail] > floor:
            tail += 1
        segment = render.samples[start * frame : tail * frame]
        crossings = np.count_nonzero(np.diff(np.signbit(segment)))
        hits.append(
            Hit(
                onset=start * FRAME_SECONDS,
                peak_db=float(levels[peak_index]),
                decay_time=(tail - start) * FRAME_SECONDS,
                rms_db=to_db(_rms(segment)),
                centroid=spectral_centroid(segment, render.sample_rate),
                zero_crossing_rate=crossings * render.sample_rate / segment.size,
            )
        )
        # a noisy tail flickers around the onset threshold; skip past it so
        # it is never mistaken for a new hit
        index = max(end, tail)
    return hits


@dataclass(frozen=True)
class Window:
    """Level and brightness over one stretch of a continuous render."""

    start: float
    rms_db: float
    centroid: float
    # level in dB of each of BAND_EDGES' log-spaced bands
    bands: tuple[float, ...] = ()


def windows(render: Render, seconds: float = 0.25) -> tuple[Window, ...]:
    """Split a render into fixed windows, for patches with no hits to select.

    An ungated bed has no onsets, so its movement shows up as how much these
    windows differ from each other rather than as a per-hit decay.
    """
    size = max(1, round(seconds * render.sample_rate))
    return tuple(
        Window(
            start=start / render.sample_rate,
            rms_db=to_db(_rms(render.samples[start : start + size])),
            centroid=spectral_centroid(
                render.samples[start : start + size], render.sample_rate
            ),
            bands=band_levels(render.samples[start : start + size], render.sample_rate),
        )
        for start in range(0, render.samples.size - size + 1, size)
    )


# third-octave-ish bands from 60 Hz to 16 kHz: fine enough to see a notch or
# formant move, coarse enough that noise doesn't swamp it
BAND_EDGES = tuple(60 * 2 ** (index / 3) for index in range(25))


def band_levels(samples: np.ndarray, sample_rate: int) -> tuple[float, ...]:
    """Level in dB of each band between consecutive `BAND_EDGES`."""
    if not samples.size:
        return ()
    power = np.abs(np.fft.rfft(samples * np.hanning(samples.size))) ** 2
    frequencies = np.fft.rfftfreq(samples.size, 1 / sample_rate)
    levels = []
    for low, high in pairwise(BAND_EDGES):
        band = power[(frequencies >= low) & (frequencies < high)]
        levels.append(
            10 * np.log10(band.mean()) if band.size and band.mean() > 0 else SILENCE_DB
        )
    return tuple(float(level) for level in levels)


def spectral_movement(stretch: tuple[Window, ...]) -> float:
    """How much the spectrum's shape changes over time, in dB.

    Each band's level is taken relative to the window's overall level, so a
    plain swell doesn't count, and the result is the mean over bands of each
    band's standard deviation across the windows. Moving notches, formants
    or a breathing cutoff raise it; a still bed stays near the estimation
    noise floor.
    """
    levels = np.array([window.bands for window in stretch])
    relative = levels - levels.mean(axis=1, keepdims=True)
    return float(relative.std(axis=0).mean())
