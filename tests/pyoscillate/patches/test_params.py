"""Slider contract: a `scale="note"` slider can only produce in-tune note
frequencies, and every patch's Register (`root_freq`) slider is one."""

import importlib
import pkgutil
import unittest
from unittest.mock import MagicMock

import pyoscillate.patches
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch, start_server
from pyoscillate.patches.params import Param, SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.patches.utility.notes.notes import freq_to_midi, midi_to_freq

REGISTER = SliderSpec(
    "root_freq", notes.B0, notes.A2, 1, notes.A1, "Register", "", scale="note"
)


def _is_note(freq: float) -> bool:
    midi = freq_to_midi(freq)
    return abs(midi - round(midi)) < 1e-3


def _patch_parameters() -> dict[str, tuple[SliderSpec, ...]]:
    """Every `Patch` subclass's slider specs, derived from its `Param`s."""
    found = {}
    for info in pkgutil.walk_packages(
        pyoscillate.patches.__path__, "pyoscillate.patches."
    ):
        module = importlib.import_module(info.name)
        for name, value in vars(module).items():
            if (
                isinstance(value, type)
                and issubclass(value, Patch)
                and value is not Patch
            ):
                found[f"{info.name}.{name}"] = tuple(
                    param.spec for param in value.params
                )
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


class CutoffSliderTests(unittest.TestCase):
    CUTOFF = SliderSpec(
        "brightness", 80, 12000, 0.02, 1200, "Brightness", "", scale="cutoff"
    )

    def test_track_is_unit_range_with_one_tick_per_step(self):
        self.assertEqual(self.CUTOFF.to_position(80), 0)
        self.assertEqual(self.CUTOFF.to_position(12000), 1)
        self.assertEqual(self.CUTOFF.divisions, 50)

    def test_ends_map_to_the_declared_range(self):
        self.assertAlmostEqual(self.CUTOFF.from_position(0), 80)
        self.assertAlmostEqual(self.CUTOFF.from_position(1), 12000)

    def test_taper_spends_the_track_on_the_low_end(self):
        self.assertLess(self.CUTOFF.from_position(0.5), 1000)

    def test_position_round_trips_through_a_tick(self):
        position = self.CUTOFF.to_position(self.CUTOFF.from_position(0.3))
        self.assertAlmostEqual(position, 0.3)

    def test_stored_values_are_only_clamped(self):
        self.assertEqual(self.CUTOFF.snap(1234), 1234)
        self.assertEqual(self.CUTOFF.snap(50000), 12000)
        self.assertEqual(self.CUTOFF.snap(1), 80)

    def test_label_is_whole_hertz(self):
        self.assertEqual(self.CUTOFF.format(1234.4), "1234")


class _Voice(Patch):
    @Param(0, 1, 0.1, 0.5, "Tone", "")
    def tone(self, value: float) -> None:
        self.applied.append(value)

    depth = Param(0, 2, 0.1, 1.0, "Depth", "")

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.applied: list[float] = []
        self.voice = None
        self._bind()
        return self


class _Bright(_Voice):
    tone = _Voice.tone.replace(default=0.9)
    extra = Param(0, 1, 0.1, 0.0, "Extra", "")


CONTEXT = BuildContext(MagicMock(), MagicMock(), Harmony())


class ParamTests(unittest.TestCase):
    def setUp(self):
        # `_bind()` creates the volume `SigTo`, which needs a booted server
        self.server = start_server(audio="manual")

    def tearDown(self):
        self.server.shutdown()

    def test_constructor_can_override_output_volume(self):
        voice = _Voice(volume=0.8, tone=0.2)

        self.assertEqual(voice.volume, 0.8)
        self.assertEqual(voice.tone, 0.2)

    def test_value_is_per_instance_and_control_waits_for_build(self):
        voice = _Voice(tone=0.2)
        other = _Voice()
        self.assertEqual((voice.tone, other.tone), (0.2, 0.5))
        self.assertIsInstance(_Voice.tone, Param)
        self.assertFalse(hasattr(voice, "applied"))

    def test_build_applies_every_control_once_then_assignment_is_live(self):
        voice = _Voice(tone=0.2).build(CONTEXT)
        self.assertEqual(voice.applied, [0.2])
        voice.tone = 0.7
        _Voice.tone.write(voice, 0.3)
        self.assertEqual(voice.applied, [0.2, 0.7, 0.3])

    def test_subclass_override_keeps_order_and_control(self):
        self.assertEqual(
            [param.name for param in _Bright.params],
            ["volume", "tone", "depth", "extra"],
        )
        self.assertEqual(_Bright.tone.default, 0.9)
        self.assertEqual(_Voice.tone.default, 0.5)
        self.assertEqual(_Bright().build(CONTEXT).applied, [0.9])


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
