"""Sweep contract: a `sweep=True` `Param` gets a per-patch `Sweep` that keeps
the user's resting value, clamps its range to the slider, is declared from a
rack `Slot`, survives style overrides, and round-trips through a preset. No
pyo server boots here; the running LFO is checked by hand, see tests/AGENTS.md."""

import unittest
from unittest.mock import MagicMock

from pyoscillate.controller import Slot
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.params import Param
from pyoscillate.patches.sweep import ParamSweep, Sweep
from pyoscillate.patches.tonal.lead import fm
from pyoscillate.projects.forest_psytrance.rack import ForestPsytranceRack
from src.flet.base import PatchPanel


class _Voice(Patch):
    name = "sweep_voice"
    title = "Sweep voice"
    summary = "Test voice."

    seen: float = 0.0

    @Param(0.0, 10.0, 0.5, 2.0, "Amount", "Test.", sweep=True)
    def amount(self, value: float) -> None:
        self.seen = value

    fixed = Param(0.0, 1.0, 0.1, 0.5, "Fixed", "Test.")

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self._built = True
        return self


class _Styled(_Voice):
    amount = _Voice.amount.replace(default=4.0)


class SweepTests(unittest.TestCase):
    def test_only_flagged_params_get_a_sweep(self):
        voice = _Voice()
        self.assertEqual([p.name for p in voice.sweeps], ["amount"])

    def test_replace_keeps_the_flag_and_sweep_for_matches_the_origin(self):
        styled = _Styled()
        self.assertTrue(_Styled.amount.sweep)
        self.assertIs(styled.sweep_for(_Voice.amount), styled.sweeps[_Styled.amount])

    def test_a_param_without_a_sweep_has_none(self):
        with self.assertRaises(LookupError):
            _Voice().sweep_for(_Voice.fixed)

    def test_a_sweep_starts_off_and_pinned_at_the_default(self):
        sweep = _Voice().sweeps[_Voice.amount]
        self.assertFalse(sweep.enabled)
        self.assertEqual((sweep.low, sweep.high), (2.0, 2.0))

    def test_range_is_clamped_and_ordered(self):
        sweep = _Voice().sweeps[_Voice.amount]
        sweep.configure(12, -3, 500)
        self.assertEqual((sweep.low, sweep.high), (0.0, 10.0))
        self.assertEqual(sweep.bars, Sweep.MAX_BARS)
        sweep.configure(7, 3, 0)
        self.assertEqual((sweep.low, sweep.high), (3.0, 7.0))
        self.assertEqual(sweep.bars, Sweep.MIN_BARS)

    def test_value_at_maps_position_onto_the_range(self):
        sweep = _Voice().sweeps[_Voice.amount]
        sweep.configure(2, 6, 4)
        self.assertEqual([sweep.value_at(p) for p in (0, 0.5, 1)], [2.0, 4.0, 6.0])

    def test_a_slot_declares_the_sweep_enabled(self):
        voice = Slot(_Voice, sweeps=(ParamSweep(_Voice.amount, 1, 3, 2),)).bind()
        sweep = voice.sweeps[_Voice.amount]
        self.assertTrue(sweep.enabled)
        self.assertEqual((sweep.low, sweep.high, sweep.bars), (1.0, 3.0, 2.0))
        self.assertEqual(voice.amount, 2.0)

    def test_disabling_hands_back_the_resting_value(self):
        voice = _Voice(amount=3.0).build(MagicMock())
        sweep = voice.sweeps[_Voice.amount]
        sweep.set_enabled(True)
        voice.seen = 9.0
        sweep.set_enabled(False)
        self.assertEqual(voice.seen, 3.0)
        self.assertEqual(voice.amount, 3.0)

    def test_nothing_runs_without_a_tempo(self):
        voice = _Voice().build(MagicMock())
        sweep = voice.sweeps[_Voice.amount]
        sweep.set_enabled(True)
        sweep.run()
        self.assertFalse(sweep.running)

    def test_every_lead_param_but_register_and_rate_sweeps(self):
        for lead in (fm.LeadFmWind, fm.LeadFmSwirl):
            with self.subTest(lead=lead.name):
                swept = {p.name for p in lead.params if p.sweep}
                self.assertEqual(
                    swept,
                    {
                        "bite",
                        "settle",
                        "swirl",
                        "breath",
                        "glide",
                        "length",
                        "echo_level",
                    },
                )

    def test_forest_leads_start_with_every_sweep_off(self):
        rack = ForestPsytranceRack()
        for lead in (rack.lead_wind, rack.lead_swirl):
            self.assertFalse(any(s.enabled for s in lead.sweeps.values()))


class SweepPresetTests(unittest.TestCase):
    def test_settings_round_trip_through_a_preset(self):
        source = PatchPanel(_Voice())
        sweep = source.patch.sweeps[_Voice.amount]
        sweep.configure(1, 5, 12)
        sweep.set_enabled(True)
        saved = source.to_preset()

        target = PatchPanel(_Voice())
        target.apply_preset(saved)
        restored = target.patch.sweeps[_Voice.amount]
        self.assertTrue(restored.enabled)
        self.assertEqual((restored.low, restored.high, restored.bars), (1.0, 5.0, 12.0))

    def test_a_patch_without_sweeps_saves_no_sweep_entry(self):
        class Plain(Patch):
            name = "plain"
            title = "Plain"
            summary = ""

            def build(self, context: BuildContext) -> Patch:
                return self

        self.assertNotIn("sweeps", PatchPanel(Plain()).to_preset())

    def test_a_sweepable_param_gets_a_sweep_row(self):
        panel = PatchPanel(_Voice())
        self.assertEqual(list(panel.sweep_rows), [_Voice.amount])


if __name__ == "__main__":
    unittest.main()
