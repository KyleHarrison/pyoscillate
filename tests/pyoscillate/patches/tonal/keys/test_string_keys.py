"""Perceptual contract for the string keyboards (`keys/string_keys.py`): a
chord rhythm strikes every tone of the chord, Sustain and Mute set how long the
strings ring, Hardness sets how bright the strike is, Dynamics follows the
accents (a harpsichord does not), the harpsichord's registers add the octave
rank, the piano's pedal lets the other strings ring, the clavichord's Bebung
rocks the pitch, and the loudest corner stays clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The first strike sits under `Patch.start()`'s fade-in, so
tests measure later ones.
"""

import random
import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum, Wobble
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING, Patch
from pyoscillate.patches.tonal.keys.string_keys import (
    Clavichord,
    Harpsichord,
    KeyedString,
    Piano,
)
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.phrase import Hooks, Rhythms
from pyoscillate.theory.pitch import Note

RATE = 44100
BPM = 120
MODULE = "pyoscillate.patches.tonal.keys.string_keys"
INSTRUMENTS: tuple[type[KeyedString], ...] = (Piano, Harpsichord, Clavichord)
# a sparse hook on the eighth grid strikes at 0, 0.5, 1.0 s; a Charleston
# chord at 0 and 0.75 s. Windows are measured from the strike they follow
STRIKE = (0.5, 0.55)
CHORD = (0.78, 1.1)
# settings that take everything but the string out of the signal
PURE = {
    "body": 0,
    "pick_noise": 0,
    "looseness": 0,
    "vibrato": 0,
    "sympathy_level": 0,
}


def _style(cls: type[Patch]) -> str:
    return cls.name.rsplit("_", 1)[-1]


def _phrase(cls: type[KeyedString], member: object) -> float:
    catalog = cls.phrase.catalog
    assert catalog is not None
    return catalog.index_of(member)


@cache
def _render(style: str, seconds: float = 1.5, **params: float) -> Render:
    return render(MODULE, {"style": style, **params}, seconds=seconds, bpm=BPM)


def _hook(cls: type[KeyedString], **params: float) -> Render:
    own = {param.name for param in cls.params}
    settings = {
        "phrase": _phrase(cls, Hooks.SPARSE_HOOK),
        **{name: value for name, value in params.items() if name in own},
    }
    return _render(_style(cls), **settings)


def _chord(cls: type[KeyedString], **params: float) -> Render:
    own = {param.name for param in cls.params}
    settings = {
        "phrase": _phrase(cls, Rhythms.CHARLESTON),
        **{name: value for name, value in params.items() if name in own},
    }
    return _render(_style(cls), **settings)


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _rms(result: Render, span: tuple[float, float]) -> float:
    return float(np.sqrt((_window(result, span) ** 2).mean()))


class HealthTests(unittest.TestCase):
    def test_render_is_silent_until_the_shared_clock_ticks(self) -> None:
        for cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                result = features(
                    render(
                        MODULE,
                        {"style": _style(cls)},
                        seconds=0.5,
                        clock_running=False,
                    )
                )

                self.assertLess(result.peak, 1e-4)

    def test_render_sounds_after_the_shared_clock_starts(self) -> None:
        for cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                self.assertGreater(features(_hook(cls)).peak, 1e-3)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for cls in INSTRUMENTS:
            for name, play in (("hook", _hook), ("chord", _chord)):
                with self.subTest(style=cls.name, phrase=name):
                    result = play(cls)

                    self.assertLess(
                        float(abs(result.samples).max()), PATCH_OUTPUT_CEILING
                    )

    def test_the_loudest_corner_stays_under_the_patch_ceiling(self) -> None:
        for cls in INSTRUMENTS:
            loudest = {
                param.name: param.spec.maximum
                for param in (
                    cls.hardness,
                    cls.dynamics,
                    cls.brightness,
                    cls.sustain,
                    cls.body,
                    cls.doubling,
                    cls.spread,
                    cls.pick_noise,
                )
            }
            if cls is Piano:
                loudest["sympathy_level"] = Piano.sympathy_level.spec.maximum
            with self.subTest(style=cls.name):
                result = _chord(cls, **loudest)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)


