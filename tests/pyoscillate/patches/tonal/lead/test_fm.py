"""Perceptual contract for the FM leads: Bite brightens each note's attack,
Breath adds airy top-end to the tone, Length sets how long notes last, the
phrases stay inside the F Phrygian scale, the voice is silent until the clock
ticks, and the loudest corner stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The first note sits under `Patch.start()`'s fade-in, so
tests that compare notes measure later ones.

Findings
========

1. Breath noise ran before the clock ticked
-------------------------------------------
Error:
    test_silent_until_the_clock_ticks failed: with `clock_running=False` the
    render peaked at 0.089 (wind) and 0.060 (swirl) instead of 0. Setting
    Breath to 0 made it silent again.
Cause:
    The breath layer was the gated product `air_band * amp`, and the Breath
    control wrote `.mul` on that product. A pyo arithmetic result keeps its
    right-hand operand in `.mul`, so the write replaced the note envelope
    `amp` with a constant and the noise ran continuously.
Change:
    Breath is now a plain `Param` followed by `self.live(...)`, a `SigTo`
    multiplied in as a separate node (`air_level`), so nothing writes `.mul`
    on a node that carries an envelope. Checked by rendering with the clock
    stopped: peak 0.0 at default, at Breath 0 and at Breath 1.
Status:
    fixed - src/pyoscillate/patches/tonal/lead/fm.py.

2. The loudest corner clipped at the default volume
---------------------------------------------------
Error:
    test_loudest_corner_is_clean_at_default_volume: clip fraction 0.136
    (wind) and 0.183 (swirl) at Bite, Swirl, Breath, Echo and Length maxed.
Cause:
    Measured at volume 0.1 the raw peaks were 0.033 for the FM voice alone,
    0.073 for the breath layer alone and 0.095 with everything maxed. At the
    0.5 default that is 0.47, far over the 0.18 ceiling. Band-passed noise has
    a crest factor near 4 against 1.4 for a sine, so a breath layer with the
    same RMS as the tone has about three times its peak. The echo adds its
    feedback tail on top.
Change:
    Echo range capped at 0.7 and `volume` default 0.5 -> 0.2. `air_gain` was
    first lowered to 0.8 to fit under the ceiling, but Breath at its maximum
    then added 0.6 dB to the note (see the correction below), so it went back
    to 2.0 and the headroom came from `volume` instead. Checked by rerunning
    the loudest-corner test for both styles.
Status:
    fixed - src/pyoscillate/patches/tonal/lead/fm.py.

Corrected along the way
-----------------------
Breath was first tested as a rise in spectral centroid. With a steady FM
index under the tone the noise band at twice the pitch did not raise the
centroid (1018 Hz against 1037 Hz), so the test now checks the thing the help
text promises: noise mixed in under the note raises its level. That check then
showed the `air_gain` 0.8 fix above made Breath nearly inaudible.
"""

import unittest
from functools import cache
from typing import ClassVar

import numpy as np

from pyoscillate.analysis.features import features, spectral_centroid, to_db
from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.lead import fm

MODULE = "pyoscillate.patches.tonal.lead.fm"
STYLES = ("wind", "swirl")
BPM = 160
SIXTEENTH = 60 / BPM / 4
# the clock fires one audio buffer after the tick
LATENCY = 0.006
# semitones above the root in F Phrygian (root, b2, b3, 4, 5, b6, b7) and the octave
PHRYGIAN = {0, 1, 3, 5, 7, 8, 10, 12}


@cache
def _render(**params: float | str) -> Render:
    return render(MODULE, params, seconds=2.0, bpm=BPM)


def _note(
    result: Render, step: int, start: float = 0.0, end: float = 0.1
) -> np.ndarray:
    """Samples `start`..`end` seconds into the note at `step`."""
    onset = step * SIXTEENTH + LATENCY
    rate = result.sample_rate
    return result.samples[round((onset + start) * rate) : round((onset + end) * rate)]


def _centroid(samples: np.ndarray) -> float:
    return spectral_centroid(samples, 44100)


def _rms_db(samples: np.ndarray) -> float:
    return to_db(float(np.sqrt(np.mean(samples**2))))


class FmLeadDataTests(unittest.TestCase):
    def test_phrases_stay_in_the_scale_and_inside_the_cycle(self) -> None:
        for lead in (fm.LeadFmWind, fm.LeadFmSwirl):
            for phrase in lead.phrases:
                with self.subTest(lead=lead.__name__):
                    self.assertTrue(set(phrase.values()) <= PHRYGIAN)
                    self.assertTrue(all(0 <= step < lead.cycle for step in phrase))

    def test_every_style_has_a_phrase_to_evolve_to(self) -> None:
        for lead in (fm.LeadFmWind, fm.LeadFmSwirl):
            with self.subTest(lead=lead.__name__):
                self.assertGreaterEqual(len(lead.phrases), 2)


class FmLeadHealthTests(unittest.TestCase):
    def test_silent_until_the_clock_ticks(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                idle = render(
                    MODULE, {"style": style}, seconds=0.5, clock_running=False
                )

                self.assertLess(float(np.abs(idle.samples).max()), 1e-4)

    def test_loudest_corner_is_clean_at_default_volume(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                loudest = features(
                    _render(
                        style=style,
                        bite=fm.LeadFm.bite.spec.maximum,
                        swirl=fm.LeadFm.swirl.spec.maximum,
                        breath=fm.LeadFm.breath.spec.maximum,
                        echo_level=fm.LeadFm.echo_level.spec.maximum,
                        length=fm.LeadFm.length.spec.maximum,
                    ),
                    ceiling=PATCH_OUTPUT_CEILING,
                )

                self.assertEqual(loudest.clip_fraction, 0.0)


class FmLeadControlTests(unittest.TestCase):
    # `swirl` and `echo` off, so only the control under test moves the tone
    QUIET: ClassVar[dict[str, float]] = {"swirl": 0, "echo_level": 0, "glide": 0}

    def test_bite_brightens_the_attack(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                soft = _note(
                    _render(style=style, bite=0, breath=0, **self.QUIET), 0, 0.03, 0.08
                )
                snarl = _note(
                    _render(style=style, bite=8, breath=0, **self.QUIET), 0, 0.03, 0.08
                )

                self.assertGreater(_centroid(snarl), _centroid(soft) * 1.3)

    def test_breath_mixes_noise_in_under_the_note(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                clean = _note(
                    _render(style=style, bite=0, breath=0, **self.QUIET), 0, 0.03, 0.08
                )
                airy = _note(
                    _render(style=style, bite=0, breath=1, **self.QUIET), 0, 0.03, 0.08
                )

                self.assertGreater(_rms_db(airy) - _rms_db(clean), 2)

    def test_length_sets_how_long_notes_last(self) -> None:
        # the amplitude table ends at 0 after `length` 16ths; measure a
        # stretch just before the next note so a short note has died away
        tight = _note(
            _render(style="wind", length=0.3, bite=0, breath=0, **self.QUIET),
            0,
            0.06,
            0.09,
        )
        full = _note(
            _render(style="wind", length=1.0, bite=0, breath=0, **self.QUIET),
            0,
            0.06,
            0.09,
        )

        self.assertGreater(_rms_db(full) - _rms_db(tight), 10)


if __name__ == "__main__":
    unittest.main()
