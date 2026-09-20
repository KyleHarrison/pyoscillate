import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from pyoscillate.clock import Clock
from pyoscillate.patches import Patch, PatchRack, start_server
from pyoscillate.projects.deep_house.rack import PATCH_DEFS
from pyoscillate.tempo import Tempo


class ServerStartupTests(unittest.TestCase):
    @patch("pyoscillate.patches.base.Server")
    def test_silent_boot_failure_raises_before_start(self, server_type: MagicMock) -> None:
        server = server_type.return_value
        server.getIsBooted.return_value = False
        server.getIsStarted.return_value = False

        with self.assertRaisesRegex(RuntimeError, "could not boot"):
            start_server(output_device=99)

        server.start.assert_not_called()


class KickNativeCrashTests(unittest.TestCase):
    def test_two_kicks_survive_live_updates(self) -> None:
        code = """
from pyoscillate.clock import Clock
from pyoscillate.patches import PatchRack, start_server
from pyoscillate.patches.deep_house import kick
from pyoscillate.tempo import Tempo

server = start_server(audio="manual")
tempo = Tempo(bpm=122)
clock = Clock(tempo)
clock.start()
rack = PatchRack()
rack.start("kick_round", kick.build(tempo, clock, "round"))
punch = rack.start("kick_punch", kick.build(tempo, clock, "punch"))
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
        cls.tempo = Tempo(bpm=122)
        cls.clock = Clock(cls.tempo)
        cls.clock.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.clock.stop()
        cls.server.stop()
        cls.server.shutdown()

    def assert_patch_lifecycle(self, patch_def) -> None:
        rack = PatchRack()
        values = {spec.name: spec.default for spec in patch_def.parameters}
        build_kwargs = dict(values)
        if patch_def.needs_tempo:
            build_kwargs["tempo"] = self.tempo
        if patch_def.needs_clock:
            build_kwargs["clock"] = self.clock

        patch = patch_def.build(**build_kwargs)
        self.assertIsInstance(patch, Patch)
        rack.start(patch_def.name, patch)
        patch.update(values)
        rack.stop(patch_def.name)


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
