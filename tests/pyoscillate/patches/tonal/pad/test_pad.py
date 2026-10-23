"""Perceptual contract for the subtractive pads (`pad/pad.py`): Brightness opens
the filter, Opening makes it bloom on a chord, Air adds noise under the tone,
Movement moves the sound and none at all holds it still, the hard-synced pads
sound at their master's pitch, Celestial Wash's ringing noise follows the
note, and no corner of the sliders makes the filter run away.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. The first hit sits under `Patch.start()`'s fade-in, so tests
measure later ones.

Findings
========

1. The filter ran away at the loudest corner
--------------------------------------------
Error:
    With Resonance 1, Opening 1 and Brightness at its maximum, five of the nine
    pads (Android Dreams, Dark City, Aurora, Portus, Post-Apocalyptic Sync
    Sweep) hit the 0.18 output ceiling at some point and were then silent for
    the rest of the render. Dark City did the same at its defaults, 5.7 s into
    a note, as its filter envelope opened to full.
Cause:
    pyo's `MoogLP` is stable at any resonance for a quiet input at the cutoffs
    below 10 kHz, but not for a hot input (the oscillators of a chord summed
    at full level, with noise) at a high cutoff, and the cutoff was allowed
    up to 18 kHz.
Change:
    The oscillators are trimmed before the filter (`voice_trim`) and the
    cutoff stops at `CUTOFF_CEILING`, 10 kHz. Checked by rendering every
    style 14 s at its defaults and at the loudest corner: none is silent
    afterwards.
Status:
    fixed - `SynthPad` in pad.py.

2. pyo's pulse oscillator is not a duty-cycle square
----------------------------------------------------
Error:
    A first build of the pads played every square an octave too high: a
    pulse at 110 Hz had its strongest partials at 220, 440 and 660 Hz, and a
    mean of 0.06 (a DC offset) at a duty of 0.5, where a square at 110 Hz has
    only odd partials and no offset.
Cause:
    `LFO(type=4, sharp=duty)` (the pulse type, which `lead/lead.py` treats as
    a duty cycle) is not a pulse of that width: at `sharp=0.5` it repeats
    twice per cycle and sits off zero.
Change:
    `Wave.oscillator` builds a square as a sawtooth minus itself delayed by
    `duty` of a period, which is zero-mean, band-limited, and has the width
    asked for. `test_the_second_oscillator_adds_the_octave` measures the pitch
    of a square (Terra Enceladus's, an octave down).
Status:
    fixed in the pads - `Wave` in pad.py. `lead/lead.py` still plays the
    type-4 pulse; not looked at here.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.pad.pad import (
    AndroidDreams,
    Aurora,
    CelestialWash,
    DarkCity,
    GalacticCathedral,
    GalacticChapel,
    Portus,
    PostApocalypticSyncSweep,
    SynthPad,
    TerraEnceladus,
)
from pyoscillate.theory.phrase import Rhythms
from pyoscillate.theory.pitch import Note

RATE = 44100
BPM = 120
MODULE = "pyoscillate.patches.tonal.pad.pad"
# the chord's root is the key's root nearest the Register: A3
ROOT = Note.A3
BAR = SynthPad.phrase.catalog.index_of(Rhythms.BAR_PULSE)
STYLES = {
    "dreams": AndroidDreams,
    "wash": CelestialWash,
    "city": DarkCity,
    "aurora": Aurora,
    "cathedral": GalacticCathedral,
    "chapel": GalacticChapel,
    "portus": Portus,
    "sweep": PostApocalypticSyncSweep,
    "enceladus": TerraEnceladus,
}
# a pad with its slow motion, its filter bloom and its room taken away: what
# is left is the oscillators through a static filter
STILL = {
    "movement": 0,
    "opening": 0,
    "resonance": 0,
    "spread": 0,
    "vibrato": 0,
    "reverb_bal": 0,
    "attack": 0.01,
    "legato": 1,
    "volume": 0.3,
}
LOUDEST = {
    "brightness": SynthPad.brightness.spec.maximum,
    "opening": 1,
    "resonance": 1,
    "air": 1,
    "movement": SynthPad.movement.spec.maximum,
}


@cache
def _render(style: str, seconds: float = 3.0, **params: float) -> Render:
    return render(
        MODULE, {"style": style, "phrase": BAR, **params}, seconds=seconds, bpm=BPM
    )


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _still(
    style: str, span: tuple[float, float] = (0.6, 1.8), **params: float
) -> Spectrum:
    return Spectrum.of(_window(_render(style, **{**STILL, **params}), span), RATE)


class HealthTests(unittest.TestCase):
    def test_every_style_is_silent_until_the_shared_clock_ticks(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                result = features(
                    render(MODULE, {"style": style}, seconds=0.5, clock_running=False)
                )

                self.assertLess(result.peak, 1e-4)

    def test_every_style_sounds_after_the_clock_starts(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                self.assertGreater(
                    features(render(MODULE, {"style": style}, seconds=3.0)).peak, 1e-3
                )

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                result = _render(style, seconds=6.0)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)

    def test_the_loudest_corner_neither_clips_nor_runs_away(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                result = _render(style, seconds=14.0, **LOUDEST)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)
                # the filter ran away and fell silent (finding 1)
                self.assertGreater(
                    float(abs(_window(result, (12.0, 14.0))).max()), 1e-4
                )

    def test_each_style_has_its_own_name(self) -> None:
        names = [cls.name for cls in STYLES.values()]

        self.assertEqual(len(set(names)), len(names))


class FilterTests(unittest.TestCase):
    def test_brightness_opens_the_filter(self) -> None:
        dull = _still("enceladus", brightness=300).share(2000, 20000)
        bright = _still("enceladus", brightness=9000).share(2000, 20000)

        self.assertGreater(bright, 5 * dull)

    def test_opening_blooms_the_filter_over_the_chord(self) -> None:
        def bloom(opening: float) -> float:
            result = _render("aurora", **{**STILL, "opening": opening, "attack": 0.1})
            early = Spectrum.of(_window(result, (0.5, 0.8)), RATE).centroid()
            late = Spectrum.of(_window(result, (1.5, 1.8)), RATE).centroid()
            return late / early

        self.assertGreater(bloom(1), 1.5 * bloom(0))

    def test_resonance_rings_at_the_cutoff(self) -> None:
        def ring(resonance: float) -> float:
            spectrum = _still("enceladus", brightness=1500, resonance=resonance)
            return spectrum.band(1100, 2200) / spectrum.band(300, 1100)

        self.assertGreater(ring(0.9), 1.3 * ring(0))


class SourceTests(unittest.TestCase):
    def test_air_adds_noise_under_the_tone(self) -> None:
        def hiss(air: float) -> float:
            return _still("enceladus", brightness=9000, air=air).band(5000, 9000)

        self.assertGreater(hiss(1), 5 * hiss(0))

    def test_the_second_oscillator_adds_the_octave(self) -> None:
        # Terra Enceladus is a sawtooth at the note and a square an octave down
        levels = _still("enceladus", brightness=3000).partial_levels(ROOT / 2, 3)

        self.assertGreater(levels[0], levels[1] - 6)

    def test_a_synced_pad_sounds_at_its_masters_pitch(self) -> None:
        # a synced oscillator repeats with its master whatever its own pitch,
        # so the sound has a partial at the master, two octaves below the note
        spectrum = _still("sweep", span=(1.0, 1.8), brightness=3000)

        master = ROOT / 4
        self.assertGreater(
            spectrum.peak_near(master, 3), 10 * spectrum.floor_near(master * 1.5, 12)
        )


class MovementTests(unittest.TestCase):
    def _swing(self, style: str, movement: float, speed: float = 1.0) -> float:
        """How far the spectral centroid swings inside one held chord, as a
        fraction of its mean."""
        result = _render(
            style,
            seconds=2.4,
            **{**STILL, "movement": movement, "movement_speed": speed},
        )
        centroids = [
            Spectrum.of(_window(result, (start, start + 0.2)), RATE).centroid()
            for start in np.arange(0.4, 1.8, 0.15)
        ]
        return (max(centroids) - min(centroids)) / float(np.mean(centroids))

    def test_movement_swings_the_filter_on_a_slow_tide(self) -> None:
        # Galactic Cathedral's only motion is its filter cutoff
        self.assertGreater(
            self._swing("cathedral", 1.5), 2 * self._swing("cathedral", 0)
        )

    def test_movement_sweeps_the_synced_oscillator(self) -> None:
        self.assertGreater(self._swing("sweep", 1.5), 2 * self._swing("sweep", 0))

    def test_movement_speed_sets_how_fast_the_tide_turns(self) -> None:
        # a slow tide has barely turned inside one chord, a fast one has
        # swung through several times
        self.assertGreater(
            self._swing("cathedral", 1.5, speed=1.2),
            1.5 * self._swing("cathedral", 1.5, speed=0.25),
        )


class WashTests(unittest.TestCase):
    def test_the_ringing_noise_follows_the_register(self) -> None:
        def pitch(root: float) -> float:
            result = _render("wash", seconds=3.5, attack=0.05, root_freq=root)
            return Spectrum.of(_window(result, (1.0, 3.0)), RATE).centroid()

        # the filter's key tracking carries the whole wash up with the note
        self.assertGreater(pitch(Note.A4), 1.5 * pitch(Note.A3))

    def test_it_fades_while_the_chord_is_held(self) -> None:
        result = _render("wash", seconds=12.0, legato=1)

        swell = float(np.sqrt((_window(result, (1.5, 3.0)) ** 2).mean()))
        faded = float(np.sqrt((_window(result, (9.0, 10.0)) ** 2).mean()))
        self.assertLess(faded, swell)


class AttackTests(unittest.TestCase):
    def test_a_slower_attack_swells_the_pad_in_more_gently(self) -> None:
        def front(attack: float) -> float:
            result = _render("enceladus", **{**STILL, "attack": attack})
            return float(np.sqrt((_window(result, (0.5, 0.6)) ** 2).mean()))

        self.assertGreater(front(0.01), 1.4 * front(1.5))


if __name__ == "__main__":
    unittest.main()
