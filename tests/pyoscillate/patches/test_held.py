"""Contracts every held voice shares (`Held`, `Ensemble` and
`ChordRoot.chord_frequencies`, `common.py`): which notes sound, how long they
are held, and how an ensemble is spread.

Findings
========

1. A note one step from the next could not be shortened or released
-------------------------------------------------------------------
Error:
    On a chord pulse (a hit every bar, or every beat) Legato had no effect
    and Release none: a parameter audit rendering every slider at its minimum
    and its maximum found the two renders sample-for-sample identical (largest
    difference 0.00000) for Choir and Angels' Legato, and for the solo voices'
    Release on a sparse hook. At Legato 0 a chord should be clipped short and
    silent for most of the bar; it held to the end of the bar.
Cause:
    The note was lifted from `next_step`, which only runs on a step boundary.
    A note held "for its step" was lifted on the next boundary after it was
    due, and when the next hit sits one step away that boundary is the next
    hit itself: the lift (`stop()`) and the next strike (`play()`) happened in
    the same callback, so the release never sounded and Legato below 1 meant 1.
Change:
    `Held` has a pulse of its own on every clock tick (`check_lift`) that
    lifts the note on the tick its hold runs out, and the hold is a fraction of
    the gap to the next note (`hold_ticks`: `staccato` of it at Legato 0, all of
    it at 1) instead of "the rest of the step plus Legato of the way". Below
    full Legato the lift lands before the next hit; at full Legato it lands
    after it, so the next note finds the old one still held and slurs into it.
    Checked by rendering both ends of Legato and Release (below) and by
    rerunning the audit.
Status:
    fixed - src/pyoscillate/patches/common.py.

2. A rate at the end of the slider crashed a phrase on another grid
--------------------------------------------------------------------
Error:
    Building a voice at its Rate slider's minimum raised `ValueError: rate must
    be between 0 and 7 for WHOLE` when the chosen phrase was a once-a-bar
    pulse.
Cause:
    The Rate slider is sized for the class's `base_division`, but a voice that
    offers phrases on several grids (a figure on eighths, a chord on bars)
    schedules each on its own, and `Phrased.schedule_pattern` passed the
    slider's value to the clock unchecked. The live `rate` control already held
    the offset inside the grid's range; the build did not.
Change:
    `Phrased.schedule_pattern` holds the rate inside the chosen grid's limits,
    as `reschedule` does.
Status:
    fixed - src/pyoscillate/patches/common.py.
"""

import unittest
from functools import cache
from types import SimpleNamespace

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.harmony import Harmony
from pyoscillate.patches.common import Held
from pyoscillate.patches.tonal.keys.organ import Organ
from pyoscillate.patches.tonal.vocal.ensemble import Angels, Choir
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.phrase import Hooks, Rhythms
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.progression import Progressions

RATE = 44100
BPM = 120
ORGAN = "pyoscillate.patches.tonal.keys.organ"
# one chord a bar: bar 0 is 0 to 2 s at 120 bpm. Everything but the drawbars
# is taken out of the signal, so the level is the held note's
PURE = {
    "percussion": 0,
    "click": 0,
    "leslie": 0,
    "drive": 0,
    "reverb_bal": 0,
    "attack": 0.005,
    "release": 0.03,
}


@cache
def _render(**params: float) -> Render:
    return render(ORGAN, {**PURE, **params}, seconds=2.6, bpm=BPM)


def _rms(result: Render, start: float, end: float) -> float:
    window = result.samples[round(start * RATE) : round(end * RATE)]
    return float(np.sqrt((window**2).mean()))


class ChordFrequencyTests(unittest.TestCase):
    def _choir(self) -> Choir:
        patch = Choir()
        patch.harmony = Harmony(key=Note.KEY_C)
        patch.progression = Progressions.JAZZ_TURNAROUND
        return patch

    def test_a_chord_is_stacked_in_the_chords_own_colour(self) -> None:
        patch = self._choir()

        # bar 0 is a D minor chord, bar 1 a G major chord
        for bar, pitch_class, triad in ((0, 2, (0, 3, 7)), (1, 7, (0, 4, 7))):
            root = Harmony.nearest(pitch_class, patch.root_freq)
            notes = patch.chord_frequencies(bar, Chords.TRIAD)
            for note, offset in zip(notes, triad, strict=True):
                with self.subTest(bar=bar, offset=offset):
                    self.assertAlmostEqual(
                        Note.freq_to_midi(note),
                        Note.freq_to_midi(Note.transpose(root, offset)),
                        places=4,
                    )

    def test_a_spread_chord_reaches_an_octave_below_and_above_the_root(self) -> None:
        patch = self._choir()

        notes = patch.chord_frequencies(0, Chords.SPREAD_TRIAD)
        root = Harmony.nearest(2, patch.root_freq)

        self.assertAlmostEqual(notes[0], root / 2, places=3)
        self.assertAlmostEqual(notes[1], root, places=3)
        self.assertAlmostEqual(notes[-1], root * 2, places=3)