class ChordTests(unittest.TestCase):
    def test_a_chord_rhythm_strikes_every_tone_of_the_chord(self) -> None:
        for cls in INSTRUMENTS:
            patch = cls()
            patch.harmony = Harmony(key=Note.KEY_A)
            spectrum = Spectrum.of(_window(_chord(cls, **PURE), CHORD), RATE)

            for tone in patch.chord_frequencies(0, cls.chord_shape):
                with self.subTest(style=cls.name, tone=round(tone, 1)):
                    self.assertGreater(
                        spectrum.peak_near(tone, 3), 20 * spectrum.floor_near(tone, 40)
                    )

    def test_a_figure_strikes_one_note_at_a_time(self) -> None:
        # the first note of the sparse hook is the root; the chord's third and
        # fifth are not struck until later notes
        for cls in INSTRUMENTS:
            patch = cls()
            patch.harmony = Harmony(key=Note.KEY_A)
            root, third, fifth = patch.chord_frequencies(0, Chords.TRIAD)
            spectrum = Spectrum.of(_window(_hook(cls, **PURE), (0.1, 0.45)), RATE)

            with self.subTest(style=cls.name):
                self.assertGreater(
                    spectrum.peak_near(root, 3), 50 * spectrum.peak_near(third, 3)
                )
                self.assertGreater(
                    spectrum.peak_near(root, 3), 50 * spectrum.peak_near(fifth, 3)
                )


class TouchTests(unittest.TestCase):
    def _level(self, cls: type[KeyedString], accent: float) -> float:
        patch = cls(looseness=0)
        patch._rng = random.Random(0)
        return patch.strike_level(accent)

    def test_a_harpsichord_plucks_with_the_same_force_whatever_the_accent(
        self,
    ) -> None:
        self.assertAlmostEqual(
            self._level(Harpsichord, 0.3), self._level(Harpsichord, 1.0)
        )

    def test_a_clavichord_follows_the_accents_closely(self) -> None:
        self.assertGreater(
            self._level(Clavichord, 1.0), 2 * self._level(Clavichord, 0.3)
        )


class RingTests(unittest.TestCase):
    def _fall(self, cls: type[KeyedString], **params: float) -> float:
        """How far the level falls from just after a strike to just before the
        next one: the closer to 1, the longer the string rings."""
        result = _hook(cls, **PURE, **params)
        return _rms(result, (0.82, 0.96)) / _rms(result, (0.52, 0.66))

    def test_a_longer_sustain_lets_the_strings_ring(self) -> None:
        for cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                self.assertGreater(
                    self._fall(cls, sustain=8.0), 1.5 * self._fall(cls, sustain=0.3)
                )

    def test_a_mute_shortens_the_ring(self) -> None:
        for cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                self.assertGreater(
                    self._fall(cls, mute=0, sustain=4.0),
                    1.5 * self._fall(cls, mute=1, sustain=4.0),
                )


class StrikeTests(unittest.TestCase):
    def _top(self, cls: type[KeyedString], low: float, **params: float) -> float:
        """The share of the strike's power above `low` Hz."""
        result = _hook(cls, **PURE, **params)
        return Spectrum.of(_window(result, STRIKE), RATE).share(low, 20000)

    def test_a_harder_hammer_makes_a_brighter_strike(self) -> None:
        for cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                self.assertGreater(
                    self._top(cls, 3000, hardness=1),
                    2 * self._top(cls, 3000, hardness=0),
                )

    def test_brightness_opens_the_top_of_the_strike(self) -> None:
        for cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                self.assertGreater(
                    self._top(cls, 2000, brightness=12000),
                    2 * self._top(cls, 2000, brightness=400),
                )


class InstrumentTests(unittest.TestCase):
    def test_the_harpsichords_registers_add_the_octave_rank(self) -> None:
        def octave(doubling: float) -> float:
            levels = Spectrum.of(
                _window(_chord(Harpsichord, doubling=doubling, **PURE), CHORD), RATE
            ).partial_levels(Note.A3, 2)
            return float(levels[1] - levels[0])

        self.assertGreater(octave(1.5), octave(0) + 2)

    def test_the_pianos_pedal_lets_the_other_strings_ring(self) -> None:
        dry = _rms(_hook(Piano, **{**PURE, "sympathy_level": 0}), (0.7, 0.95))
        pedal = _rms(_hook(Piano, **{**PURE, "sympathy_level": 1}), (0.7, 0.95))

        self.assertGreater(pedal, 1.3 * dry)

    def test_the_pianos_unison_strings_beat_when_they_are_detuned(self) -> None:
        def beating(spread: float) -> float:
            result = _chord(Piano, spread=spread, sustain=6.0, **PURE)
            return Wobble.level(_window(result, (1.0, 1.5)), RATE, 0.02)

        self.assertGreater(beating(30), beating(0) + 0.15)

    def test_a_clavichords_bebung_rocks_the_pitch(self) -> None:
        def swing(bebung: float) -> float:
            result = _hook(Clavichord, **{**PURE, "vibrato": bebung})
            samples = _window(result, (0.1, 0.45))
            return Wobble.pitch(samples, RATE, 190, 250)

        self.assertLess(swing(0), 8)
        self.assertGreater(swing(100), 40)


if __name__ == "__main__":
    unittest.main()
