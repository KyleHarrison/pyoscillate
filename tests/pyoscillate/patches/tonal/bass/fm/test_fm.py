"""Perceptual contract for the FM bass: Growl brightens the bark without
making it louder, Settle keeps the bark later into the note, Edge brightens
the settled tone, accents bark harder, Length sets how long notes last, and
the loudest corner stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/CLAUDE.md. The first note sits under `Patch.start()`'s fade-in, so
tests measure later ones.

Findings
========

1. The bark carries a DC offset, which also hid the accent
----------------------------------------------------------
Error:
    test_accents_bark_harder failed: the accented note's first 40 ms had a
    lower centroid than the unaccented one (59 Hz against 65 Hz at Register
    55; 161 against 221 Hz at 110), although its index is 1.4 times higher.
    Over four whole periods at 110 Hz, the accented `bark` note at Growl 6
    averaged -0.024, a third of its RMS; the pure sine at Growl 0 averaged
    nothing. `grit` showed the same at Growl 12 (0.006).
Cause:
    At ratio 1 the first lower sideband lands on 0 Hz. pyo's `FM` integrates
    the modulated frequency, so the carrier's phase relative to the
    modulator depends on the note's history and the 0 Hz term does not
    cancel. The offset follows the index envelope, so each bark is a
    subsonic thump. It uses headroom and drags the centroid down, which is
    why the more-modulated accent measured darker. CrossFM's feedback puts
    energy at 0 Hz at high index in the same way.
Change:
    A 2nd-order `ButHP` at 20 Hz (`SUBSONIC`) after the oscillator, below the
    lowest Register, which loses under 1 dB to it. pyo's `DCBlock` was tried
    first. It halved the offset, but a one-pole filter is too slow for an
    offset that moves within milliseconds, and the test still failed. The
    high-pass's phase shift raises the crest at Register 30 by up to ~25%, so
    VOLUME_DEFAULT went from 0.5 to 0.42 to keep the loudest corner clean.
Status:
    fixed - src/pyoscillate/patches/tonal/bass/fm/fm.py.

Corrected along the way
-----------------------
The first DC measurement used a 30 ms window, 3.3 periods at 110 Hz, so a
plain sine also "failed". The test now averages over whole periods.
test_length_sets_how_long_notes_last first measured up to 120 ms into the
note, which caught the next note's onset; it now stops at 90 ms.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features, spectral_centroid, to_db
from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.bass.fm import fm

MODULE = "pyoscillate.patches.tonal.bass.fm.fm"
BPM = 120
SIXTEENTH = 60 / BPM / 4
# the clock fires one audio buffer after the tick
LATENCY = 0.006
SLIDERS = {spec.name: spec for spec in fm.PARAMETERS}


@cache
def _render(**params: float | str) -> Render:
    return render(MODULE, params, seconds=1.2, bpm=BPM)


def _note(result: Render, step: int, start: float = 0.0, end: float = 0.1) -> np.ndarray:
    """Samples `start`..`end` seconds into the note at `step`."""
    onset = step * SIXTEENTH + LATENCY
    rate = result.sample_rate
    return result.samples[round((onset + start) * rate) : round((onset + end) * rate)]


def _centroid(samples: np.ndarray) -> float:
    return spectral_centroid(samples, 44100)


def _rms_db(samples: np.ndarray) -> float:
    return to_db(float(np.sqrt(np.mean(samples**2))))


# steps 7 and 8 of the rolling profile are both the root, unaccented then accented
UNACCENTED, ACCENTED = 7, 8


class FMBassHealthTests(unittest.TestCase):
    def test_notes_carry_no_dc_offset(self) -> None:
        for style in fm.STYLES:
            for growl in (0, 6, 12):
                with self.subTest(style=style, growl=growl):
                    # a whole number of periods, so a plain sine averages to 0
                    samples = _note(
                        _render(style=style, root_freq=110, growl=growl, edge=0),
                        ACCENTED,
                        end=4 / 110,
                    )
                    rms = float(np.sqrt(np.mean(samples**2)))

                    self.assertLess(abs(float(samples.mean())), rms * 0.05)

    def test_loudest_corner_is_clean_at_default_volume(self) -> None:
        for style in fm.STYLES:
            for root_freq in (SLIDERS["root_freq"].minimum, SLIDERS["root_freq"].maximum):
                with self.subTest(style=style, root_freq=root_freq):
                    loudest = features(
                        _render(
                            style=style,
                            root_freq=root_freq,
                            growl=SLIDERS["growl"].maximum,
                            edge=SLIDERS["edge"].maximum,
                            length=SLIDERS["length"].maximum,
                        ),
                        ceiling=PATCH_OUTPUT_CEILING,
                    )

                    self.assertEqual(loudest.clip_fraction, 0.0)


class FMBassControlTests(unittest.TestCase):
    def test_growl_brightens_the_bark(self) -> None:
        for style in fm.STYLES:
            with self.subTest(style=style):
                soft = _note(_render(style=style, growl=0), ACCENTED, end=0.04)
                snarl = _note(_render(style=style, growl=12), ACCENTED, end=0.04)

                self.assertGreater(_centroid(snarl), _centroid(soft) * 1.5)

    def test_growl_does_not_change_loudness(self) -> None:
        # the CLAUDE.md claim: FM keeps its amplitude whatever the index
        soft = _note(_render(style="bark", growl=0), ACCENTED)
        snarl = _note(_render(style="bark", growl=12), ACCENTED)

        self.assertLess(abs(_rms_db(snarl) - _rms_db(soft)), 1.5)

    def test_settle_keeps_the_bark_later_into_the_note(self) -> None:
        for style in fm.STYLES:
            with self.subTest(style=style):
                quick = _note(_render(style=style, settle=0.02, edge=0), ACCENTED, 0.05, 0.1)
                slow = _note(_render(style=style, settle=0.4, edge=0), ACCENTED, 0.05, 0.1)

                self.assertGreater(_centroid(slow), _centroid(quick) * 1.3)

    def test_edge_brightens_the_settled_tone(self) -> None:
        for style in fm.STYLES:
            with self.subTest(style=style):
                pure = _note(_render(style=style, settle=0.02, edge=0), ACCENTED, 0.05, 0.1)
                edged = _note(_render(style=style, settle=0.02, edge=3), ACCENTED, 0.05, 0.1)

                self.assertGreater(_centroid(edged), _centroid(pure) * 1.3)

    def test_accents_bark_harder(self) -> None:
        result = _render(style="bark", edge=0)
        plain = _note(result, UNACCENTED, end=0.04)
        accented = _note(result, ACCENTED, end=0.04)

        self.assertGreater(_centroid(accented), _centroid(plain) * 1.1)
        self.assertGreater(_rms_db(accented) - _rms_db(plain), 1.5)

    def test_length_sets_how_long_notes_last(self) -> None:
        # the amplitude table ends at 0 after `length` 16ths; measure a
        # stretch that ends clear of the next note's onset
        tight = _note(_render(style="bark", length=0.3), ACCENTED, 0.04, 0.09)
        full = _note(_render(style="bark", length=1.0), ACCENTED, 0.04, 0.09)

        self.assertGreater(_rms_db(full) - _rms_db(tight), 20)


if __name__ == "__main__":
    unittest.main()
