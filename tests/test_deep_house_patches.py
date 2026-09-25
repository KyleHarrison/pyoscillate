import ast
import math
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import A, Harmony
from pyoscillate.patches import Patch, PatchRack, start_server
from pyoscillate.patches.drums.clap import clap
from pyoscillate.patches.drums.tom import tom
from pyoscillate.patches.musical.chord import chord
from pyoscillate.patches.tonal.bass import groove as bass
from pyoscillate.projects.deep_house.rack import BPM, PATCH_DEFS, TICKS_PER_BAR
from pyoscillate.tempo import Tempo


class ServerStartupTests(unittest.TestCase):
    @patch("pyoscillate.patches.base.Server")
    def test_silent_boot_failure_raises_before_start(
        self, server_type: MagicMock
    ) -> None:
        server = server_type.return_value
        server.getIsBooted.return_value = False
        server.getIsStarted.return_value = False

        with self.assertRaisesRegex(RuntimeError, "could not boot"):
            start_server(output_device=99)

        server.start.assert_not_called()


class ClockRateTests(unittest.TestCase):
    def test_rate_limits_follow_supported_note_divisions(self) -> None:
        self.assertEqual(Clock.rate_limits(NoteDivision.SIXTEENTH), (-4, 3))

    @patch("pyoscillate.clock.Pattern")
    def test_ticks_for_rate_supports_the_clap_slider_bounds(self, _: MagicMock) -> None:
        clock = Clock(Tempo(bpm=132), ticks_per_bar=256)
        minimum, maximum = Clock.rate_limits(NoteDivision.SIXTEENTH)

        self.assertEqual(clock.ticks_for_rate(NoteDivision.SIXTEENTH, minimum), 256)
        self.assertEqual(clock.ticks_for_rate(NoteDivision.SIXTEENTH, maximum), 2)

    def test_clap_rate_slider_uses_clock_limits(self) -> None:
        rate = next(spec for spec in clap.PARAMETERS if spec.name == "rate")

        self.assertEqual(
            (rate.minimum, rate.maximum),
            Clock.rate_limits(NoteDivision.SIXTEENTH),
        )


