"""The one place a phrase step becomes pitches (`Phrased.phrase_pitches`,
`common.py`): every voice family answers only where its root sits
(`root_for`), and what a voice plays and what the Flet timeline shows both come
from that, so the two cannot disagree."""

import unittest

from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, start_server
from pyoscillate.patches.common import Phrased, Step
from pyoscillate.patches.tonal.bass import TechnoBass
from pyoscillate.patches.tonal.bass.fm.fm import FmBassBark
from pyoscillate.patches.tonal.bass.funk.funk import FunkBass
from pyoscillate.patches.tonal.bass.groove import BassRolling
from pyoscillate.patches.tonal.bass.hover import BassHover
from pyoscillate.patches.tonal.bass.reese.reese import ReeseWobble
from pyoscillate.patches.tonal.keys.string_keys import Harpsichord
from pyoscillate.patches.tonal.lead.fm import LeadFmWind
from pyoscillate.patches.tonal.lead.lead import LeadBrass
from pyoscillate.patches.tonal.pluck.pluck import PluckHook
from pyoscillate.tempo import Tempo
from pyoscillate.theory.phrase import PhraseMode
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.progression import Progressions


class PhrasePitchTests(unittest.TestCase):
    PITCHED = (
        BassRolling,
        BassHover,
        FmBassBark,
        FunkBass,
        LeadBrass,
        LeadFmWind,
        PluckHook,
        ReeseWobble,
        Harpsichord,
        TechnoBass,
    )
    # voices that write the sounding pitch to one `pitch` signal per note
    STRUCK = (
        BassRolling,
        BassHover,
        FmBassBark,
        FunkBass,
        LeadFmWind,
        PluckHook,
        ReeseWobble,
        TechnoBass,
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server(audio="manual")
        cls.clock = Clock(Tempo(bpm=120))
        cls.clock.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.clock.stop()
        cls.server.stop()
        cls.server.shutdown()

    def built(self, patch_class: type[Phrased], key: int = Note.KEY_C) -> Phrased:
        patch = patch_class()
        patch.build(BuildContext(Tempo(bpm=120), self.clock, Harmony(key=key)))
        patch.progression = Progressions.JAZZ_TURNAROUND
        return patch

    def test_every_pitched_family_answers_where_its_root_sits(self) -> None:
        for patch_class in self.PITCHED:
            with self.subTest(patch=patch_class.__name__):
                patch = self.built(patch_class)
                for bar in range(4):
                    self.assertIsNotNone(patch.root_for(patch.harmony, bar))

    def test_a_phrase_step_resolves_to_the_note_the_voice_asks_for(self) -> None:
        for patch_class in self.PITCHED:
            patch = self.built(patch_class)
            phrase = patch.selected_phrase
            if phrase.mode is PhraseMode.NONE:
                continue
            for step in phrase.steps:
                for bar in range(4):
                    with self.subTest(patch=patch_class.__name__, at=step.at, bar=bar):
                        self.assertEqual(
                            patch.phrase_pitches(
                                patch.harmony, phrase, int(step.offset), bar
                            ),
                            [patch.note_frequency(int(step.offset), bar)],
                        )

    def test_a_struck_voice_plays_what_the_shared_method_reports(self) -> None:
        for patch_class in self.STRUCK:
            patch = self.built(patch_class)
            phrase = patch.selected_phrase
            for step in phrase.steps:
                with self.subTest(patch=patch_class.__name__, at=step.at):
                    patch._step = lambda s=step: Step(s.at, True, int(s.offset))
                    patch.next_step()
                    bar = patch._clock.bar_index
                    self.assertAlmostEqual(
                        patch.pitch.value,
                        patch.phrase_pitches(
                            patch.harmony, phrase, int(step.offset), bar
                        )[0],
                        places=4,
                    )

    def test_a_detuned_lead_plays_the_shared_note_through_its_oscillators(self) -> None:
        patch = self.built(LeadBrass)
        phrase = patch.selected_phrase
        for step in phrase.steps:
            with self.subTest(at=step.at):
                patch._step = lambda s=step: Step(s.at, True, int(s.offset))
                patch.next_step()
                note = patch.phrase_pitches(
                    patch.harmony, phrase, int(step.offset), patch._clock.bar_index
                )[0]
                self.assertAlmostEqual(
                    patch.pitch1.value,
                    Note.transpose(note, patch.osc1_detune),
                    places=4,
                )
                self.assertAlmostEqual(
                    patch.pitch2.value,
                    Note.transpose(note, patch.osc2_detune),
                    places=4,
                )

    def test_a_chord_following_bass_roots_on_its_own_centre_and_register(self) -> None:
        patch = self.built(BassRolling)
        for bar in range(4):
            expected = patch.chord_freq(patch.harmony, patch.register_centre, bar)
            self.assertAlmostEqual(
                patch.root_for(patch.harmony, bar), expected * 2**patch.octave
            )

    def test_a_fixed_pitch_bass_ignores_the_chords(self) -> None:
        for patch_class in (TechnoBass, BassHover, FmBassBark):
            patch = self.built(patch_class)
            with self.subTest(patch=patch_class.__name__):
                self.assertEqual(
                    {patch.root_for(patch.harmony, bar) for bar in range(4)},
                    {patch.root_freq},
                )

    def test_a_pluck_sounds_an_octave_above_the_chord_root(self) -> None:
        patch = self.built(PluckHook)
        for bar in range(4):
            self.assertAlmostEqual(
                patch.root_for(patch.harmony, bar),
                Note.transpose(
                    patch.chord_freq(patch.harmony, patch.root_freq, bar), 12
                ),
            )

    def test_a_voice_that_names_no_root_shows_and_plays_no_pitches(self) -> None:
        patch = self.built(Harpsichord)
        self.assertIsNone(Phrased.root_for(patch, patch.harmony, 0))

    def test_a_note_pool_phrase_is_left_to_the_voice(self) -> None:
        patch = self.built(Harpsichord)

        class Pool:
            mode = PhraseMode.POOL_INDEX

        self.assertEqual(patch.phrase_pitches(patch.harmony, Pool(), 0, 0), [])  # type: ignore[arg-type]
