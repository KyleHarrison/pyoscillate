"""Contracts every plucked-string instrument shares (`pluck/string.py`)."""

import random
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
    """The widest a course sits from the harmonic series of the note at the
    instrument's own Spread, as a fraction of the frequency: a unison pair a
    few cents apart, but an octave pair is on the series."""
    spread = next((p.default for p in cls.params if p.name == "spread"), 0)
    return max(
        abs(Note.semitone_ratio(index * spread / 100) - 1)
        for index in range(len(cls.courses))
    )


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
                # their own pitches, and a bend, vibrato or loose hand moves
                # the string off it
                quiet = {
                    name: 0
                    for name in (
                        "body",
                        "sympathy_level",
                        "bend",
                        "vibrato",
                        "looseness",
                        "pick_noise",
                    )
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
    def peaks_at_eighth_partial(
        instrument: type[PluckedString], module: str, **params: float
    ) -> int:
        """How many separate spectral peaks the note's eighth partial has: a
        unison pair a few cents apart splits it into two."""
        patch = instrument()
        patch.harmony = Harmony(key=Note.KEY_A)
        patch.phrase = Hooks.SPARSE_HOOK
        partial = 8 * patch.note_frequency(0, 0)
        # half speed leaves the first note ringing alone for most of a second
        result = _play(
            instrument, _module(module), body=0, rate=-1, sustain=4.0, **params
        )
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
        # a loose hand drifts the note off the unplayed strings' exact tuning
        def tail(sympathy: float) -> float:
            return _rms(
                _window(
                    _play(
                        Sitar,
                        _module("sitar"),
                        sympathy_level=sympathy,
                        looseness=0,
                        bend=0,
                    ),
                    TAIL,
                )
            )

        dry, rich = tail(0), tail(1)

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
            # a harp's open strings ring on a series of their own
            quiet = {
                name: 0
                for name in ("sympathy_level", "looseness")
                if any(param.name == name for param in cls.params)
            }
            spectrum, freqs = _spectrum(
                _window(_play(cls, _module(module), body=0, **quiet), (0.27, 0.48))
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


class PluckedStringCharacterTests(unittest.TestCase):
    """Every instrument is its own: shared controls with their own starting
    values, and at least one control only its kind of instrument has."""

    SHARED = {param.name for param in PluckedString.params} | {
        param.name for param in Body.params
    }

    def test_no_two_instruments_start_the_same(self) -> None:
        starts = {
            cls.name: tuple(
                (param.name, param.default)
                for param in cls.params
                if param.name != "phrase"
            )
            for _, cls in INSTRUMENTS
        }

        self.assertEqual(len(set(starts.values())), len(starts))

    def test_every_instrument_has_a_control_of_its_own(self) -> None:
        for _, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                own = {param.name for param in cls.params} - self.SHARED

                self.assertTrue(own, "needs a signature control")

    def test_each_shared_control_has_its_own_start_across_the_family(self) -> None:
        # a control that every instrument starts at the same value is not
        # shaping anyone's character
        for name in ("hardness", "dynamics", "looseness", "pick_noise", "brightness"):
            with self.subTest(control=name):
                defaults = {
                    next(p for p in cls.params if p.name == name).default
                    for _, cls in INSTRUMENTS
                }

                self.assertGreater(len(defaults), 3)

    def test_a_harder_strike_is_sharper(self) -> None:
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                soft = _centroid(_play(cls, _module(module), hardness=0), STRIKE)
                hard = _centroid(_play(cls, _module(module), hardness=1), STRIKE)

                self.assertGreater(hard, soft)

    def test_a_muted_hand_cuts_the_ring_short(self) -> None:
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                free = _rms(_window(_play(cls, _module(module), mute=0), TAIL))
                muted = _rms(_window(_play(cls, _module(module), mute=1), TAIL))

                self.assertLess(muted, 0.3 * free)

    def test_vibrato_rocks_the_partials_off_the_pitch(self) -> None:
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                patch = cls()
                patch.harmony = Harmony(key=Note.KEY_A)
                patch.phrase = Hooks.SPARSE_HOOK
                pitch = patch.note_frequency(0, 0)
                quiet = {
                    name: 0
                    for name in ("body", "bend", "looseness", "sympathy_level")
                    if any(param.name == name for param in cls.params)
                }
                steady = _play(cls, _module(module), vibrato=0, **quiet)
                rocked = _play(cls, _module(module), vibrato=100, **quiet)
                span = (0.27, 0.48)

                self.assertGreater(
                    _off_pitch(_window(rocked, span), pitch),
                    _off_pitch(_window(steady, span), pitch) + 1.0,
                )

    def test_the_pick_is_heard_at_the_strike(self) -> None:
        for module, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                click = (0.5, 0.512)
                bare = _centroid(_play(cls, _module(module), pick_noise=0), click)
                picked = _centroid(_play(cls, _module(module), pick_noise=1), click)

                self.assertGreater(picked, bare)

    def test_body_size_moves_the_resonances(self) -> None:
        def lift(cls: type[Body], module: str, size: float) -> float:
            """How much the body adds near the modes of a body 1.6 times as big,
            against the same string with no body."""

            def near(**params: float) -> float:
                quiet = {
                    name: 0
                    for name in ("sympathy_level", "looseness", "pick_noise")
                    if any(param.name == name for param in cls.params)
                }
                spectrum, freqs = _spectrum(
                    _window(_play(cls, module, **quiet, **params), STRIKE)
                )
                band = np.zeros_like(freqs, dtype=bool)
                for mode in cls.body_modes:
                    band |= abs(freqs - 1.6 * mode) < 0.06 * mode
                return float(spectrum[band].sum() / spectrum.sum())

            return near(body=1, body_size=size) / near(body=0)

        for module, cls in INSTRUMENTS:
            if not issubclass(cls, Body):
                continue
            with self.subTest(style=cls.name):
                self.assertGreater(
                    lift(cls, _module(module), 1.6), lift(cls, _module(module), 0.6)
                )

    def test_dynamics_lean_on_the_accents_and_looseness_varies_the_touch(self) -> None:
        for _, cls in INSTRUMENTS:
            with self.subTest(style=cls.name):
                patch = cls()
                patch.looseness = 0
                patch._rng = random.Random(0)

                patch.dynamics = 0
                flat = patch.strike_level(0.4)
                patch.dynamics = 1
                leaning = patch.strike_level(0.4)
                patch.looseness = 1
                loose = {patch.strike_level(1.0) for _ in range(8)}

                self.assertLess(leaning, flat)
                self.assertGreater(len(loose), 1)


class PluckedStringCoursesCharacterTests(unittest.TestCase):
    def test_spread_sets_how_far_the_pair_beats(self) -> None:
        for module, cls in (("folk", Mandolin), ("folk", Lute), ("folk", Dulcimer)):
            with self.subTest(style=cls.name):
                self.assertEqual(
                    PluckedStringCoursesTests.peaks_at_eighth_partial(
                        cls, module, spread=0
                    ),
                    1,
                )
                self.assertGreaterEqual(
                    PluckedStringCoursesTests.peaks_at_eighth_partial(
                        cls, module, spread=20
                    ),
                    2,
                )

    def test_doubling_none_leaves_a_single_string(self) -> None:
        self.assertEqual(
            PluckedStringCoursesTests.peaks_at_eighth_partial(
                Mandolin, "folk", doubling=0
            ),
            1,
        )

    def test_a_twelve_string_adds_octave_strings(self) -> None:
        def octave_share(doubling: float) -> float:
            patch = GuitarAcoustic()
            patch.harmony = Harmony(key=Note.KEY_A)
            patch.phrase = Hooks.SPARSE_HOOK
            pitch = patch.note_frequency(0, 0)
            result = _play(
                GuitarAcoustic,
                _module("guitar"),
                body=0,
                looseness=0,
                doubling=doubling,
            )
            spectrum, freqs = _spectrum(_window(result, (0.27, 0.48)))
            near = lambda k: spectrum[abs(freqs - pitch * k) < 0.02 * pitch].sum()
            return float(near(2) / near(1))

        self.assertGreater(octave_share(1.0), 1.5 * octave_share(0.0))


class SympathyTests(unittest.TestCase):
    def test_a_harps_open_strings_ring_in_answer(self) -> None:
        def tail(level: float) -> float:
            return _rms(
                _window(
                    _play(
                        Harp,
                        _module("harp"),
                        sympathy_level=level,
                        looseness=0,
                        body=0,
                    ),
                    TAIL,
                )
            )

        self.assertGreater(tail(1.0), 1.05 * tail(0.0))

    def test_sympathy_ring_sets_how_long_they_hang(self) -> None:
        def tail(ring: float) -> float:
            return _rms(
                _window(
                    _play(
                        Sitar,
                        _module("sitar"),
                        sympathy_level=1,
                        sympathy_ring=ring,
                        looseness=0,
                        bend=0,
                    ),
                    TAIL,
                )
            )

        self.assertGreater(tail(6.0), tail(0.5))


class SignatureControlTests(unittest.TestCase):
    def test_twang_brings_forward_the_banjos_nasal_band(self) -> None:
        def share(twang: float) -> float:
            spectrum, freqs = _spectrum(
                _window(_play(Banjo, _module("folk"), twang=twang, body=0), STRIKE)
            )
            band = (freqs > 1800) & (freqs < 3000)
            return float(spectrum[band].sum() / spectrum.sum())

        self.assertGreater(share(1.0), 1.1 * share(0.0))

    def test_tremolo_pulses_the_electric_guitars_level(self) -> None:
        span = (0.55, 0.95)

        def levels(tremolo: float) -> np.ndarray:
            samples = _window(
                _render(_module("guitar"), "electric", tremolo=tremolo, looseness=0),
                span,
            )
            frames = samples[: len(samples) // 882 * 882].reshape(-1, 882)
            return np.sqrt((frames**2).mean(axis=1))

        ratio = levels(1.0) / levels(0.0)

        self.assertGreater(float(ratio.std() / ratio.mean()), 0.2)

    def test_a_closed_speaker_darkens_the_amp(self) -> None:
        closed = _centroid(
            _render(_module("guitar"), "electric", speaker=2000, drive=1), FIRST
        )
        open_ = _centroid(
            _render(_module("guitar"), "electric", speaker=9000, drive=1), FIRST
        )

        self.assertGreater(open_, 1.1 * closed)

    def test_grit_roughens_the_bass(self) -> None:
        def high_share(grit: float) -> float:
            result = render(
                "pyoscillate.patches.tonal.bass.standup",
                {"grit_amount": grit},
                seconds=1.2,
                bpm=BPM,
            )
            spectrum, freqs = _spectrum(_window(result, (0.3, 0.9)))
            return float(spectrum[freqs > 1000].sum() / spectrum.sum())

        self.assertGreater(high_share(1.0), 1.3 * high_share(0.0))

    def test_a_bend_reshapes_the_start_of_the_note(self) -> None:
        # the string is still tuning in while it is struck, so the opening
        # of the note sounds different from a clean strike
        def opening(bend: float) -> float:
            result = _play(
                GuitarAcoustic,
                _module("guitar"),
                bend=bend,
                looseness=0,
                pick_noise=0,
                body=0,
            )
            return _centroid(result, (0.5, 0.52))

        self.assertGreater(abs(opening(-12) - opening(0)), 0.1 * opening(0))


if __name__ == "__main__":
    unittest.main()