class PatchGraphOwnershipTests(unittest.TestCase):
    def test_every_patch_builder_declares_resources(self) -> None:
        patch_root = Path(__file__).parents[1] / "src" / "pyoscillate" / "patches"
        missing_resources = []

        for source_path in patch_root.rglob("*.py"):
            tree = ast.parse(source_path.read_text(), filename=str(source_path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Return) or not isinstance(
                    node.value, ast.Call
                ):
                    continue
                if (
                    not isinstance(node.value.func, ast.Name)
                    or node.value.func.id != "BuiltPatch"
                ):
                    continue
                resources = next(
                    (
                        keyword.value
                        for keyword in node.value.keywords
                        if keyword.arg == "resources"
                    ),
                    None,
                )
                if resources is None or (
                    isinstance(resources, (ast.Tuple, ast.List)) and not resources.elts
                ):
                    relative_path = source_path.relative_to(patch_root.parents[2])
                    missing_resources.append(f"{relative_path}:{node.lineno}")

        self.assertEqual(missing_resources, [])


class KickNativeCrashTests(unittest.TestCase):
    def test_two_kicks_survive_live_updates(self) -> None:
        code = """
from pyoscillate.clock import Clock
from pyoscillate.patches import PatchRack, start_server
from pyoscillate.patches.drums.kick import kick
from pyoscillate.tempo import Tempo

server = start_server(audio="manual")
tempo = Tempo(bpm=122)
clock = Clock(tempo)
clock.start()
rack = PatchRack()
rack.start("kick_round", kick.KickRound().build(tempo, clock))
punch = rack.start("kick_punch", kick.KickPunch().build(tempo, clock))
for index in range(500):
    punch.update({
        "level": 0.1 + (index % 19) * 0.05,
        "drive": (index % 17) * 0.05,
    })
    server.process()
rack.stop_all()
clock.stop()
server.stop()
server.shutdown()
"""
        result = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-c", code],
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


class DeepHousePatchSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server(audio="manual")
        cls.tempo = Tempo(bpm=BPM)
        cls.clock = Clock(cls.tempo, ticks_per_bar=TICKS_PER_BAR)
        cls.clock.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.clock.stop()
        cls.server.stop()
        cls.server.shutdown()

    def assert_patch_lifecycle(self, patch_def) -> None:
        rack = PatchRack()
        voice = patch_def.voice
        values = {spec.name: spec.default for spec in voice.parameters}
        build_kwargs = dict(values)
        if voice.needs_tempo:
            build_kwargs["tempo"] = self.tempo
        if voice.needs_clock:
            build_kwargs["clock"] = self.clock
        if voice.needs_harmony:
            build_kwargs["harmony"] = Harmony(progression=(0, 5, 10, 7))

        patch = voice.build(**build_kwargs)
        self.assertIsInstance(patch, Patch)
        rack.start(patch_def.name, patch)
        patch.update(values)
        rate = next(
            (spec for spec in voice.parameters if spec.name == "rate"), None
        )
        if rate is not None:
            patch.set("rate", rate.maximum)
        rack.stop(patch_def.name)

    def test_chord_retains_native_trigger_graph(self) -> None:
        patch = chord.build(self.tempo, self.clock, "velvet")
        resource_types = [type(resource).__name__ for resource in patch.resources]

        self.assertIn("Trig", resource_types)
        self.assertIn("TrigEnv", resource_types)
        self.assertEqual(resource_types.count("Osc"), len(chord.INTERVALS))

    def sounding_roots(self, harmony: Harmony) -> dict[str, float]:
        """Fire each pitched patch's sequencer up to its first note in the
        clock's current bar, and return the pitch it played, divided by the
        interval its pattern puts on that note - i.e. the chord root it used."""
        chord_patch = chord.build(self.tempo, self.clock, "velvet", harmony=harmony)
        bass_patch = bass.build(self.tempo, self.clock, "rolling", harmony=harmony)
        tom_patch = tom.Tom().build(self.tempo, self.clock, harmony=harmony)
        # the chord stabs on the third 16th, the bass on the first, the tom's
        # first fill note (a fifth up) on the eleventh
        for _ in range(3):
            chord_patch.sequencer.callback()
        bass_patch.sequencer.callback()
        for _ in range(11):
            tom_patch.sequencer.callback()
        chord_osc = next(r for r in chord_patch.resources if type(r).__name__ == "Osc")
        bass_osc = next(r for r in bass_patch.resources if type(r).__name__ == "Osc")
        tom_tuning = next(r for r in tom_patch.resources if type(r).__name__ == "Sig")
        fifth = 2 ** (7 / 12)
        return {
            "chord": chord_osc.freq,
            "bass": bass_osc.freq,
            "tom": tom_tuning.value * tom.BODY_FREQ / fifth,
        }

    def assert_same_pitch_class(self, roots: dict[str, float], expected: int) -> None:
        for name, frequency in roots.items():
            with self.subTest(part=name):
                pitch_class = round(69 + 12 * math.log2(frequency / 440)) % 12
                self.assertEqual(pitch_class, expected)

    def test_bass_chord_and_tom_change_chord_on_the_same_bar(self) -> None:
        harmony = Harmony(key=A, progression=(0, 5, 10, 7))
        saved_tick = self.clock._tick
        try:
            for bar, pitch_class in enumerate((9, 2, 7, 4)):  # A, D, G, E
                self.clock._tick = bar * self.clock.bar
                with self.subTest(bar=bar):
                    self.assert_same_pitch_class(
                        self.sounding_roots(harmony), pitch_class
                    )
        finally:
            self.clock._tick = saved_tick

    def test_changing_the_key_moves_every_part_together(self) -> None:
        harmony = Harmony(key=A, progression=(0, 5, 10, 7))
        saved_tick = self.clock._tick
        try:
            self.clock._tick = 0
            harmony.key = 0  # C
            self.assert_same_pitch_class(self.sounding_roots(harmony), 0)
        finally:
            self.clock._tick = saved_tick


def make_lifecycle_test(patch_def):
    def test_lifecycle(self: DeepHousePatchSmokeTests) -> None:
        self.assert_patch_lifecycle(patch_def)

    return test_lifecycle


for definition in PATCH_DEFS:
    setattr(
        DeepHousePatchSmokeTests,
        f"test_{definition.name}_lifecycle",
        make_lifecycle_test(definition),
    )


if __name__ == "__main__":
    unittest.main()
