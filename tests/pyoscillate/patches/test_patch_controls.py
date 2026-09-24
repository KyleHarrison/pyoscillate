"""Runtime contract shared by the patches ported from the pyo examples
(docs/todos/pyo-examples.md): every slider has a live control, and moving
each one to both ends of its range while audio runs never raises or crashes.

The run happens in a subprocess on a `manual` server, because pyo keeps one
native server per process and a native crash would take pytest down with it.
"""

import json
import subprocess
import sys
import unittest

# module -> build params needed to construct it (profile names and so on)
PATCHES: dict[str, list[dict]] = {
    "pyoscillate.patches.texture.noise.noise": [
        {"style": "air"},
        {"style": "surf"},
        {"style": "barber"},
    ],
    "pyoscillate.patches.transition.riser.riser": [
        {"style": "noise"},
        {"style": "shift"},
        {"style": "pitch"},
    ],
}

SCRIPT = """
import importlib, inspect, json, sys
from pyoscillate.clock import Clock
from pyoscillate.patches import PatchRack, start_server
from pyoscillate.tempo import Tempo

cases = json.loads(sys.argv[1])
server = start_server(audio="manual")
tempo = Tempo(bpm=124)
clock = Clock(tempo)
clock.start()
rack = PatchRack()
problems = []
for module_name, params in cases:
    module = importlib.import_module(module_name)
    accepted = inspect.signature(module.build).parameters
    context = {name: value for name, value in {"tempo": tempo, "clock": clock}.items()
               if name in accepted}
    patch = rack.start(module_name, module.build(**context, **params))
    names = [spec.name for spec in module.PARAMETERS]
    missing = sorted(set(names) - set(patch.controls))
    if missing:
        problems.append(f"{module_name} {params}: no live control for {missing}")
    if not patch.resources:
        problems.append(f"{module_name} {params}: empty resources")
    for spec in module.PARAMETERS:
        for value in (spec.minimum, spec.maximum, spec.default):
            patch.set(spec.name, value)
            for _ in range(20):
                server.process()
    rack.stop(module_name)
    for _ in range(40):
        server.process()
clock.stop()
server.stop()
server.shutdown()
print(json.dumps(problems))
"""


class PatchControlTests(unittest.TestCase):
    def test_every_slider_is_live_across_its_range(self) -> None:
        cases = [
            [module, params] for module, variants in PATCHES.items() for params in variants
        ]
        result = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-c", SCRIPT, json.dumps(cases)],
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout.strip().splitlines()[-1]), [])


if __name__ == "__main__":
    unittest.main()
