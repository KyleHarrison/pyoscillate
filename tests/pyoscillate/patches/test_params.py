"""Slider contract: a `scale="note"` slider can only produce in-tune note
frequencies, and every patch's Register (`root_freq`) slider is one."""

import importlib
import pkgutil
import unittest

import pyoscillate.patches
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.patches.utility.notes.notes import freq_to_midi, midi_to_freq

REGISTER = SliderSpec("root_freq", notes.B0, notes.A2, 1, notes.A1, "Register", "", scale="note")


def _is_note(freq: float) -> bool:
    midi = freq_to_midi(freq)
    return abs(midi - round(midi)) < 1e-3


def _patch_parameters() -> dict[str, tuple[SliderSpec, ...]]:
    found = {}
    for info in pkgutil.walk_packages(pyoscillate.patches.__path__, "pyoscillate.patches."):
        module = importlib.import_module(info.name)
        if isinstance(getattr(module, "PARAMETERS", None), tuple):
            found[info.name] = module.PARAMETERS
    return found


class NoteHelperTests(unittest.TestCase):
    def test_midi_and_freq_round_trip(self):
        self.assertAlmostEqual(midi_to_freq(69), 440)
        self.assertAlmostEqual(freq_to_midi(notes.A1), 33, places=4)

    def test_note_names_match_the_rack_key_spelling(self):
        self.assertEqual(notes.note_name(notes.A1), "A1")
        self.assertEqual(notes.note_name(notes.Fs2), "F#2")
        self.assertEqual(notes.note_name(notes.Ds2), "Eb2")
        self.assertEqual(notes.note_name(notes.C0), "C0")

    def test_short_aliases_match_their_members(self):
        for member in notes.Note:
            with self.subTest(note=member.name):
                self.assertEqual(getattr(notes, member.name), member.value)


class NoteSliderTests(unittest.TestCase):
    def test_every_tick_is_a_semitone(self):
        # B0..A2 is 22 semitones
        self.assertEqual(REGISTER.divisions, 22)
        low = REGISTER.to_position(REGISTER.minimum)
        for tick in range(REGISTER.divisions + 1):
            freq = REGISTER.from_position(low + tick)
            with self.subTest(tick=tick):
                self.assertTrue(_is_note(freq), freq)

    def test_positions_between_ticks_snap_to_a_note(self):
        position = REGISTER.to_position(notes.A1) + 0.4
        self.assertAlmostEqual(REGISTER.from_position(position), notes.A1, places=2)

    def test_stored_values_snap_to_the_nearest_note_in_range(self):
        self.assertAlmostEqual(REGISTER.snap(92), notes.Fs2, places=2)
        self.assertAlmostEqual(REGISTER.snap(10), notes.B0, places=2)
        self.assertAlmostEqual(REGISTER.snap(500), notes.A2, places=2)

    def test_label_is_the_note_name(self):
        self.assertEqual(REGISTER.format(notes.A1), "A1")

    def test_linear_sliders_are_unchanged(self):
        spec = SliderSpec("decay", 0.05, 2, 0.05, 0.3, "Decay", "")
        self.assertEqual(spec.divisions, 39)
        self.assertEqual(spec.from_position(0.3), 0.3)
        self.assertEqual(spec.snap(5), 5)
        self.assertEqual(spec.format(0.3), "0.30")


class PatchRegisterTests(unittest.TestCase):
    def test_every_register_slider_steps_through_notes(self):
        registers = {
            module: spec
            for module, parameters in _patch_parameters().items()
            for spec in parameters
            if spec.name == "root_freq"
        }
        self.assertTrue(registers)
        for module, spec in registers.items():
            with self.subTest(module=module):
                self.assertEqual(spec.scale, "note")
                for freq in (spec.minimum, spec.maximum, spec.default):
                    self.assertTrue(_is_note(freq), f"{freq} Hz is not a note")
                self.assertLessEqual(spec.minimum, spec.default)
                self.assertLessEqual(spec.default, spec.maximum)


if __name__ == "__main__":
    unittest.main()
