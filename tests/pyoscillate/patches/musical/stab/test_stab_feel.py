"""`Stab.strum` and `Stab.feel`: what each stab writes onto its per-note
delays and envelopes, checked on stand-in nodes (no audio server)."""

import unittest
from types import SimpleNamespace

import numpy as np

from pyoscillate.analysis.render import render
from pyoscillate.patches.musical.stab.stab import Stab, StabVelvet

SAMPLE_RATE = 44100
MODULE = "pyoscillate.patches.musical.stab.stab"


def _chord(strum: float, feel: float) -> SimpleNamespace:
    intervals = (0, 3, 7, 10)
    voices = len(intervals)
    chord = SimpleNamespace(
        strum=strum,
        feel=feel,
        STRUM_SPAN=Stab.STRUM_SPAN,
        HUMAN_TIMING=Stab.HUMAN_TIMING,
        HUMAN_LEVEL=Stab.HUMAN_LEVEL,
        intervals=intervals,
        note_level=Stab.NOTE_LEVEL,
        register_centre=Stab.register_centre,
        octave=0,
        _step=lambda: SimpleNamespace(hit=True),
        _clock=SimpleNamespace(bar_index=0),
        harmony=SimpleNamespace(),
        chord_freq=lambda harmony, centre, bar: centre,
        _feel=SimpleNamespace(random=lambda: 1.0),
        voices=[SimpleNamespace(freq=0.0) for _ in range(voices)],
        note_delays=[SimpleNamespace(delay=-1.0) for _ in range(voices)],
        note_envs=[SimpleNamespace(mul=0.0) for _ in range(voices)],
        trigger=SimpleNamespace(play=lambda: None),
        _sample_rate=SAMPLE_RATE,
        whole_samples=lambda seconds: Stab.whole_samples(chord, seconds),
    )
    return chord


class StabFeelTests(unittest.TestCase):
    def test_defaults_play_one_block(self) -> None:
        chord = _chord(0, 0)
        Stab.next_step(chord)

        self.assertEqual([d.delay for d in chord.note_delays], [0.0] * 4)
        self.assertEqual([e.mul for e in chord.note_envs], [Stab.NOTE_LEVEL] * 4)

    def test_strum_spreads_notes_low_to_high(self) -> None:
        chord = _chord(1.0, 0)
        Stab.next_step(chord)

        delays = [d.delay for d in chord.note_delays]
        self.assertEqual(delays[0], 0.0)
        self.assertEqual(delays, sorted(delays))
        self.assertAlmostEqual(delays[-1], 3 * Stab.STRUM_SPAN)

    def test_feel_offsets_timing_and_softens_level(self) -> None:
        chord = _chord(0, 1.0)
        Stab.next_step(chord)

        self.assertAlmostEqual(chord.note_delays[0].delay, Stab.HUMAN_TIMING, places=4)
        self.assertAlmostEqual(
            chord.note_envs[0].mul, Stab.NOTE_LEVEL * (1 - Stab.HUMAN_LEVEL)
        )

    def test_delays_land_on_whole_samples(self) -> None:
        # a fractional delay splits the one-sample trigger pulse, which
        # `TrigEnv` ignores, so the note would never sound
        chord = _chord(0.37, 0.61)
        chord._feel = SimpleNamespace(random=lambda: 0.3137)
        Stab.next_step(chord)

        for note_delay in chord.note_delays:
            samples = note_delay.delay * SAMPLE_RATE
            self.assertAlmostEqual(samples, round(samples), places=6)

    def test_every_feel_value_still_sounds(self) -> None:
        for feel in (0.05, 0.37, 1.0):
            with self.subTest(feel=feel):
                result = render(MODULE, {"style": "velvet", "feel": feel}, seconds=3.0)
                self.assertGreater(float(np.abs(result.samples).max()), 0.01)

    def test_every_strum_value_still_sounds(self) -> None:
        for strum in (0.1, 0.37, 1.0):
            with self.subTest(strum=strum):
                result = render(
                    MODULE, {"style": "velvet", "strum": strum}, seconds=3.0
                )
                self.assertGreater(float(np.abs(result.samples).max()), 0.01)

    def test_styles_expose_both(self) -> None:
        self.assertIs(StabVelvet.strum.origin, Stab.strum)
        self.assertIs(StabVelvet.feel.origin, Stab.feel)


if __name__ == "__main__":
    unittest.main()
