"""Contracts every bowed solo string shares (`strings/bowed.py`)."""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING, Patch
from pyoscillate.patches.common import Body
from pyoscillate.patches.tonal.strings.bowed import (
    Bowed,
    Cello,
    DoubleBass,
    HurdyGurdy,
    Riti,
    Viola,
    Violin,
)
from pyoscillate.theory.phrase import Hooks
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.progression import Progressions

MODULE = "pyoscillate.patches.tonal.strings.bowed"
RATE = 44100
BPM = 120
INSTRUMENTS: tuple[type[Bowed], ...] = (
    Violin,
    Viola,
    Cello,
    DoubleBass,
    HurdyGurdy,
    Riti,
)
# the sparse hook on the eighth grid strikes at 0, 0.5, 1.0 s and the output
# fades in over ~0.2 s: measure the first note once the fade is over, and the
# second from its own start. A bow at the default Legato lifts a little before
# the next note
FIRST = (0.3, 0.42)
SECOND_START = (0.5, 0.54)
SECOND_LATER = (0.8, 0.9)
# settings that take everything but the bowed pitch out of the signal
PURE = {"vibrato": 0, "rosin_amount": 0, "body": 0, "glide": 0, "drone_level": 0}


def _style(cls: type[Patch]) -> str:
    return cls.name.rsplit("_", 1)[-1]


@cache
def _render(style: str, **params: float) -> Render:
    return render(MODULE, {"style": style, **params}, seconds=1.2, bpm=BPM)


def _hook(cls: type[Bowed], **params: float) -> dict[str, float]:
    """`params` with the sparse hook selected (a position in this
    instrument's own catalog), and only those that instrument has."""
    catalog = cls.phrase.catalog
    assert catalog is not None
    own = {param.name for param in cls.params}
    return {
        "phrase": catalog.index_of(Hooks.SPARSE_HOOK),
        **{name: value for name, value in params.items() if name in own},
    }


def _play(cls: type[Bowed], **params: float) -> Render:
    return _render(_style(cls), **_hook(cls, **params))


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _rms(samples: np.ndarray) -> float:
    return float(np.sqrt((samples**2).mean()))


