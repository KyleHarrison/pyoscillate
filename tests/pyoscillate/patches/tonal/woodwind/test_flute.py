"""Perceptual contract for the flute (`woodwind/flute/flute.py`) and the controls every
wind shares (`woodwind/wind.py`): the flute sits on the rack's note, Overtones
fills out the tone without changing its loudness, Brightness opens the pipe,
Opening makes a note start dull and brighten, Pitch tracking brightens high
notes, Breath adds hiss that Air focus gathers around the pitch, Tongue puts a
consonant on a note struck afresh and none on a slur, Tremolo and Flutter pulse
the level at their own speeds, Bend scoops into the pitch, and the loudest
corner stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The phrase is the flute's default (`Leads.WIND_DRIFT`, sixteenth
notes): a first note at 0 (inside the patch's fade-in, so never measured), and a
second, F above the register's A, from 0.625 s. A note is measured once its
attack is over.

Findings
========

1. Breath was inaudible
-----------------------
Error:
    At full Breath the breath alone measured 0.0010 rms against a tone of 0.034:
    30 dB under it, so the help text's "a lot is a windy, effortful blow" was
    unreachable.
Cause:
    The resonated breath's trim (`air_trim`, 0.1) was carried over from the
    whistle, whose resonator is far sharper; a wider pipe rings less of the noise
    and needs a much larger trim.
Change:
    `air_trim` is 1.8, which puts the breath at full Breath about 6 dB under the
    tone (0.0166 rms), measured with a flute whose tone is off.
Status:
    fixed - src/pyoscillate/patches/tonal/woodwind/wind.py.

2. Air focus doubled as a level control
---------------------------------------
Error:
    With the trim held fixed, Air focus 3 to 80 moved the breath from 0.00076 to
    0.00101 rms (+2.5 dB) with the first make-up exponent (0.5), so a sharper pipe
    was also a louder one.
Cause:
    A band-pass resonator passes a share of white noise in proportion to its
    bandwidth, so the breath loses level as the resonance sharpens; a make-up of
    Air focus to the power 0.5 overshoots what pyo's `Reson` loses.
Change:
    The make-up exponent (`air_makeup`) is 0.4, which holds the breath alone
    within 0.5 dB across the range on the first note (0.0166 to 0.0158 rms) and
    the flute as a whole within 0.3 dB on a long F5 (0.0392 to 0.0379 rms). The
    breath alone still sags 2.5 dB on that F5 (0.0182 to 0.0136): a narrow band
    of noise is a few independent samples in a short window, so only a long one
    reads steadily, and the test measures the whole flute over half a second.
Status:
    fixed - src/pyoscillate/patches/tonal/woodwind/wind.py.

3. Tongue was barely audible
----------------------------
Error:
    At full Tongue the burst on a fresh note peaked at 0.0126 rms against a
    steady tone of 0.034: 13 dB under it, a consonant only if you knew to listen.
Cause:
    The burst's level (`tongue_boost`, 1.5 times the tone) is the share of a
    noise band 1100 Hz wide, which carries only a fraction of the noise's power.
Change:
    `tongue_boost` is 6, so a full burst peaks at about the level of the steady
    tone (0.037 against 0.034) for about 30 ms.
Status:
    fixed - src/pyoscillate/patches/tonal/woodwind/wind.py.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum, Wobble
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.woodwind.flute.flute import Flute
from pyoscillate.patches.tonal.woodwind.flute.flute_phrases import (
    FlutePhrases,
    FluteTunes,
)
from pyoscillate.theory.phrase import Leads
from pyoscillate.theory.pitch import Note

RATE = 44100
BPM = 120
MODULE = "pyoscillate.patches.tonal.woodwind.flute.flute"
# the second note of the default phrase: the minor sixth above the A4 register
NOTE = Note.transpose(Note.A4, 8)
SECOND_ON = 0.625
# after the attack and before the note lifts (its hold ends near 0.95 s)
SETTLED = (0.78, 0.93)
# the first 30 ms of the second note
ONSET = (0.628, 0.658)
# with the rate halved the notes are twice as long: a second from 1.25 s to
# 2.0 s, long enough for a few cycles of a slow pulse
SLOW = {"rate": -1, "legato": 1.0, "attack": 0.01, "release": 0.03}
SLOW_SETTLED = (1.45, 1.95)
PURE = {
    "breath": 0,
    "vibrato": 0,
    "unsteadiness": 0,
    "tremolo": 0,
    "tongue": 0,
    "bend": 0,
    "flutter": 0,
    "opening": 0,
    "tracking": 0,
    "reverb_bal": 0,
    "brightness": 12000,
    "release": 0.03,
}


@cache
def _render(seconds: float = 1.2, **params: float) -> Render:
    return render(MODULE, {**PURE, **params}, seconds=seconds, bpm=BPM)


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _rms(samples: np.ndarray) -> float:
    return float(np.sqrt((samples**2).mean()))


def _settled(**params: float) -> Spectrum:
    return Spectrum.of(_window(_render(**params), SETTLED), RATE)


class HealthTests(unittest.TestCase):
    def test_render_is_silent_until_the_shared_clock_ticks(self) -> None:
        result = features(render(MODULE, {}, seconds=0.5, clock_running=False))

        self.assertLess(result.peak, 1e-4)

    def test_render_sounds_after_the_shared_clock_starts(self) -> None:
        self.assertGreater(features(render(MODULE, {}, seconds=0.8)).peak, 1e-3)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        loudest = {
            "brightness": Flute.brightness.spec.maximum,
            "breath": Flute.breath.spec.maximum,
            "tongue": Flute.tongue.spec.maximum,
            "overtones": Flute.overtones.spec.maximum,
            "tremolo": Flute.tremolo.spec.maximum,
            "air_focus": Flute.air_focus.spec.maximum,
            "opening": 0,
            "tracking": Flute.tracking.spec.maximum,
            "reverb_bal": Flute.reverb_bal.spec.maximum,
        }
        for name, params in (("default", {}), ("loudest corner", loudest)):
            with self.subTest(settings=name):
                result = render(MODULE, params, seconds=2.4, bpm=BPM)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)


class PitchTests(unittest.TestCase):
    def test_the_flute_sits_on_the_note(self) -> None:
        self.assertAlmostEqual(_settled().peak_frequency(400, 1000), NOTE, delta=3)

    def test_bend_scoops_into_the_note_from_below(self) -> None:
        def onset_pitch(bend: float) -> float:
            samples = _window(_render(attack=0.005, bend=bend), ONSET)
            return Spectrum.of(samples, RATE).peak_frequency(400, 1000)

        # a note that starts 3 semitones flat is below its pitch while it climbs
        self.assertLess(onset_pitch(-3), 0.96 * onset_pitch(0))
        self.assertAlmostEqual(onset_pitch(0), NOTE, delta=12)


class ToneTests(unittest.TestCase):
    def test_overtones_fill_out_the_tone(self) -> None:
        def second_partial(overtones: float) -> float:
            levels = _settled(overtones=overtones).partial_levels(NOTE, 2)
            return float(levels[1] - levels[0])

        self.assertGreater(second_partial(1), second_partial(0) + 20)

    def test_overtones_do_not_change_the_loudness(self) -> None:
        def level(overtones: float) -> float:
            return _rms(_window(_render(overtones=overtones), SETTLED))

        quiet, loud = sorted((level(0), level(1)))
        self.assertLess(20 * np.log10(loud / quiet), 1.5)

    def test_brightness_opens_the_pipe(self) -> None:
        def centroid(brightness: float) -> float:
            return _settled(overtones=1, brightness=brightness).centroid()

        self.assertGreater(centroid(12000), 1.5 * centroid(800))

    def test_opening_starts_a_note_dull_and_brightens_it(self) -> None:
        def early_centroid(opening: float) -> float:
            samples = _window(
                _render(overtones=1, brightness=4000, attack=0.3, opening=opening),
                (0.65, 0.72),
            )
            return Spectrum.of(samples, RATE).centroid()

        self.assertLess(early_centroid(0.9), 0.8 * early_centroid(0))

    def test_pitch_tracking_brightens_high_notes(self) -> None:
        def top(tracking: float) -> float:
            levels = _settled(
                overtones=1, brightness=1200, tracking=tracking
            ).partial_levels(NOTE, 4)
            return float(levels[3] - levels[0])

        # the note sits above the pitch tracking is centred on, so the pipe
        # opens further than Brightness put it
        self.assertGreater(top(1), top(0) + 3)


class BreathTests(unittest.TestCase):
    def test_breath_adds_hiss_around_the_note(self) -> None:
        def hiss(breath: float) -> float:
            spectrum = _settled(breath=breath)
            return spectrum.band(NOTE * 0.9, NOTE * 1.1) - spectrum.band(
                NOTE - 40, NOTE + 40
            )

        self.assertGreater(hiss(1), 3 * hiss(0))

    def test_air_focus_gathers_the_breath_around_the_pitch(self) -> None:
        def straying(focus: float) -> float:
            # the hiss away from the note (below it, and between it and its
            # octave) against the power at the note itself, tone and ring
            spectrum = _settled(breath=1, air_focus=focus)
            away = spectrum.band(NOTE * 0.3, NOTE * 0.8) + spectrum.band(
                NOTE * 1.2, NOTE * 1.8
            )
            return away / spectrum.band(NOTE * 0.9, NOTE * 1.1)

        self.assertGreater(straying(3), 3 * straying(80))

    def test_air_focus_does_not_change_the_loudness(self) -> None:
        def level(focus: float) -> float:
            samples = _window(
                _render(2.1, **SLOW, breath=1, air_focus=focus), SLOW_SETTLED
            )
            return _rms(samples)

        quiet, loud = sorted((level(3), level(80)))
        self.assertLess(20 * np.log10(loud / quiet), 1.5)


class ArticulationTests(unittest.TestCase):
    def test_tongue_puts_a_consonant_on_a_note_struck_afresh(self) -> None:
        def onset(tongue: float) -> float:
            return _rms(_window(_render(attack=0.5, tongue=tongue), ONSET))

        self.assertGreater(onset(1), 2 * onset(0))

    def test_a_slurred_note_has_no_tongue(self) -> None:
        def onset(tongue: float) -> float:
            # full Legato holds the first note until the second, which slurs
            return _rms(_window(_render(attack=0.5, legato=1.0, tongue=tongue), ONSET))

        self.assertAlmostEqual(onset(1) / onset(0), 1.0, delta=0.1)

    def test_tongue_length_stretches_the_consonant(self) -> None:
        def tail(length: float) -> float:
            samples = _window(
                _render(attack=0.5, tongue=1, tongue_length=length), (0.67, 0.72)
            )
            return _rms(samples)

        self.assertGreater(tail(0.15), 2 * tail(0.005))


class PulseTests(unittest.TestCase):
    def test_tremolo_pulses_the_level_at_its_speed(self) -> None:
        def swing(tremolo: float) -> float:
            samples = _window(
                _render(
                    2.1, **SLOW, tremolo=tremolo, tremolo_speed=6, vibrato_bloom=0.01
                ),
                SLOW_SETTLED,
            )
            return Wobble.level(samples, RATE, 0.01)

        self.assertGreater(swing(0.5), 3 * swing(0))
        samples = _window(
            _render(2.1, **SLOW, tremolo=0.5, tremolo_speed=6, vibrato_bloom=0.01),
            SLOW_SETTLED,
        )
        self.assertAlmostEqual(
            Wobble.level_rate(samples, RATE, 0.01, 3, 12), 6, delta=1.5
        )

    def test_flutter_rolls_the_breath_at_its_speed(self) -> None:
        def swing(flutter: float) -> float:
            samples = _window(
                _render(2.1, **SLOW, flutter=flutter, flutter_speed=24), SLOW_SETTLED
            )
            return Wobble.level(samples, RATE, 0.005)

        self.assertGreater(swing(1), 3 * swing(0))
        samples = _window(
            _render(2.1, **SLOW, flutter=1, flutter_speed=24), SLOW_SETTLED
        )
        self.assertAlmostEqual(
            Wobble.level_rate(samples, RATE, 0.005, 15, 40), 24, delta=4
        )


class TuneTests(unittest.TestCase):
    def test_the_flute_offers_its_tunes_beside_the_shared_lines(self) -> None:
        offered = Flute.phrase.catalog.members()

        self.assertIs(Flute.phrase.catalog, FlutePhrases)
        for tune in FluteTunes.members():
            self.assertIn(tune, offered)
        self.assertIn(Leads.WIND_DRIFT, offered)

    def test_a_tune_fits_its_cycle_and_the_flutes_range(self) -> None:
        for tune in FluteTunes.members():
            with self.subTest(tune=tune.id):
                starts = [step.at for step in tune.steps]

                self.assertEqual(starts, sorted(set(starts)))
                self.assertLess(max(starts), tune.cycle)
                # a whole number of bars on the sixteenth grid
                self.assertEqual(tune.cycle % 16, 0)
                # within two octaves of the register's root
                self.assertTrue(all(-12 <= step.offset <= 24 for step in tune.steps))

    def test_a_tune_plays(self) -> None:
        for tune in FluteTunes.members():
            with self.subTest(tune=tune.id):
                result = render(
                    MODULE,
                    {"phrase": FlutePhrases.index_of(tune)},
                    seconds=1.6,
                    bpm=BPM,
                )

                self.assertGreater(features(result).peak, 1e-3)


if __name__ == "__main__":
    unittest.main()
