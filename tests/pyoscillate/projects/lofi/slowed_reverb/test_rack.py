import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from pyoscillate.patches.drums.hat.groove import CLOSED, GrooveLofi
from pyoscillate.patches.drums.kick.kick import KickLofi
from pyoscillate.patches.tonal.drone.wash import SoundscapeWash
from pyoscillate.projects.lofi.slowed_reverb.rack import SlowedReverbRack


class SlowedReverbRackDefaultsTests(unittest.TestCase):
    def test_finished_preset_matches_the_rack_starting_values(self) -> None:
        rack = SlowedReverbRack()
        patches = {patch.name: patch for group in rack.groups for patch in group.patches}
        preset_path = (
            Path(__file__).resolve().parents[5] / "src/flet/slowed_reverb/presets/finished.json"
        )
        preset = json.loads(preset_path.read_text())

        for patch_name, values in preset.items():
            if patch_name == "_rack":
                continue
            patch = patches[patch_name]
            for name, value in values.items():
                if name == "enabled" or not hasattr(patch, name):
                    continue
                with self.subTest(patch=patch_name, parameter=name):
                    self.assertAlmostEqual(getattr(patch, name), value)

        self.assertEqual(preset["_rack"]["macro"], rack.macro.slider.default)

    def test_initial_values_match_the_finished_preset(self) -> None:
        patches = {
            patch.name: patch for group in SlowedReverbRack().groups for patch in group.patches
        }

        expected = {
            "strings": {
                "root_freq": 174.61411571650194,
                "brightness": 3900,
                "attack": 2.15,
                "release": 2.9,
                "spread": 0.2,
                "shimmer": 0.8,
                "colour": 0.9,
                "volume": 0.7,
            },
            "keys": {
                "root_freq": 164.81377845643496,
                "bark": 5.0,
                "bite": 0.3,
                "decay": 3.1,
                "tremolo": 0.85,
                "wobble": 0.6,
                "volume": 1.5,
            },
            "bass_hover": {
                "root_freq": 41.20344461410875,
                "cutoff": 770,
                "reverb_size": 0.85,
                "reverb_damp": 0.85,
                "reverb_bal": 0.85,
                "breath": 0.5,
                "rate": -1,
                "volume": 1.6,
            },
            "soundscape_wash": {
                "root_freq": 97.99885899543733,
                "detune": 0.45,
                "detune_bal": 0.1,
                "pitch_drift": 0.8,
                "chorus_depth": 2.1,
                "chorus_feedback": 0.8,
                "chorus_bal": 0.75,
                "reverb_size": 0.25,
                "reverb_damp": 0.15,
                "reverb_bal": 0.75,
                "delay_time": 1.0,
                "delay_feedback": 0.7,
                "volume": 0.5,
            },
            "noise_dust": {
                "colour": 1.7,
                "brightness": 1200,
                "motion": 0.3,
                "depth": 0.75,
                "level": 0.35,
                "volume": 0.3,
            },
            "pluck_hook": {
                "root_freq": 164.81377845643496,
                "brightness": 2.4,
                "decay": 0.45,
                "brightness_decay": 0.2,
                "volume": 0.4,
            },
            "kick_lofi": {
                "level": 0.4,
                "drive": 0.2,
                "punch": 0.8,
                "length": 0.8,
                "click": 0.5,
                "rate": -1,
                "volume": 0.3,
            },
            "hat_lofi": {
                "level": 0.06,
                "cutoff": 3500,
                "metal": 0.1,
                "length": 0.75,
                "rate": -1,
                "volume": 0.12,
            },
        }

        self.assertEqual(set(patches), set(expected))
        for patch_name, values in expected.items():
            patch = patches[patch_name]
            for name, value in values.items():
                with self.subTest(patch=patch_name, parameter=name):
                    self.assertAlmostEqual(getattr(patch, name), value)

    def test_lift_macro_starts_neutral_and_reaches_brighter_values(self) -> None:
        rack = SlowedReverbRack()
        patches = {patch.name: patch for group in rack.groups for patch in group.patches}

        rack.pad.active_patch = patches["soundscape_wash"]
        rack.hook.active_patch = patches["pluck_hook"]
        rack.lead.active_patch = patches["strings"]
        rack.apply_macro(0)
        self.assertEqual(patches["soundscape_wash"].chorus_depth, 2.1)
        self.assertEqual(patches["pluck_hook"].brightness, 2.4)
        self.assertEqual(patches["soundscape_wash"].volume, 0.5)
        self.assertEqual(patches["pluck_hook"].volume, 0.4)

        rack.apply_macro(1)
        self.assertEqual(patches["soundscape_wash"].chorus_depth, 5)
        self.assertEqual(patches["pluck_hook"].brightness, 5)

    def test_section_evolution_is_wired_to_live_pad_and_groove_groups(self) -> None:
        rack = SlowedReverbRack()
        bars = {group.name: group.bars for group in rack.group_controllers}

        self.assertEqual(
            bars,
            {"lead": 8, "pad": 16, "hook": 8, "kick": 8, "hat": 8},
        )

        pad_patch = SoundscapeWash(chorus_depth=2.1, delay_feedback=0.7)
        pad_patch.chorus_depth_sig = SimpleNamespace(value=0.0)
        pad_patch.delay_feedback_sig = SimpleNamespace(value=0.0)
        pad_patch.on_evolve(1)
        self.assertAlmostEqual(pad_patch.chorus_depth_sig.value, 2.52)
        self.assertAlmostEqual(pad_patch.delay_feedback_sig.value, 0.77)

        kick_patch = KickLofi()
        kick_patch._clock = SimpleNamespace(tick=8)
        kick_patch._division = SimpleNamespace(steps=1)
        kick_patch.on_evolve(0)
        self.assertIsNone(kick_patch._step()[1])
        kick_patch.on_evolve(1)
        self.assertEqual(kick_patch._step()[1], 0.45)

        hat_patch = GrooveLofi()
        hat_patch._clock = SimpleNamespace(tick=2)
        hat_patch._division = SimpleNamespace(steps=1)
        hat_patch.on_evolve(0)
        self.assertIsNone(hat_patch._step()[1])
        hat_patch.on_evolve(1)
        self.assertEqual(hat_patch._step()[1], (CLOSED, 0.25))


if __name__ == "__main__":
    unittest.main()