def _spectrum(samples: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Power spectrum and its frequencies, zero-padded so a peak lands within a
    fraction of a hertz."""
    size = 8 * len(samples)
    spectrum = np.abs(np.fft.rfft(samples * np.hanning(len(samples)), size)) ** 2
    return spectrum, np.fft.rfftfreq(size, 1 / RATE)


def _high_share(result: Render, span: tuple[float, float], above: float) -> float:
    spectrum, freqs = _spectrum(_window(result, span))
    return float(spectrum[freqs > above].sum() / spectrum.sum())


def _off_pitch(samples: np.ndarray, pitch: float) -> float:
    """How far (Hz) the strongest partials sit from the nearest multiple of
    `pitch`: near zero when every partial belongs to one harmonic series."""
    spectrum, freqs = _spectrum(samples)
    peaks = [
        freq
        for index, freq in enumerate(freqs[1:-1], start=1)
        if 50 < freq < 8000
        and spectrum[index] > 0.0025 * spectrum.max()
        and spectrum[index] >= spectrum[index - 1]
        and spectrum[index] > spectrum[index + 1]
    ]
    return max(abs(freq - pitch * round(freq / pitch)) for freq in peaks)


class BowedTests(unittest.TestCase):
    def test_notes_are_the_chord_tones_in_the_chords_own_colour(self) -> None:
        for cls in INSTRUMENTS:
            patch = cls()
            patch.harmony = Harmony(key=Note.KEY_C)
            patch.progression = Progressions.JAZZ_TURNAROUND
            patch.phrase = Hooks.SPARSE_HOOK

            # bar 0 is a D minor chord, bar 1 a G major chord
            for bar, pitch_class, triad in ((0, 2, (0, 3, 7)), (1, 7, (0, 4, 7))):
                root = Harmony.nearest(pitch_class, patch.root_freq)
                for tone, offset in enumerate(triad):
                    with self.subTest(style=patch.name, bar=bar, tone=tone):
                        self.assertAlmostEqual(
                            Note.freq_to_midi(patch.note_frequency(tone, bar)),
                            Note.freq_to_midi(Note.transpose(root, offset)),
                            places=4,
                        )

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
                result = features(
                    render(
                        MODULE,
                        {"style": _style(cls)},
                        seconds=0.5,
                        clock_running=True,
                    )
                )

                self.assertGreater(result.peak, 1e-4)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                result = _play(cls)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)

    def test_every_partial_sits_on_the_bowed_pitch(self) -> None:
        # the first note is the key's root nearest each instrument's Register
        for cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                patch = cls()
                patch.harmony = Harmony(key=Note.KEY_A)
                patch.phrase = Hooks.SPARSE_HOOK
                result = _play(cls, **PURE)

                self.assertLess(
                    _off_pitch(_window(result, FIRST), patch.note_frequency(0, 0)),
                    3.0,
                )

    def test_every_note_sounds_at_a_similar_level(self) -> None:
        # the loop gains a note by its pitch times its ring time: the bow is
        # scaled to cancel that, so a low note is no quieter than a high one
        levels = [_rms(_window(_play(cls), (0.6, 0.9))) for cls in INSTRUMENTS]

        self.assertLess(max(levels), 2.0 * min(levels))

    def test_brightness_adds_high_partials(self) -> None:
        for cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                soft = _high_share(_play(cls, brightness=500, **PURE), FIRST, 2000)
                hard = _high_share(_play(cls, brightness=12000, **PURE), FIRST, 2000)

                self.assertGreater(hard, 3 * soft)

    def test_a_longer_attack_swells_in_more_slowly(self) -> None:
        # nothing rings on from the first note, so the second starts from silence
        def start_to_later(attack: float) -> float:
            result = _play(Violin, attack=attack, release=0.05, legato=0, resonance=0.1)
            return _rms(_window(result, SECOND_START)) / _rms(
                _window(result, SECOND_LATER)
            )

        self.assertGreater(start_to_later(0.02), 2 * start_to_later(1.0))

    def test_vibrato_spreads_the_pitch(self) -> None:
        def near_pitch(vibrato: float) -> float:
            patch = Violin()
            patch.harmony = Harmony(key=Note.KEY_A)
            patch.phrase = Hooks.SPARSE_HOOK
            pitch = patch.note_frequency(0, 0)
            result = _play(Violin, **{**PURE, "vibrato": vibrato})
            spectrum, freqs = _spectrum(_window(result, (0.3, 0.45)))
            return float(
                spectrum[abs(freqs - pitch) < 0.005 * pitch].sum() / spectrum.sum()
            )

        self.assertGreater(near_pitch(0), 1.5 * near_pitch(100))

    def test_legato_holds_a_note_toward_the_next(self) -> None:
        def gap(legato: float) -> float:
            result = _play(Violin, legato=legato, release=0.05, resonance=0.1)
            return _rms(_window(result, (0.42, 0.49)))

        self.assertLess(gap(0.0), 0.3 * gap(1.0))

    def test_resonance_lets_the_string_ring_after_the_bow_lifts(self) -> None:
        def ringing(resonance: float) -> float:
            result = _play(Violin, legato=0, release=0.05, resonance=resonance)
            return _rms(_window(result, (0.36, 0.48)))

        self.assertGreater(ringing(1.5), 3 * ringing(0.1))

    def test_rosin_adds_noise_to_the_tone(self) -> None:
        clean = _high_share(_play(Violin, rosin_amount=0.0), FIRST, 3000)
        rasping = _high_share(_play(Violin, rosin_amount=1.0), FIRST, 3000)

        self.assertGreater(rasping, 1.5 * clean)

    def test_body_adds_resonance_at_its_modes(self) -> None:
        def at_modes(cls: type[Bowed], body: float) -> float:
            spectrum, freqs = _spectrum(_window(_play(cls, body=body), FIRST))
            near = np.zeros_like(freqs, dtype=bool)
            for mode in cls.body_modes:
                near |= abs(freqs - mode) < 0.08 * mode
            return float(spectrum[near].sum() / spectrum.sum())

        for cls in INSTRUMENTS:
            if not issubclass(cls, Body):
                continue
            with self.subTest(style=cls.name):
                self.assertGreater(at_modes(cls, 1.0), at_modes(cls, 0.0))


class HurdyGurdyTests(unittest.TestCase):
    def test_a_drone_sounds_the_keys_tonic_underneath(self) -> None:
        # the key is A and the drone sits in the octave nearest D3: A2
        def near_tonic(drone: float) -> float:
            result = _play(HurdyGurdy, drone_level=drone, body=0)
            spectrum, freqs = _spectrum(_window(result, FIRST))
            return float(
                spectrum[abs(freqs - Note.A2) < 0.02 * Note.A2].sum() / spectrum.sum()
            )

        self.assertGreater(near_tonic(1.0), 3 * near_tonic(0.0))


if __name__ == "__main__":
    unittest.main()