class SoundingTests(unittest.TestCase):
    def _organ(self, phrase: object) -> Organ:
        patch = Organ()
        patch.harmony = Harmony(key=Note.KEY_A)
        patch.phrase = phrase
        return patch

    def test_a_chord_rhythm_sounds_the_whole_chord(self) -> None:
        patch = self._organ(Rhythms.BAR_PULSE)

        notes = patch.sounding(1.0, 0)

        self.assertEqual(notes, patch.chord_frequencies(0, Chords.TRIAD))
        self.assertEqual(len(notes), Organ.note_count())

    def test_a_figure_sounds_the_one_note_it_names(self) -> None:
        patch = self._organ(Hooks.SPARSE_HOOK)

        for tone in (0, 1, 2):
            with self.subTest(tone=tone):
                self.assertEqual(
                    patch.sounding(tone, 0), [patch.note_frequency(tone, 0)]
                )

    def test_voices_are_every_note_repeated_for_its_copies(self) -> None:
        patch = Choir()
        notes = [100.0, 200.0]

        pitches = patch.voice_pitches(notes)
        gains = patch.voice_gains(len(notes))

        self.assertEqual(Choir.voice_count(), len(pitches))
        # a short chord is padded with its last note, silenced by its gain
        self.assertEqual(pitches[:4], [100.0, 100.0, 200.0, 200.0])
        self.assertEqual(set(pitches[4:]), {200.0})
        self.assertEqual(gains, [1.0] * 4 + [0.0] * (len(gains) - 4))


class EnsembleTests(unittest.TestCase):
    def test_copies_are_spread_either_side_of_the_note(self) -> None:
        patch = Angels()

        ratios = patch.detune_ratios(20)

        # three copies of every note: flat, in tune, sharp
        first = ratios[:3]
        self.assertAlmostEqual(first[0], Note.semitone_ratio(-0.2))
        self.assertAlmostEqual(first[1], 1.0)
        self.assertAlmostEqual(first[2], Note.semitone_ratio(0.2))
        self.assertEqual(ratios, first * Angels.note_count())

    def test_no_spread_leaves_every_voice_in_tune(self) -> None:
        self.assertEqual(set(Angels().detune_ratios(0)), {1.0})

    def test_copies_vibrato_at_slightly_different_speeds(self) -> None:
        patch = Angels()

        rates = patch.vibrato_rates(5.0)

        self.assertEqual(len(set(rates[:3])), 3)
        self.assertAlmostEqual(rates[1], 5.0)
        self.assertLess(rates[0], 5.0)
        self.assertGreater(rates[2], 5.0)


class HoldTests(unittest.TestCase):
    def _organ(self, legato: float) -> Organ:
        patch = Organ(legato=legato)
        patch.phrase = Rhythms.BAR_PULSE
        # a bar pulse hits once a bar, 32 ticks apart at the default grid
        patch._division = SimpleNamespace(steps=32)
        return patch

    def test_a_longer_legato_holds_the_note_longer(self) -> None:
        holds = [self._organ(legato).hold_ticks(0) for legato in (0, 0.25, 0.5, 0.75)]

        self.assertEqual(holds, sorted(holds))
        self.assertEqual(len(set(holds)), len(holds))

    def test_a_note_lifts_before_the_next_unless_legato_is_full(self) -> None:
        gap = 32

        self.assertLess(self._organ(0.95).hold_ticks(0), gap)
        self.assertGreater(self._organ(1.0).hold_ticks(0), gap)

    def test_the_shortest_note_is_a_fraction_of_the_gap(self) -> None:
        self.assertAlmostEqual(
            self._organ(0).hold_ticks(0), 32 * Held.staccato, delta=1
        )


class HoldRenderTests(unittest.TestCase):
    def test_legato_zero_clips_the_chord_and_leaves_the_rest_of_the_bar_silent(
        self,
    ) -> None:
        clipped = _render(legato=0)
        held = _render(legato=1)

        # 1.0 to 1.5 s is well after a quarter-bar note, inside the held one
        self.assertLess(_rms(clipped, 1.0, 1.5), 0.02 * _rms(held, 1.0, 1.5))

    def test_a_longer_release_lets_the_note_linger_after_it_lifts(self) -> None:
        short = _render(legato=0, release=0.03)
        long = _render(legato=0, release=2.0)

        # the clipped note lifts at 0.5 s: just after it, only the release remains
        self.assertGreater(_rms(long, 0.7, 1.0), 10 * _rms(short, 0.7, 1.0))

    def test_full_legato_slurs_the_next_chord_into_the_held_one(self) -> None:
        # a slow attack makes a re-struck note start from silence at the bar line
        slurred = _render(legato=1, attack=1.5)
        struck = _render(legato=0.5, attack=1.5)

        self.assertGreater(_rms(slurred, 2.05, 2.25), 3 * _rms(struck, 2.05, 2.25))


class RateRangeTests(unittest.TestCase):
    def test_every_rate_on_the_slider_builds_a_chord_pulse(self) -> None:
        for rate in (Organ.rate.spec.minimum, Organ.rate.spec.maximum):
            with self.subTest(rate=rate):
                result = features(
                    render(ORGAN, {**PURE, "rate": rate}, seconds=1.2, bpm=BPM)
                )

                self.assertGreater(result.peak, 1e-4)


if __name__ == "__main__":
    unittest.main()
