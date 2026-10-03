import math
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch, start_server
from pyoscillate.patches.drums.clap import clap
from pyoscillate.patches.drums.tom import tom
from pyoscillate.patches.musical.arp import arp
from pyoscillate.patches.musical.stab import stab
from pyoscillate.patches.params import RateParam
from pyoscillate.patches.tonal.bass import groove as bass
from pyoscillate.projects.deep_house.rack import DeepHouseRack
from pyoscillate.tempo import Tempo
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.progression import Progressions


class ServerStartupTests(unittest.TestCase):
    @patch("pyoscillate.patches.base.Server")
    def test_silent_boot_failure_raises_before_start(
        self, server_type: MagicMock
    ) -> None:
        server = server_type.return_value
        server.getIsBooted.return_value = False
        server.getIsStarted.return_value = False

        with self.assertRaisesRegex(RuntimeError, "could not boot"):
            start_server()

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
        rate = clap.Clap.rate.spec

        self.assertEqual(
            (rate.minimum, rate.maximum),
            Clock.rate_limits(NoteDivision.SIXTEENTH),
        )


class KickNativeCrashTests(unittest.TestCase):
    def test_two_kicks_survive_live_updates(self) -> None:
        code = """
from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, start_server
from pyoscillate.patches.drums.kick import kick
from pyoscillate.tempo import Tempo
from pyoscillate.theory.chord import Chords

server = start_server(audio="manual")
tempo = Tempo(bpm=122)
clock = Clock(tempo)
clock.start()
context = BuildContext(tempo, clock, Harmony())
round_kick = kick.KickRound().build(context).start()
punch = kick.KickPunch().build(context).start()
for index in range(500):
    punch.level = 0.1 + (index % 19) * 0.05
    punch.drive = (index % 17) * 0.05
    server.process()
round_kick.stop()
punch.stop()
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
        cls.rack = DeepHouseRack()
        cls.server = start_server(audio="manual")
        cls.tempo = Tempo(bpm=cls.rack.bpm)
        cls.clock = Clock(cls.tempo, ticks_per_bar=cls.rack.ticks_per_bar)
        cls.clock.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.clock.stop()
        cls.server.stop()
        cls.server.shutdown()

    def test_every_patch_survives_its_lifecycle(self) -> None:
        context = BuildContext(self.tempo, self.clock, self.rack.harmony)
        for group in self.rack.groups:
            for voice in group.patches:
                with self.subTest(patch=voice.name):
                    for param in voice.params:
                        param.write(voice, param.default)

                    patch = voice.build(context)
                    self.assertIsInstance(patch, Patch)
                    patch.start()
                    for param in voice.params:
                        param.write(voice, param.default)
                        if isinstance(param, RateParam):
                            param.write(voice, param.spec.maximum)
                    patch.stop()

    def test_chord_retains_native_trigger_graph(self) -> None:
        patch = stab.StabVelvet().build(BuildContext(self.tempo, self.clock, Harmony()))
        resource_types = [type(resource).__name__ for resource in patch.resources]

        self.assertIn("Trig", resource_types)
        self.assertIn("TrigEnv", resource_types)
        self.assertEqual(resource_types.count("Osc"), len(Chords.SEVENTH_CHORD.offsets))

    def test_arp_glide_and_gate_follow_tempo(self) -> None:
        patch = arp.Arp()
        built = patch.build(BuildContext(self.tempo, self.clock, Harmony()))
        bpm = self.tempo.bpm
        self.addCleanup(self.tempo.set_bpm, bpm)
        glide, gate = patch.mid_freq.time, patch.gate_env.dur

        self.tempo.set_bpm(bpm * 2)
        built.retempo()

        self.assertAlmostEqual(patch.mid_freq.time, glide / 2, places=4)
        self.assertAlmostEqual(patch.gate_env.dur, gate / 2, places=4)

    def test_chord_voice_count_follows_voicing(self) -> None:
        context = BuildContext(self.tempo, self.clock, Harmony())
        for index in (0, 1, 33, 74):
            with self.subTest(voicing=index):
                voice = stab.StabVelvet()
                stab.StabVelvet.voicing.write(voice, index)
                patch = voice.build(context)
                resource_types = [type(r).__name__ for r in patch.resources]
                self.assertEqual(
                    resource_types.count("Osc"),
                    len(Chords.by_index(index).offsets),
                )
                loudness = sum(env.mul for env in patch.note_envs)
                self.assertAlmostEqual(loudness, 4 * stab.Stab.NOTE_LEVEL)

    def sounding_roots(self, harmony: Harmony) -> dict[str, float]:
        """Fire each pitched patch's sequencer at its first note in the
        clock's current bar, and return the pitch it played, divided by the
        interval its pattern puts on that note - i.e. the chord root it used.

        Each patch's step is derived live from `clock.tick` (see
        `GatedVoice.step_pattern`), not from a counter that advances once per
        call - so a step is fired by moving the clock to that step's tick and
        calling the voice's own division callback once (its `sequencer` may also hold a gate), rather than calling it
        repeatedly with the clock held still."""
        context = BuildContext(self.tempo, self.clock, harmony)
        seed = Progressions.DEEP_HOUSE_MINOR
        chord_patch = stab.StabVelvet(progression=seed).build(context)
        bass_patch = bass.BassRolling(progression=seed).build(context)
        tom_patch = tom.Tom(progression=seed).build(context)
        bar_start = self.clock._tick

        def fire(patch: Patch, step_index: int) -> None:
            self.clock._tick = bar_start + step_index * patch._division.steps
            patch._division.callback()

        # the chord stabs on the third 16th, the bass on the first, the tom's
        # first fill note (a fifth up) on the eleventh
        fire(chord_patch, 2)
        fire(bass_patch, 0)
        fire(tom_patch, 10)
        self.clock._tick = bar_start
        chord_osc = next(r for r in chord_patch.resources if type(r).__name__ == "Osc")
        tom_tuning = next(r for r in tom_patch.resources if type(r).__name__ == "Sig")
        fifth = 2 ** (7 / 12)
        return {
            "chord": chord_osc.freq,
            "bass": bass_patch.pitch.value,
            "tom": tom_tuning.value * tom.Tom.body_freq / fifth,
        }

    def assert_same_pitch_class(self, roots: dict[str, float], expected: int) -> None:
        for name, frequency in roots.items():
            with self.subTest(part=name):
                pitch_class = round(69 + 12 * math.log2(frequency / 440)) % 12
                self.assertEqual(pitch_class, expected)

    def test_bass_chord_and_tom_change_chord_on_the_same_bar(self) -> None:
        harmony = Harmony(key=Note.KEY_A)
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
        harmony = Harmony(key=Note.KEY_A)
        saved_tick = self.clock._tick
        try:
            self.clock._tick = 0
            harmony.key = 0  # C
            self.assert_same_pitch_class(self.sounding_roots(harmony), 0)
        finally:
            self.clock._tick = saved_tick


if __name__ == "__main__":
    unittest.main()
