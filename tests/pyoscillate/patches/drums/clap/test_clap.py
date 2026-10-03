"""Perceptual contract for the clap: render it offline and check that each
control moves its measurable correlate the way its label promises.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md.

Findings
========

1. Unscheduled hit when the patch starts
----------------------------------------
Error:
    A started clap made a clap-shaped hit at ~0.025 s. Nothing had been
    scheduled yet: its first backbeat is at 0.5 s. The hit was ~15 dB under
    a real one, softened only by the `Patch.start()` fade-in. With the clock
    never started, every other gated patch did the same. The loudest were
    chord (peak 0.178, almost at the output ceiling), kick (0.108) and bass (0.067).
Cause:
    pyo's `Trig()` emits one trigger the first time it is computed, whether
    or not `play()` has been called. Every patch that builds a bare `Trig()`
    and later calls `trigger.play()` from its sequencer therefore fires once
    at start-up.
Change:
    Construct the trigger as `Trig().stop()` so it only fires on `play()`.
    Verified offline: a stopped `Trig` stays silent, and `play()` still
    fires at full level. This applies to all 12 `Trig`-driven patches; see
    tests/pyoscillate/patches/test_gated_patches.py.
Status:
    fix pending - test_silent_before_the_first_scheduled_hit fails until then.

2. The top of the Presence range is hard-clipped
------------------------------------------------
Error:
    At the default volume (`Clap.volume` default 0.28), Presence above
    ~0.4 drives the burst into the `PATCH_OUTPUT_CEILING` (0.18) clip. At the
    slider's maximum (0.6), the transient is flattened for ~2 ms per hit.
    The loudest case is the brightest Brightness (4000).
Cause:
    The pre-limiter peak is ~1.6-1.9 x Presence, depending on Brightness
    (`MAKEUP_GAIN` times the band-pass resonance). The Presence slider's
    range was chosen without that gain or the output ceiling in mind.
    `Compress` never catches it, because its -1 dBFS threshold sits far
    above the 0.18 ceiling, so the final `Clip` does the work.
Change:
    Lower the Presence slider maximum from 0.6 to 0.3, which gives a ~0.16
    peak at the brightest setting. Every value on the slider then stays
    clean at the default volume. Raising volume past the default is
    still caught by the limiter, as intended.
Status:
    fixed - `Clap.level` maximum lowered to 0.3 in
    src/pyoscillate/patches/drums/clap/clap.py.

Corrected along the way
-----------------------
An early render reported the *default* clap as clipped. That was an
artefact of rendering at `Patch.volume` 1.0 instead of the default
`Clap.volume` (0.28). `render()` now defaults to the patch's volume default, so
tests hear what the listener hears.

At that quieter volume the measurement layer had its own bug. The start-up
hit peaked near -50 dB, which put its "-40 dB below peak" end-of-tail floor
below the envelope's -90 dB silence clamp. The tail never ended, and it
swallowed every later hit (a 1.985 s "decay" for a 0.08 s Tail). Fixed in
`pyoscillate.analysis.features`: reaching silence now also ends a tail.
"""

import unittest
from functools import cache

from pyoscillate.analysis.features import Features, Hit, features
from pyoscillate.analysis.render import render
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.drums.clap import clap

MODULE = "pyoscillate.patches.drums.clap.clap"
BPM = 120
# PATTERN {4, 12} on 16ths at 120 BPM: beats two and four of the first bar
BACKBEATS = (0.5, 1.5)
ONSET_TOLERANCE = 0.02
SECONDS = 2.0


@cache
def _measure(**params: float) -> Features:
    return features(
        render(MODULE, params, seconds=SECONDS, bpm=BPM),
        ceiling=PATCH_OUTPUT_CEILING,
    )


def _backbeat(result: Features) -> Hit:
    """The first scheduled clap, ignoring anything off the pattern."""
    return min(result.hits, key=lambda hit: abs(hit.onset - BACKBEATS[0]))


def _envelope_length(spread: float, decay: float) -> float:
    return clap.Clap.bursts * spread + decay


class ClapHealthTests(unittest.TestCase):
    def test_hits_land_on_beats_two_and_four(self) -> None:
        onsets = [hit.onset for hit in _measure().hits]

        for beat in BACKBEATS:
            self.assertTrue(
                any(abs(onset - beat) < ONSET_TOLERANCE for onset in onsets),
                f"no clap near {beat}s; onsets were {onsets}",
            )

    def test_silent_before_the_first_scheduled_hit(self) -> None:
        early = [
            hit for hit in _measure().hits if hit.onset < BACKBEATS[0] - ONSET_TOLERANCE
        ]

        self.assertEqual(early, [])

    def test_presence_range_is_clean_at_default_volume(self) -> None:
        loudest = _measure(
            level=clap.Clap.level.spec.maximum,
            tone=clap.Clap.tone.spec.maximum,
        )

        self.assertEqual(loudest.clip_fraction, 0.0)

    def test_tail_dies_away_before_the_next_hit(self) -> None:
        first = _backbeat(_measure())

        self.assertLess(first.onset + first.decay_time, BACKBEATS[1])


class ClapControlTests(unittest.TestCase):
    def test_tail_lengthens_the_decay(self) -> None:
        short = _backbeat(_measure(decay=0.08))
        long = _backbeat(_measure(decay=0.3))

        self.assertGreater(long.decay_time, short.decay_time)

    def test_tail_length_tracks_the_envelope_it_asks_for(self) -> None:
        for decay in (0.08, 0.3):
            with self.subTest(decay=decay):
                measured = _backbeat(_measure(decay=decay)).decay_time
                expected = _envelope_length(clap.Clap.spread.default, decay)

                self.assertGreater(measured, expected * 0.7)
                self.assertLess(measured, expected * 1.3)

    def test_brightness_raises_the_spectral_centroid(self) -> None:
        dull = _backbeat(_measure(tone=600))
        bright = _backbeat(_measure(tone=3000))

        self.assertGreater(bright.centroid, dull.centroid * 1.5)

    def test_brightness_keeps_loudness_steady(self) -> None:
        dull = _backbeat(_measure(tone=600))
        bright = _backbeat(_measure(tone=3000))

        self.assertLess(abs(bright.rms_db - dull.rms_db), 1.5)

    def test_presence_raises_the_level(self) -> None:
        quiet = _backbeat(_measure(level=0.1))
        loud = _backbeat(_measure(level=0.2))

        # doubling the level should read as roughly +6 dB
        self.assertGreater(loud.rms_db - quiet.rms_db, 4.0)
        self.assertLess(loud.rms_db - quiet.rms_db, 8.0)


if __name__ == "__main__":
    unittest.main()
