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
    fixed - `GatedVoice._reset()` constructs a stopped `Trig`, so a gated
    patch stays silent until its scheduled callback calls `play()`.
"""

import unittest

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import render

# module -> build params needed to construct it. texture/atmosphere is left
# out on purpose: its envelope and FM voice carry `add` offsets, so it is
# never silent by design and has no "unscheduled" output to test for.
# A "#label" suffix tests another style of the same module.
GATED_PATCHES = {
    "pyoscillate.patches.drums.clap.clap": {},
    "pyoscillate.patches.drums.cymbal.cymbal": {"style": "ride"},
    "pyoscillate.patches.drums.hat": {},
    "pyoscillate.patches.drums.hat.groove": {"style": "crisp"},
    "pyoscillate.patches.drums.hat.groove#halftime": {"style": "halftime"},
    "pyoscillate.patches.drums.kick.kick": {"style": "round"},
    "pyoscillate.patches.drums.kick.kick#dubstep": {"style": "dubstep"},
    "pyoscillate.patches.drums.low_hat": {},
    "pyoscillate.patches.drums.percussion.percussion": {"style": "rim"},
    "pyoscillate.patches.drums.snare.snare": {"style": "lofi"},
    "pyoscillate.patches.drums.snare.snare#halftime": {"style": "halftime"},
    "pyoscillate.patches.drums.tom.tom": {},
    "pyoscillate.patches.musical.stab.stab": {"style": "velvet"},
    "pyoscillate.patches.pitched_percussion.bell.bell": {"style": "chime"},
    "pyoscillate.patches.pitched_percussion.bell.bell#fm": {"style": "fm"},
    "pyoscillate.patches.tonal.bass": {},
    "pyoscillate.patches.tonal.bass.groove": {"style": "rolling"},
    "pyoscillate.patches.tonal.bass.fm.fm": {"style": "bark"},
    "pyoscillate.patches.tonal.bass.fm.fm#grit": {"style": "grit"},
    "pyoscillate.patches.tonal.bass.funk.funk": {},
    "pyoscillate.patches.tonal.bass.reese.reese": {"style": "wobble"},
    "pyoscillate.patches.tonal.bass.reese.reese#heave": {"style": "heave"},
    "pyoscillate.patches.tonal.keys.accordion": {},
    "pyoscillate.patches.tonal.keys.celeste": {},
    "pyoscillate.patches.tonal.keys.keys": {},
    "pyoscillate.patches.tonal.keys.organ": {},
    "pyoscillate.patches.tonal.keys.string_keys": {"style": "piano"},
    "pyoscillate.patches.tonal.keys.string_keys#harpsichord": {"style": "harpsichord"},
    "pyoscillate.patches.tonal.keys.string_keys#clavichord": {"style": "clavichord"},
    "pyoscillate.patches.tonal.vocal.ensemble": {"style": "choir"},
    "pyoscillate.patches.tonal.vocal.ensemble#angels": {"style": "angels"},
    "pyoscillate.patches.tonal.vocal.solo": {"style": "female"},
    "pyoscillate.patches.tonal.vocal.solo#male": {"style": "male"},
    "pyoscillate.patches.tonal.vocal.whistling": {},
    "pyoscillate.patches.tonal.woodwind.flute.flute": {},
    "pyoscillate.patches.transition.riser.riser": {"style": "noise"},
}
# -80 dBFS: comfortably above numerical noise, far below anything audible
SILENT_PEAK = 1e-4


class GatedPatchSilenceTests(unittest.TestCase):
    def test_started_patch_is_silent_until_its_clock_ticks(self) -> None:
        for name, params in GATED_PATCHES.items():
            with self.subTest(module=name):
                module = name.split("#")[0]
                result = features(
                    render(module, params, seconds=0.5, clock_running=False)
                )

                self.assertLess(result.peak, SILENT_PEAK)


if __name__ == "__main__":
    unittest.main()
