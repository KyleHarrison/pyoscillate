"""Perceptual contract for the funk bass: Quack and Brightness brighten the
line, a short Swell brightens the ghost notes that a slow one leaves dark,
Length holds notes longer, the loudest corner stays clean, and no corner of
the sliders sends the ladder filter to NaN.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. Measurements come from the second bar, clear of
`Patch.start()`'s fade-in.

Findings
========

1. A wide, fast sweep blew the ladder filter up to NaN
------------------------------------------------------
Error:
    With Quack 8 (or Brightness 400) the render was silent after the first
    few milliseconds. Tracing the graph on a manual server, `MoogLP` output
    NaN at buffer 24, with its cutoff at 8.5 kHz and an input of -3.7. The
    patch limiter then turns the NaN into silence for good.
Cause:
    pyo's `MoogLP` is unstable when a fast sweep drives it with a hot input.
    Offline, with the cutoff swept to 12 kHz at Growl 0.95, it stayed
    finite with an input peak around 1 and failed at 2. The saw plus the
    pulse peak near 3.7. A fixed cutoff stays finite up to 15 kHz, so the
    cutoff alone was not the cause.
Change:
    The mix is scaled by `FILTER_TRIM` (0.25) before the filter, and the
    cutoff is clipped at `CUTOFF_CEILING` (8 kHz) for margin. GAIN went
    from 0.25 to 0.4 to restore the level after the trim (and after
    finding 2, whose releases end notes earlier).
Status:
    fixed - src/pyoscillate/patches/tonal/bass/funk/funk.py. Guarded by
    test_no_corner_goes_silent.

2. Length barely changed how long notes lasted
----------------------------------------------
Error:
    test_length_holds_notes_longer failed: 0.2-0.24 s into the One, Length
    1.5 measured 0.025 RMS against 0.033 at Length 0.3, so the shorter
    note was the louder one. test_short_swell_brightens_the_ghost_notes
    failed too: Swell 0.4 measured a brighter ghost (192 Hz) than Swell
    0.005 (142 Hz).
Cause:
    Each note set the `Adsr`s' `dur` to gate + release. pyo's `Adsr`
    doesn't release before its decay has finished: with a gate shorter than
    attack + decay it runs the full 0.29 s decay, drops straight to a
    lower level (0.36 to 0.13 in one buffer, which clicks), and releases in
    whatever time is left. Gates are mostly shorter than the decay, so
    Length and Swell set envelope shapes the notes never followed.
Change:
    The envelopes run with `dur=0` and are released by `stop()`, which
    ramps down from the current level at any stage (checked offline). A
    `TrigEnv` gate is restarted by every note and calls the release from its
    end trigger. A new note restarts the gate, so a long note's release
    can't cut off the next one (checked offline: retriggering after 50 ms
    moved the end trigger from 0.1 to 0.15 s).
Status:
    fixed - src/pyoscillate/patches/tonal/bass/funk/funk.py.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features, spectral_centroid
from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.bass.funk import funk

MODULE = "pyoscillate.patches.tonal.bass.funk.funk"
BPM = 120
SIXTEENTH = 60 / BPM / 4
# the clock fires one audio buffer after the tick
LATENCY = 0.006
# the held root on the One and a ghost note, both in the second bar
ONE, GHOST = 16, 19


def _step(index: int) -> funk.Step:
    return funk.LINE[index % len(funk.LINE)]


@cache
def _render(**params: float) -> Render:
    return render(MODULE, params, seconds=2.4, bpm=BPM)


def _note(
    result: Render, step: int, start: float = 0.0, end: float = 0.1
) -> np.ndarray:
    """Samples `start`..`end` seconds into the note at `step`."""
    onset = step * SIXTEENTH + LATENCY
    rate = result.sample_rate
    return result.samples[round((onset + start) * rate) : round((onset + end) * rate)]


def _centroid(samples: np.ndarray) -> float:
    return spectral_centroid(samples, 44100)


def _rms(samples: np.ndarray) -> float:
    return float(np.sqrt(np.mean(samples**2)))


class FunkBassLineTests(unittest.TestCase):
    def test_measured_steps_are_what_the_tests_assume(self) -> None:
        self.assertEqual(_step(ONE).semitones, 0)
        self.assertEqual(_step(GHOST).semitones, 0)
        self.assertGreater(_step(ONE).accent, _step(GHOST).accent)

    def test_every_pitch_is_a_minor_seventh_chord_tone(self) -> None:
        tones = {0, 3, 7, 10}
        for step in funk.LINE:
            if step.hit:
                self.assertIn(step.semitones % 12, tones)


class FunkBassHealthTests(unittest.TestCase):
    def test_no_corner_goes_silent(self) -> None:
        # the widest sweeps, where a NaN from the filter would mute the patch
        for params in (
            {"quack": funk.FunkBass.quack.spec.maximum},
            {
                "cutoff": funk.FunkBass.cutoff.spec.maximum,
                "quack": funk.FunkBass.quack.spec.maximum,
            },
            {
                "cutoff": funk.FunkBass.cutoff.spec.maximum,
                "quack": funk.FunkBass.quack.spec.maximum,
                "resonance": funk.FunkBass.resonance.spec.maximum,
                "swell": funk.FunkBass.swell.spec.minimum,
                "octave": funk.FunkBass.octave.spec.maximum,
            },
        ):
            with self.subTest(**params):
                samples = _note(_render(**params), ONE)

                self.assertTrue(np.isfinite(samples).all())
                self.assertGreater(_rms(samples), 1e-3)

    def test_loudest_corner_is_clean_at_default_volume(self) -> None:
        for resonance in (
            funk.FunkBass.resonance.spec.minimum,
            funk.FunkBass.resonance.spec.maximum,
        ):
            with self.subTest(resonance=resonance):
                loudest = features(
                    _render(
                        cutoff=funk.FunkBass.cutoff.spec.maximum,
                        quack=funk.FunkBass.quack.spec.maximum,
                        resonance=resonance,
                        length=funk.FunkBass.length.spec.maximum,
                        octave=funk.FunkBass.octave.spec.maximum,
                    ),
                    ceiling=PATCH_OUTPUT_CEILING,
                )

                self.assertEqual(loudest.clip_fraction, 0.0)


class FunkBassControlTests(unittest.TestCase):
    def test_quack_opens_the_filter(self) -> None:
        # around the top of the default 150 ms swell
        muted = _note(_render(quack=0), ONE, 0.1, 0.18)
        wide = _note(_render(quack=8), ONE, 0.1, 0.18)

        self.assertGreater(_centroid(wide), _centroid(muted) * 2)

    def test_brightness_brightens_the_ghost_notes(self) -> None:
        # a ghost ends before the swell opens the filter, so only the
        # resting cutoff decides its tone
        dark = _note(_render(cutoff=20), GHOST, end=0.05)
        bright = _note(_render(cutoff=400), GHOST, end=0.05)

        self.assertGreater(_centroid(bright), _centroid(dark) * 1.5)

    def test_short_swell_brightens_the_ghost_notes(self) -> None:
        lazy = _note(_render(swell=0.4), GHOST, end=0.05)
        snappy = _note(_render(swell=0.005), GHOST, end=0.05)

        self.assertGreater(_centroid(snappy), _centroid(lazy) * 1.3)

    def test_accented_notes_quack_harder_than_ghosts(self) -> None:
        one = _note(_render(), ONE, 0.02, 0.05)
        ghost = _note(_render(), GHOST, 0.02, 0.05)

        self.assertGreater(_rms(one), _rms(ghost))
        self.assertGreater(_centroid(one), _centroid(ghost))

    def test_length_holds_notes_longer(self) -> None:
        # the One is held 1.8 16ths; past its gate at Length 0.3 only the
        # release is left, at Length 1.5 it is still sustaining
        short = _note(_render(length=0.3), ONE, 0.2, 0.24)
        long = _note(_render(length=1.5), ONE, 0.2, 0.24)

        self.assertGreater(_rms(long), _rms(short) * 1.5)


if __name__ == "__main__":
    unittest.main()
