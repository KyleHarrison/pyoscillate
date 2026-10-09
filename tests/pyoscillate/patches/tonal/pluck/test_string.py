"""Contracts every plucked-string instrument shares (`pluck/string.py`)."""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features, spectral_centroid
from pyoscillate.analysis.render import Render, render
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING, Patch
from pyoscillate.patches.common import Body
from pyoscillate.patches.tonal.bass.standup import StandupBass
from pyoscillate.patches.tonal.pluck.folk import (
    Banjo,
    Dulcimer,
    Lute,
    Mandocello,
    Mandolin,
)
from pyoscillate.patches.tonal.pluck.guitar import GuitarAcoustic, GuitarElectric
from pyoscillate.patches.tonal.pluck.harp import Harp, Kora
from pyoscillate.patches.tonal.pluck.sitar import Sitar
from pyoscillate.patches.tonal.pluck.string import PluckedString
from pyoscillate.theory.phrase import Hooks
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.progression import Progressions

RATE = 44100
BPM = 120
# (module, class): every plucked instrument
INSTRUMENTS: tuple[tuple[str, type[PluckedString]], ...] = (
    ("guitar", GuitarAcoustic),
    ("guitar", GuitarElectric),
    ("folk", Banjo),
    ("folk", Mandolin),
    ("folk", Mandocello),
    ("folk", Lute),
    ("folk", Dulcimer),
    ("harp", Harp),
    ("harp", Kora),
    ("sitar", Sitar),
)
# the same sparse hook plays on all of them, so a strike lands at 0, 0.5, 1.0 s
# and the output's fade-in (~0.2 s) is over before the first one is measured
FIRST = (0.3, 0.45)
STRIKE = (0.52, 0.6)
TAIL = (0.88, 0.99)


def _module(name: str) -> str:
    return f"pyoscillate.patches.tonal.pluck.{name}"


def _style(cls: type[Patch]) -> str:
    return cls.name.rsplit("_", 1)[-1]


@cache
def _render(module: str, style: str, **params: float) -> Render:
    return render(
        module,
        {"style": style, **params},
        seconds=1.2,
        bpm=BPM,
    )


def _hook(cls: type[PluckedString], **params: float) -> dict[str, float]:
    """`params` with the sparse hook selected: the phrase is the dropdown's
    position of the member in this instrument's own catalog."""
    catalog = cls.phrase.catalog
    assert catalog is not None
    return {"phrase": catalog.index_of(Hooks.SPARSE_HOOK), **params}


def _play(cls: type[PluckedString], module: str, **params: float) -> Render:
    return _render(module, _style(cls), **_hook(cls, **params))


def _window(result: Render, span: tuple[float, float]) -> np.ndarray:
    return result.samples[round(span[0] * RATE) : round(span[1] * RATE)]


def _rms(samples: np.ndarray) -> float:
    return float(np.sqrt((samples**2).mean()))


def _centroid(result: Render, span: tuple[float, float]) -> float:
    return spectral_centroid(_window(result, span), RATE)


