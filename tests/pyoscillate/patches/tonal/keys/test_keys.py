"""Perceptual contract for the keys: chords land on the Charleston rhythm,
Bark pings mostly on hard notes, Bite brightens the sustained tone, Decay
sets how long a chord rings, Tremolo throbs the level, and the loudest
corner stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The first chord sits under `Patch.start()`'s fade-in, so
tests measure later ones.

Findings
========

1. The body carries a DC offset
-------------------------------
Error:
    At Bite 3, the hard chord's first 400 ms averaged 0.0098, over five
    times the 5%-of-RMS bound. A rough probe put it at 65% of RMS at
    Register 110 with Bark and Bite at maximum. Bite also measured no
    brighter: the sustained centroid was 269 Hz at Bite 3 against 247 Hz at
    Bite 0, short of the promised lift.
Cause:
    The same defect as the FM bass (tests/.../bass/fm/test_fm.py, finding 1).
    The body pair is ratio 1, so its first lower sideband lands on 0 Hz,
    and pyo's `FM` integrates frequency, so the term does not cancel. The
    offset follows the body's index envelope and pulls the centroid down.
Change:
    A 2nd-order `ButHP` at 20 Hz (`SUBSONIC`) on the mixed chord, below the
    lowest note (87 Hz). Both tests pass.
Status:
    fixed - src/pyoscillate/patches/tonal/keys/keys.py.

2. A hard strike left the chord quieter
---------------------------------------
Error:
    test_bark_is_gone_once_the_chord_rings failed: 300-500 ms after the hard
    chord, Bark 6 moved the centroid 16% from Bark 0, and the level was 6.5
    dB lower (7.4 dB at Bite 0.8). Bark promises a ping that fades as the
    chord rings, so after the ping the chord should sound the same.
Cause:
    The tine pair shared the body's amplitude envelope, so its carrier kept
    ringing on the same pitch as the body's. `FM` integrates the modulated
    frequency, so the tine's index burst leaves its carrier phase-shifted
    against the body's by an amount that depends on Bark. The two
    fundamentals then partly cancel. At Bite 0, where both are pure sines,
    the centroid barely moved (247 against 236 Hz) but the level still fell,
    which pinned it on the phase, not the spectrum.
Change:
    The tine pair gets its own short amplitude envelope (`TINE_RING`, 0.3 s)
    at half the body's level (`TINE_LEVEL`), as a DX7 E.PIANO's tine stack
    fades before its body. Once the tine is gone, only the body rings, and
    the tine's phase no longer matters. At full tine level the strike rose
    about 6 dB above the ring, so a chord's -40 dB point came early (0.54 s
    for Decay 0.8); half level keeps it within the Decay band. The strike's
    share of the level falls, so the `volume` default went from 0.6 to 0.8 (the
    loudest corner peaks at ~0.16).
Status:
    fixed - src/pyoscillate/patches/tonal/keys/keys.py.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import (
    Features,
    Hit,
    envelope,
    features,
    spectral_centroid,
)
from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.keys import keys
from pyoscillate.theory.intervals import Progression

MODULE = "pyoscillate.patches.tonal.keys.keys"
BPM = 120
SIXTEENTH = 60 / BPM / 4
BAR = SIXTEENTH * keys.BAR_STEPS
# the clock fires one audio buffer after the tick
LATENCY = 0.006
ONSET_TOLERANCE = 0.02
# bar two: the hard chord on beat one, the soft push on the "and" of two
HARD = BAR
SOFT = BAR + 6 * SIXTEENTH


@cache
def _render(seconds: float = 3.2, **params: float) -> Render:
    # the boom-bap rack's chords: Keys follows the rack's harmony, and a ring
    # time measured on one chord is not the same on another
    return render(
        MODULE,
        params,
        seconds=seconds,
        bpm=BPM,
        key=0,
        progression=Progression.JAZZ_TURNAROUND.roots,
    )


def _span(result: Render, onset: float, start: float, end: float) -> np.ndarray:
    rate = result.sample_rate
    first = onset + LATENCY
    return result.samples[round((first + start) * rate) : round((first + end) * rate)]


def _centroid(samples: np.ndarray) -> float:
    return spectral_centroid(samples, 44100)


def _hit(result: Features, onset: float) -> Hit:
    for hit in result.hits:
        if abs(hit.onset - onset) < ONSET_TOLERANCE:
            return hit
    raise AssertionError(
        f"no hit near {onset:.3f} s in {[h.onset for h in result.hits]}"
    )


class KeysHealthTests(unittest.TestCase):
    def test_chords_land_on_the_charleston_rhythm(self) -> None:
        result = features(_render(decay=0.5))
        for onset in (SOFT - BAR, HARD, SOFT):
            _hit(result, onset)

    def test_chords_carry_no_dc_offset(self) -> None:
        for bite in (0, keys.Keys.bite.spec.maximum):
            with self.subTest(bite=bite):
                samples = _span(_render(bite=bite, tremolo=0), HARD, 0, 0.4)
                rms = float(np.sqrt(np.mean(samples**2)))

                self.assertLess(abs(float(samples.mean())), rms * 0.05)

    def test_loudest_corner_is_clean_at_default_volume(self) -> None:
        for root_freq in (
            keys.Keys.root_freq.spec.minimum,
            keys.Keys.root_freq.spec.maximum,
        ):
            with self.subTest(root_freq=root_freq):
                loudest = features(
                    _render(
                        root_freq=root_freq,
                        bark=keys.Keys.bark.spec.maximum,
                        bite=keys.Keys.bite.spec.maximum,
                        decay=keys.Keys.decay.spec.maximum,
                        tremolo=0,
                    ),
                    ceiling=PATCH_OUTPUT_CEILING,
                )

                self.assertEqual(loudest.clip_fraction, 0.0)


class KeysControlTests(unittest.TestCase):
    def test_bark_pings_mostly_on_hard_notes(self) -> None:
        round_ = _render(bark=0, tremolo=0)
        barking = _render(bark=keys.Keys.bark.spec.maximum, tremolo=0)

        def lift(onset: float) -> float:
            """How much Bark brightens the strike at `onset`."""
            return _centroid(_span(barking, onset, 0, 0.04)) / _centroid(
                _span(round_, onset, 0, 0.04)
            )

        self.assertGreater(lift(HARD), 1.5)
        self.assertGreater(lift(HARD), lift(SOFT) * 1.2)

    def test_bark_is_gone_once_the_chord_rings(self) -> None:
        # the tine dies in TINE_TIME; well after it, Bark changes nothing
        round_ = _span(_render(bark=0, tremolo=0), HARD, 0.3, 0.5)
        barking = _span(
            _render(bark=keys.Keys.bark.spec.maximum, tremolo=0), HARD, 0.3, 0.5
        )

        self.assertLess(abs(_centroid(barking) / _centroid(round_) - 1), 0.1)

    def test_bite_brightens_the_sustained_tone(self) -> None:
        mellow = _span(_render(bark=0, bite=0, tremolo=0), HARD, 0.1, 0.3)
        reedy = _span(
            _render(bark=0, bite=keys.Keys.bite.spec.maximum, tremolo=0), HARD, 0.1, 0.3
        )

        self.assertGreater(_centroid(reedy), _centroid(mellow) * 1.3)

    def test_decay_sets_how_long_a_chord_rings(self) -> None:
        # at Rate -2 the grid is quarter notes: chords at 0 and 3 s, then 8 s
        onset = 6 * 4 * SIXTEENTH
        for decay in (0.8, 2.0):
            with self.subTest(decay=decay):
                hit = _hit(
                    features(_render(seconds=5.5, decay=decay, rate=-2, tremolo=0)),
                    onset,
                )

                # the amplitude table is RING_CURVE e-folds (-40 dB) at `decay`
                self.assertGreater(hit.decay_time, decay * 0.7)
                self.assertLess(hit.decay_time, decay * 1.3)

    def test_tremolo_throbs_the_level(self) -> None:
        def depth(result: Render) -> float:
            """Spread in dB of 10 ms levels over the ring, around the decay's trend."""
            window = Render(_span(result, HARD, 0.1, 0.6), result.sample_rate)
            levels = envelope(window, 0.01)
            trend = np.polyval(
                np.polyfit(np.arange(levels.size), levels, 1), np.arange(levels.size)
            )
            return float(np.std(levels - trend))

        steady = depth(_render(tremolo=0, decay=4))
        throbbing = depth(_render(tremolo=1, decay=4))

        self.assertGreater(throbbing - steady, 3)


if __name__ == "__main__":
    unittest.main()
