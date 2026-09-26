"""Rack-level sync contract: patches sharing the rack's `Clock` must fire
their bar-boundary events on the exact same tick, whatever tick the clock
happened to be on when they were built - not from each patch's own idea of
where a bar starts. See `pyoscillate.harmony.Harmony`'s docstring: "never
from a patch's own step counter... the clock's bar count is the same for
everyone."

This runs Keys and Strings together on one shared `Clock`, seeded with a
non-bar-aligned pre-roll (the clock is advanced a few 16th notes before
either patch is built) to reproduce a patch switched on mid-song rather
than at the top of a bar - the situation the Flet UI's per-patch toggle
actually creates. It drives the clock directly (`Clock._advance()`) instead
of the real-time `Pattern`, since only the scheduling decision is under
test, not the audio.

Findings
========

1. Keys drifted out of phase with the rest of the rack
-------------------------------------------------------
Error:
    With a 5-sixteenth pre-roll, Keys' first Charleston "hard" hit (and its
    chord choice) fired on the very next clock tick after it was built -
    5 sixteenths off the true bar boundary - while Strings, built on the
    same clock, only re-triggers on the real bar boundary.
Cause:
    `Keys.build()` seeded a private `self._step = 0` / `self._slot = 0` at
    build time and incremented them locally on every callback, instead of
    reading the shared clock's own tick/bar position the way Strings reads
    `clock.bar_index` and every `needs_harmony` voice does. A patch's own
    step count depends on when it was built, so it starts counting from
    whatever moment that was rather than from the rack's actual downbeat.
Change:
    `Keys.build()`'s `next_step()` now derives its step-within-bar from
    `clock.tick // self._division.steps` and its chord/slot from
    `clock.bar_index`, both public and identical for every patch on the
    clock. Added `Clock.tick` (a public accessor for the previously private
    `_tick`) to support this.
Status:
    fixed - src/pyoscillate/patches/tonal/keys/keys.py,
    src/pyoscillate/clock.py.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# a non-bar-aligned pre-roll: if a patch counts its own steps from build
# time instead of the clock's tick, its first hit will land 5 sixteenths
# off the true bar boundary rather than on it
PRE_ROLL_SIXTEENTHS = 5
BARS_TO_RUN = 6

_SCRIPT = """
import json
import sys

from pyo.lib.server import Server

from pyoscillate.clock import Clock
from pyoscillate.patches.tonal.keys import keys
from pyoscillate.patches.tonal.strings import strings
from pyoscillate.projects.lofi import rack
from pyoscillate.tempo import Tempo

output_path, pre_roll_sixteenths, bars_to_run = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

server = Server(sr=44100, nchnls=2, duplex=0, audio="offline")
server.setGlobalSeed(1)
server.boot()

tempo = Tempo(bpm=rack.BPM)
clock = Clock(tempo, ticks_per_bar=rack.TICKS_PER_BAR)

# simulate the rack's clock already having been running a while, off the
# bar boundary, before these two patches are switched on together
for _ in range(pre_roll_sixteenths * clock.sixteenth):
    clock._advance()

keys_patch = keys.Keys()
keys_patch.build(tempo, clock)
keys_patch.start()

strings_patch = strings.Strings()
strings_patch.build(tempo, clock, harmony=rack.HARMONY)
strings_patch.start()

# a slot is reused every SLOTS hits (see keys.py), so a hard hit can reassign
# a slot that was already at velocity 1.0 from an earlier bar - watching for
# a change in `velocities` would miss that repeat. Wrapping each trigger's
# own `play()` instead catches every hit, hard or soft, regardless of slot reuse.
hit_events = []
for slot, trigger in enumerate(keys_patch.triggers):
    def _wrap(slot=slot, play=trigger.play):
        def wrapper(*args, **kwargs):
            hit_events.append((clock.tick, keys_patch.velocities[slot]))
            return play(*args, **kwargs)

        return wrapper

    trigger.play = _wrap()

chord_change_ticks = []

for _ in range(bars_to_run * clock.bar):
    tick = clock.tick
    before_root = strings_patch.chord_saws[0].freq
    clock._advance()
    if strings_patch.chord_saws[0].freq != before_root:
        chord_change_ticks.append(tick)

hard_hit_ticks = sorted(tick for tick, velocity in hit_events if velocity == 1.0)

keys_patch.stop()
strings_patch.stop()
server.shutdown()

with open(output_path, "w") as f:
    json.dump(
        {
            "bar_ticks": clock.bar,
            "hard_hit_ticks": hard_hit_ticks,
            "chord_change_ticks": chord_change_ticks,
        },
        f,
    )
"""


def _run() -> dict:
    with tempfile.TemporaryDirectory() as directory:
        output_path = Path(directory) / "result.json"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                _SCRIPT,
                str(output_path),
                str(PRE_ROLL_SIXTEENTHS),
                str(BARS_TO_RUN),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"rack sync probe failed:\n{result.stderr}")
        return json.loads(output_path.read_text())


class LofiRackSyncTests(unittest.TestCase):
    def test_keys_hard_hits_land_on_the_real_bar_boundary(self) -> None:
        """Keys' downbeat must fire on a multiple of the clock's own bar
        length, not on whatever tick it happened to be built on."""
        data = _run()

        self.assertEqual(len(data["hard_hit_ticks"]), BARS_TO_RUN)
        for tick in data["hard_hit_ticks"]:
            self.assertEqual(tick % data["bar_ticks"], 0)

    def test_keys_and_strings_change_together(self) -> None:
        """Keys' downbeat and Strings' once-per-bar re-articulation, built
        on the same clock, must fire on the exact same ticks."""
        data = _run()

        self.assertEqual(data["hard_hit_ticks"], data["chord_change_ticks"])


if __name__ == "__main__":
    unittest.main()
