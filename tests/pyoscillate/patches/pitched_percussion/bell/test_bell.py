"""Perceptual contract for the bell: hits land where the pattern says, Strike
brightens the onset, Ring sets how long a note lasts, and the loudest corner
of the range stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The first hit sits under `Patch.start()`'s fade-in, so tests
measure later ones.
"""

import unittest
from functools import cache

from pyoscillate.analysis.features import Features, Hit, features, spectral_centroid
from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.pitched_percussion.bell import bell
from pyoscillate.theory.intervals import Melody

MODULE = "pyoscillate.patches.pitched_percussion.bell.bell"
BPM = 120
SIXTEENTH = 60 / BPM / 4
ONSET_TOLERANCE = 0.02


@cache
def _render(**params: float | str) -> Render:
    return render(MODULE, params, seconds=2.3, bpm=BPM)


def _onset_centroid(result: Render, onset: float, seconds: float = 0.06) -> float:
    """Brightness of the strike itself: the first `seconds` of a note."""
    start = round(onset * result.sample_rate)
    samples = result.samples[start : start + round(seconds * result.sample_rate)]
    return spectral_centroid(samples, result.sample_rate)


@cache
def _features(seconds: float = 4.0, **params: float | str) -> Features:
    return features(render(MODULE, params, seconds=seconds, bpm=BPM))


def _hit(result: Features, onset: float) -> Hit:
    for hit in result.hits:
        if abs(hit.onset - onset) < ONSET_TOLERANCE:
            return hit
    raise AssertionError(
        f"no hit near {onset:.3f} s in {[h.onset for h in result.hits]}"
    )


class BellHealthTests(unittest.TestCase):
    def test_hits_land_on_the_pattern(self) -> None:
        # the first hit is under the fade-in, so start from the second
        expected = [step * SIXTEENTH for step in sorted(Melody.BELL_FIGURE.steps)][1:]
        for style in bell.STYLES:
            with self.subTest(style=style):
                result = _features(style=style, ring=0.3)
                for onset in expected:
                    _hit(result, onset)

    def test_loudest_corner_is_clean_at_default_volume(self) -> None:
        for style in bell.STYLES:
            for root_freq in (
                bell.Bell.root_freq.spec.minimum,
                bell.Bell.root_freq.spec.maximum,
            ):
                for strike in (
                    bell.Bell.strike.spec.minimum,
                    bell.Bell.strike.spec.maximum,
                ):
                    with self.subTest(style=style, root_freq=root_freq, strike=strike):
                        render_ = render(
                            MODULE,
                            {
                                "style": style,
                                "root_freq": root_freq,
                                "strike": strike,
                                "ring": bell.Bell.ring.spec.maximum,
                            },
                            seconds=4.0,
                            bpm=BPM,
                        )
                        loudest = features(render_, ceiling=PATCH_OUTPUT_CEILING)

                        self.assertEqual(loudest.clip_fraction, 0.0)


class BellControlTests(unittest.TestCase):
    def test_strike_brightens_the_onset(self) -> None:
        # 2.0 s is step 16, the second bar's first note. The fm index clears
        # within the note, so the promise is about its start, not the average
        for style in bell.STYLES:
            with self.subTest(style=style):
                soft = _onset_centroid(_render(style=style, strike=0), 2.0)
                hard = _onset_centroid(_render(style=style, strike=1), 2.0)

                self.assertGreater(hard, soft * 1.5)

    def test_ring_sets_how_long_a_note_lasts(self) -> None:
        # at Rate -2 the pattern steps in quarter notes, so the note at step 6
        # (3.0 s) has 3 s to itself before step 12
        onset = 6 * 4 * SIXTEENTH
        for style in bell.STYLES:
            for ring in (0.5, 1.5):
                with self.subTest(style=style, ring=ring):
                    hit = _hit(
                        _features(seconds=5.5, style=style, ring=ring, rate=-2), onset
                    )

                    # Ring is the prime's (or the envelope's) time to -40 dB;
                    # the chime's hum outlasts it by up to 0.5^-DECAY_SLOPE
                    longest = ring * bell.PARTIALS[0] ** -bell.DECAY_SLOPE
                    self.assertGreater(hit.decay_time, ring * 0.7)
                    self.assertLess(hit.decay_time, longest * 1.2)


if __name__ == "__main__":
    unittest.main()
