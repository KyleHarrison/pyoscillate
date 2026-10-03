"""Gate contract: the `Gate` add-on chops a voice into clocked pulses, leaves
it untouched at depth 0, and works on both a gated and an ungated voice base.

Gated renders use the real server in a subprocess (see tests/AGENTS.md); the
pulse pattern itself is checked without one."""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.common import ContinuousVoice, Gate
from pyoscillate.patches.texture.noise.noise import NoiseAir, NoiseDust
from pyoscillate.patches.tonal.drone import Drone
from pyoscillate.patches.tonal.drone.wash import SoundscapeWash
from pyoscillate.patches.tonal.strings.strings import Strings

STRINGS = "pyoscillate.patches.tonal.strings.strings"
WASH = "pyoscillate.patches.tonal.drone.wash"
NOISE = "pyoscillate.patches.texture.noise.noise"
# every module that takes the gate, with the style that selects its patch ("" if none)
ROLLOUT = (
    ("pyoscillate.patches.tonal.drone", ""),
    ("pyoscillate.patches.tonal.drone.filter", ""),
    ("pyoscillate.patches.tonal.drone.fm", ""),
    ("pyoscillate.patches.tonal.drone.sub_chaos", ""),
    ("pyoscillate.patches.tonal.drone.sub_swell", ""),
    (NOISE, "air"),
    (NOISE, "surf"),
    (NOISE, "barber"),
)


@cache
def _render(module: str, gate: float, density: float = 1.0, style: str = "") -> Render:
    params: dict[str, float | str] = {"gate": gate, "gate_density": density}
    if style:
        params["style"] = style
    return render(module, params, seconds=4.0)


def _envelope(result: Render) -> np.ndarray:
    """Mean absolute level per 10 ms, after the first second of fade-in."""
    samples = np.abs(result.samples[result.sample_rate :])
    window = result.sample_rate // 100
    usable = samples[: samples.size // window * window]
    return usable.reshape(-1, window).mean(axis=1)


class GatePatternTests(unittest.TestCase):
    def test_full_density_plays_every_step(self) -> None:
        patch = Strings(gate_density=1.0)
        self.assertTrue(all(patch.gate_hit(i) for i in range(Gate.GATE_STEPS)))

    def test_zero_density_plays_no_step(self) -> None:
        patch = Strings(gate_density=0.0)
        self.assertFalse(any(patch.gate_hit(i) for i in range(Gate.GATE_STEPS)))

    def test_a_pattern_repeats_and_differs_by_seed(self) -> None:
        first = Strings(gate_density=0.5, gate_seed=3)
        again = Strings(gate_density=0.5, gate_seed=3)
        other = Strings(gate_density=0.5, gate_seed=4)
        steps = range(Gate.GATE_STEPS)
        self.assertEqual(
            [first.gate_hit(i) for i in steps], [again.gate_hit(i) for i in steps]
        )
        self.assertNotEqual(
            [first.gate_hit(i) for i in steps], [other.gate_hit(i) for i in steps]
        )

    def test_the_gate_is_off_by_default(self) -> None:
        for patch_class in (Strings, SoundscapeWash):
            with self.subTest(patch=patch_class.__name__):
                self.assertEqual(patch_class().gate, 0.0)

    def test_a_voice_that_skips_add_gate_fails_to_finish(self) -> None:
        class Forgetful(Gate, ContinuousVoice):
            def build(self, context):  # type: ignore[no-untyped-def]
                self._reset()
                return self.finish(None)  # type: ignore[arg-type]

        with self.assertRaises(RuntimeError):
            Forgetful().build(None)  # type: ignore[arg-type]


class GateSoundTests(unittest.TestCase):
    def test_depth_zero_never_goes_silent(self) -> None:
        for module in (STRINGS, WASH):
            with self.subTest(module=module):
                self.assertGreater(_envelope(_render(module, 0.0)).min(), 0.0)

    def test_full_depth_is_silent_between_pulses_and_audible_in_them(self) -> None:
        for module in (STRINGS, WASH):
            with self.subTest(module=module):
                level = _envelope(_render(module, 1.0))
                self.assertEqual(level.min(), 0.0)
                self.assertGreater(level.max(), 0.0)

    def test_lower_density_leaves_more_silence(self) -> None:
        for module in (STRINGS, WASH):
            with self.subTest(module=module):
                full = _envelope(_render(module, 1.0, 1.0))
                sparse = _envelope(_render(module, 1.0, 0.4))
                self.assertGreater((sparse == 0).mean(), (full == 0).mean())

    def test_every_rolled_out_patch_chops_at_full_depth_only(self) -> None:
        for module, style in ROLLOUT:
            with self.subTest(module=module, style=style):
                smooth = _envelope(_render(module, 0.0, style=style))
                chopped = _envelope(_render(module, 1.0, style=style))
                self.assertGreater(smooth.min(), 0.0)
                self.assertEqual(chopped.min(), 0.0)
                self.assertGreater(chopped.max(), 0.0)


class RemainingGateTests(unittest.TestCase):
    """The rest of the gated and continuous voices take the gate the same way."""

    VOICES = (
        ("pyoscillate.patches.tonal.lead.lead", "brass"),
        ("pyoscillate.patches.tonal.lead.fm", "wind"),
        ("pyoscillate.patches.tonal.pluck.pluck", ""),
        ("pyoscillate.patches.tonal.keys.keys", ""),
        ("pyoscillate.patches.musical.stab.stab", "velvet"),
        ("pyoscillate.patches.musical.arp.arp", ""),
        ("pyoscillate.patches.texture.rumble.rumble", ""),
        ("pyoscillate.patches.texture.atmosphere", ""),
    )

    def test_every_voice_chops_more_at_full_depth(self) -> None:
        for module, style in self.VOICES:
            with self.subTest(module=module, style=style):
                smooth = _envelope(_render(module, 0.0, style=style))
                chopped = _envelope(_render(module, 1.0, style=style))
                self.assertGreater(chopped.max(), 0.0)
                self.assertGreater((chopped == 0).mean(), (smooth == 0).mean())


class GateScopeTests(unittest.TestCase):
    def test_dust_keeps_its_own_discrete_clicks_and_takes_no_gate(self) -> None:
        self.assertFalse(issubclass(NoiseDust, Gate))
        self.assertTrue(issubclass(NoiseAir, Gate))

    def test_a_drone_with_its_own_bar_division_still_gates(self) -> None:
        # the drone's note-step division and the gate's both end up in the
        # patch's sequencer group
        self.assertTrue(issubclass(Drone, Gate))


if __name__ == "__main__":
    unittest.main()
