"""Perceptual contract for the hover bass: Space (reverb size) sustains more
tail energy, Breath creates a slow amplitude swell rather than a flat level,
and the loudest corner stays clean despite a continuous, densely-retriggered
source through a long reverb tail. Also checks `profiles.HOVER`'s own data,
since every audio assertion above depends on it being what the rack's
README claims (a four-bar, steady 8th-note pulse stepping E-F-G-A once per
bar).

Brightness (the low-pass cutoff) is deliberately left untested: with the
near-sine `HOVER` harmonics, most of the signal's energy is the fundamental
regardless of cutoff, so a direction assertion would be asserting a proxy too
weak to trust - see tests/AGENTS.md ("leave it untested rather than asserting
a weak proxy").

The clock-stopped silence contract (`test_gated_patches.GATED_PATCHES`) isn't
duplicated here: it's a pre-existing, already-tracked failure shared by every
`GatedVoice` patch (`Trig()` fires once at start-up regardless of `play()`),
not something introduced by this patch.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md.

Findings
========

1. The loudest corner (max Space/Breath/Brightness) clipped
-------------------------------------------------------------
Error:
    At the module's original the `volume` default (0.7), `reverb_size=1.0,
    breath=0.6, cutoff=900` measured `clip_fraction` 0.31 - the patch
    limiter's `Compress`+`Clip` couldn't tame it.
Cause:
    A continuous, densely-retriggered source (a hit every 2 sixteenths)
    through a long `Freeverb` tail builds up more sustained energy than a
    single struck note, unlike the patches most of this family's default
    volumes were tuned against.
Change:
    the `volume` default lowered to 0.22 (checked offline: clean at the same
    extreme settings, with headroom to spare).
Status:
    fixed - src/pyoscillate/patches/tonal/bass/hover.py.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features, spectral_centroid
from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.bass import hover
from pyoscillate.theory.phrase import BassLines

MODULE = "pyoscillate.patches.tonal.bass.hover"
BPM = 240
SIXTEENTH = 60 / BPM / 4
BAR = SIXTEENTH * 16
# the clock fires one audio buffer after the tick
LATENCY = 0.006


@cache
def _render(seconds: float = 1.0, **params: float) -> Render:
    return render(MODULE, params, seconds=seconds, bpm=BPM)


def _window(result: Render, start: float, end: float) -> np.ndarray:
    rate = result.sample_rate
    return result.samples[round(start * rate) : round(end * rate)]


def _note(
    result: Render, step: int, start: float = 0.0, end: float = 0.05
) -> np.ndarray:
    onset = step * SIXTEENTH + LATENCY
    return _window(result, onset + start, onset + end)


def _rms(samples: np.ndarray) -> float:
    return float(np.sqrt(np.mean(samples**2))) if len(samples) else 0.0


def _centroid(samples: np.ndarray) -> float:
    return spectral_centroid(samples, 44100)


class HoverMelodyTests(unittest.TestCase):
    def test_steps_e_f_g_a_once_per_bar(self) -> None:
        steps = BassLines.BASS_HOVER.values
        self.assertEqual(steps[0], 0)
        self.assertEqual(steps[16], 1)
        self.assertEqual(steps[32], 3)
        self.assertEqual(steps[48], 5)

    def test_pulses_every_other_step(self) -> None:
        steps = BassLines.BASS_HOVER.values
        for step in range(BassLines.BASS_HOVER.cycle):
            self.assertEqual(step in steps, step % 2 == 0)


class HoverBassHealthTests(unittest.TestCase):
    def test_loudest_corner_is_clean_at_default_volume(self) -> None:
        loudest = features(
            _render(
                cutoff=hover.BassHover.cutoff.spec.maximum,
                reverb_size=hover.BassHover.reverb_size.spec.maximum,
                breath=hover.BassHover.breath.spec.maximum,
            ),
            ceiling=PATCH_OUTPUT_CEILING,
        )

        self.assertEqual(loudest.clip_fraction, 0.0)


class HoverBassControlTests(unittest.TestCase):
    def test_space_sustains_more_tail_energy(self) -> None:
        # well past the envelope's own decay, so what's left is reverb tail
        tight = _note(
            _render(reverb_size=hover.BassHover.reverb_size.spec.minimum), 0, 0.2, 0.3
        )
        spacious = _note(
            _render(reverb_size=hover.BassHover.reverb_size.spec.maximum), 0, 0.2, 0.3
        )

        self.assertGreater(_rms(spacious), _rms(tight) * 1.15)

    def test_breath_creates_a_slow_amplitude_swell(self) -> None:
        # one breath cycle is 4 bars; the `Sine` starts at phase 0 (value
        # `add`, the swell's midpoint), so its peak (`add + mul`) falls a
        # quarter-cycle in and its trough (`add - mul`) three-quarters in
        cycle = BAR * 4
        flat = _render(seconds=cycle, breath=hover.BassHover.breath.spec.minimum)
        swelling = _render(seconds=cycle, breath=hover.BassHover.breath.spec.maximum)

        flat_peak = _rms(_window(flat, cycle * 0.2, cycle * 0.3))
        flat_trough = _rms(_window(flat, cycle * 0.7, cycle * 0.8))
        swelling_peak = _rms(_window(swelling, cycle * 0.2, cycle * 0.3))
        swelling_trough = _rms(_window(swelling, cycle * 0.7, cycle * 0.8))

        flat_ratio = flat_peak / flat_trough if flat_trough else float("inf")
        swelling_ratio = (
            swelling_peak / swelling_trough if swelling_trough else float("inf")
        )

        self.assertGreater(swelling_ratio, flat_ratio * 1.3)


if __name__ == "__main__":
    unittest.main()