def _spectrum(samples: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Power spectrum and its frequencies, zero-padded so a peak lands within a
    fraction of a hertz."""
    size = 8 * len(samples)
    spectrum = np.abs(np.fft.rfft(samples * np.hanning(len(samples)), size)) ** 2
    return spectrum, np.fft.rfftfreq(size, 1 / RATE)


def _off_pitch(samples: np.ndarray, pitch: float, detune: float = 0.0) -> float:
    """How far (Hz) the strongest partials sit from the nearest multiple of
    `pitch`, beyond what `detune` (a fraction of the partial's frequency)
    allows: at most zero when every partial is on one harmonic series."""
    spectrum, freqs = _spectrum(samples)
    peaks = [
        freq
        for index, freq in enumerate(freqs[1:-1], start=1)
        if 50 < freq < 8000
        and spectrum[index] > 0.0025 * spectrum.max()
        and spectrum[index] >= spectrum[index - 1]
        and spectrum[index] > spectrum[index + 1]
    ]
    return max(
        abs(freq - pitch * round(freq / pitch)) - detune * freq for freq in peaks
    )


def _course_detune(cls: type[PluckedString]) -> float:
    """The widest a course sits from the harmonic series of the note, as a
    fraction of the frequency: a unison pair a few cents apart, but an octave
    pair is on the series."""
    return max(abs(ratio / round(ratio) - 1) for ratio, _ in cls.courses)


class PluckedStringTests(unittest.TestCase):
    def test_notes_are_the_chord_tones_in_the_chords_own_colour(self) -> None:
        for _, cls in INSTRUMENTS:
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
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                result = features(
                    render(
                        _module(module),
                        {"style": _style(cls)},
                        seconds=0.5,
                        clock_running=False,
                    )
                )

                self.assertLess(result.peak, 1e-4)

    def test_render_sounds_after_the_shared_clock_starts(self) -> None:
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                result = features(
                    render(
                        _module(module),
                        {"style": _style(cls)},
                        seconds=0.5,
                        clock_running=True,
                    )
                )

                self.assertGreater(result.peak, 1e-4)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                result = _play(cls, _module(module))

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)

    def test_the_first_note_is_not_swallowed_at_startup(self) -> None:
        # a control that glides up from zero at start (like a `live()` signal
        # feeding the pick comb) would swallow the first pluck
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                result = _play(cls, _module(module))

                self.assertGreater(
                    _rms(_window(result, FIRST)),
                    0.1 * _rms(_window(result, (0.55, 0.7))),
                )

    def test_every_partial_sits_on_the_struck_pitch(self) -> None:
        # the first strike is the key's root nearest each instrument's Register
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                patch = cls()
                patch.harmony = Harmony(key=Note.KEY_A)
                patch.phrase = Hooks.SPARSE_HOOK
                pitch = patch.note_frequency(0, 0)
                # a sitar's sympathetic strings and an instrument's body ring at
                # their own pitches
                quiet = {
                    name: 0
                    for name in ("body", "sympathy_level")
                    if any(param.name == name for param in cls.params)
                }
                result = _play(cls, _module(module), **quiet)

                self.assertLess(
                    _off_pitch(
                        _window(result, (0.27, 0.48)), pitch, _course_detune(cls)
                    ),
                    5.0,
                )

    def test_a_note_starts_brighter_than_it_ends(self) -> None:
        # the loop low-pass shaves the highs on every trip: the string mellows
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                result = _play(cls, _module(module))

                self.assertGreater(
                    _centroid(result, (0.5, 0.56)), _centroid(result, TAIL)
                )

    def test_brightness_raises_the_strike_centroid(self) -> None:
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                soft = _centroid(_play(cls, _module(module), brightness=500), STRIKE)
                hard = _centroid(_play(cls, _module(module), brightness=12000), STRIKE)

                self.assertGreater(hard, 1.5 * soft)

    def test_plucking_nearer_the_middle_is_more_mellow(self) -> None:
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                bridge = _centroid(_play(cls, _module(module), position=0.06), FIRST)
                middle = _centroid(_play(cls, _module(module), position=0.5), FIRST)

                self.assertGreater(bridge, 1.1 * middle)

    def test_longer_sustain_leaves_more_of_the_note_ringing(self) -> None:
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                tails = [
                    _rms(_window(_play(cls, _module(module), sustain=s), TAIL))
                    for s in (0.3, 2.5, 8.0)
                ]

                self.assertEqual(tails, sorted(tails))
                self.assertLess(tails[0], 0.2 * tails[-1])

    def test_body_adds_resonance_at_its_modes(self) -> None:
        def at_modes(cls: type[Body], module: str, body: float) -> float:
            spectrum, freqs = _spectrum(_window(_play(cls, module, body=body), STRIKE))
            near = np.zeros_like(freqs, dtype=bool)
            for mode in cls.body_modes:
                near |= abs(freqs - mode) < 0.08 * mode
            return float(spectrum[near].sum() / spectrum.sum())

        for module, cls in INSTRUMENTS:
            if not issubclass(cls, Body):
                continue
            with self.subTest(style=cls.name):
                self.assertGreater(
                    at_modes(cls, _module(module), 1.0),
                    at_modes(cls, _module(module), 0.0),
                )


class PluckedStringCoursesTests(unittest.TestCase):
    @staticmethod
    def peaks_at_eighth_partial(instrument: type[PluckedString], module: str) -> int:
        """How many separate spectral peaks the note's eighth partial has: a
        unison pair a few cents apart splits it into two."""
        patch = instrument()
        patch.harmony = Harmony(key=Note.KEY_A)
        patch.phrase = Hooks.SPARSE_HOOK
        partial = 8 * patch.note_frequency(0, 0)
        # half speed leaves the first note ringing alone for most of a second
        result = _play(instrument, _module(module), body=0, rate=-1, sustain=4.0)
        spectrum, freqs = _spectrum(_window(result, (0.3, 0.95)))
        near = spectrum[abs(freqs - partial) < 0.03 * partial]
        return sum(
            1
            for i in range(1, len(near) - 1)
            if near[i] >= near[i - 1]
            and near[i] > near[i + 1]
            and near[i] > 0.1 * near.max()
        )

    def test_paired_strings_split_each_partial(self) -> None:
        for module, cls in (
            ("folk", Mandolin),
            ("folk", Mandocello),
            ("folk", Lute),
            ("folk", Dulcimer),
        ):
            with self.subTest(style=cls.name):
                self.assertGreaterEqual(self.peaks_at_eighth_partial(cls, module), 2)

    def test_a_single_string_keeps_each_partial_whole(self) -> None:
        for module, cls in (
            ("folk", Banjo),
            ("guitar", GuitarAcoustic),
            ("harp", Harp),
        ):
            with self.subTest(style=cls.name):
                self.assertEqual(self.peaks_at_eighth_partial(cls, module), 1)


class StandupBassTests(unittest.TestCase):
    # BASS_CONVERSATION strikes at 0 and 1 s on the sixteenth grid
    FIRST_NOTE = (0.3, 0.9)

    @staticmethod
    def play(**params: float) -> Render:
        return render(
            "pyoscillate.patches.tonal.bass.standup", params, seconds=1.2, bpm=BPM
        )

    def test_the_line_is_the_chord_root_in_the_bass_register(self) -> None:
        patch = StandupBass()
        patch.harmony = Harmony(key=Note.KEY_A)

        self.assertAlmostEqual(
            Note.freq_to_midi(patch.note_frequency(0, 0)),
            Note.freq_to_midi(Note.A1),
            places=4,
        )

    def test_every_partial_sits_on_the_struck_pitch(self) -> None:
        result = self.play(body=0)

        self.assertLess(_off_pitch(_window(result, self.FIRST_NOTE), Note.A1), 3.0)

    def test_it_sits_below_the_guitar(self) -> None:
        bass = self.play()
        guitar = _play(GuitarAcoustic, _module("guitar"))

        self.assertLess(_centroid(bass, self.FIRST_NOTE), _centroid(guitar, FIRST))

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        self.assertLess(float(abs(self.play().samples).max()), PATCH_OUTPUT_CEILING)


class SitarTests(unittest.TestCase):
    def test_buzz_blooms_as_the_note_fades(self) -> None:
        def high_share(buzz: float, span: tuple[float, float]) -> float:
            spectrum, freqs = _spectrum(
                _window(_play(Sitar, _module("sitar"), buzz_amount=buzz), span)
            )
            return float(spectrum[freqs > 3000].sum() / spectrum.sum())

        self.assertGreater(high_share(1.0, TAIL), 1.5 * high_share(0.0, TAIL))

    def test_sympathetic_strings_add_to_the_ring(self) -> None:
        dry = _rms(_window(_play(Sitar, _module("sitar"), sympathy_level=0), TAIL))
        rich = _rms(_window(_play(Sitar, _module("sitar"), sympathy_level=1), TAIL))

        self.assertGreater(rich, 1.05 * dry)


class KoraTests(unittest.TestCase):
    def test_every_note_has_an_octave_string_above_it(self) -> None:
        # the octave string rings on the same harmonic series, so it shows as
        # more energy at the even partials: compare the kora to a single string
        def even_share(cls: type[PluckedString], module: str) -> float:
            patch = cls()
            patch.harmony = Harmony(key=Note.KEY_A)
            patch.phrase = Hooks.SPARSE_HOOK
            pitch = patch.note_frequency(0, 0)
            spectrum, freqs = _spectrum(
                _window(_play(cls, _module(module), body=0), (0.27, 0.48))
            )
            even = sum(
                spectrum[abs(freqs - pitch * k) < 0.02 * pitch].sum()
                for k in range(2, 12, 2)
            )
            odd = sum(
                spectrum[abs(freqs - pitch * k) < 0.02 * pitch].sum()
                for k in range(3, 12, 2)
            )
            return float(even / odd)

        self.assertGreater(even_share(Kora, "harp"), even_share(Harp, "harp"))


if __name__ == "__main__":
    unittest.main()
