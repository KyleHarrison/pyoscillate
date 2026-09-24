"""Health contract shared by every gated patch: no sound without a tick.

Findings
========

1. Every Trig-driven patch sounds once at start-up
--------------------------------------------------
Error:
    Each patch below was built and started with its clock never running,
    and each still made sound. Peaks included chord 0.178 (almost at the
    0.18 output ceiling), kick 0.108, bass 0.067, cymbal 0.047 and clap
    0.043. With no ticks, the correct output is silence.
Cause:
    pyo's `Trig()` emits one trigger the first time it is computed, whether
    or not `play()` has been called. Each patch builds a bare `Trig()` and
    relies on its sequencer calling `play()`, so each fires once as soon as
    it starts.
Change:
    Construct the trigger as `Trig().stop()` in every Trig-driven patch.
    Verified offline: a stopped `Trig` is silent until `play()`, which still
    fires at full level. texture/atmosphere gets the same change, but it
    is not tested here (see GATED_PATCHES).
Status:
    fix pending - test_started_patch_is_silent_until_its_clock_ticks fails
    for all 12 patches until then.
"""

import unittest

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import render

# module -> build params needed to construct it. texture/atmosphere is left
# out on purpose: its envelope and FM voice carry `add` offsets, so it is
# never silent by design and has no "unscheduled" output to test for.
GATED_PATCHES = {
    "pyoscillate.patches.drums.clap.clap": {},
    "pyoscillate.patches.drums.cymbal.cymbal": {"style": "ride"},
    "pyoscillate.patches.drums.hat": {},
    "pyoscillate.patches.drums.hat.groove": {"style": "crisp"},
    "pyoscillate.patches.drums.kick.kick": {"style": "round"},
    "pyoscillate.patches.drums.low_hat": {},
    "pyoscillate.patches.drums.percussion.percussion": {"style": "rim"},
    "pyoscillate.patches.drums.snare.snare": {},
    "pyoscillate.patches.drums.tom.tom": {},
    "pyoscillate.patches.musical.chord.chord": {"style": "velvet"},
    "pyoscillate.patches.tonal.bass": {},
    "pyoscillate.patches.tonal.bass.groove": {"style": "rolling"},
    "pyoscillate.patches.transition.riser.riser": {"style": "noise"},
}
# -80 dBFS: comfortably above numerical noise, far below anything audible
SILENT_PEAK = 1e-4


class GatedPatchSilenceTests(unittest.TestCase):
    def test_started_patch_is_silent_until_its_clock_ticks(self) -> None:
        for module, params in GATED_PATCHES.items():
            with self.subTest(module=module):
                result = features(
                    render(module, params, seconds=0.5, clock_running=False)
                )

                self.assertLess(result.peak, SILENT_PEAK)


if __name__ == "__main__":
    unittest.main()
