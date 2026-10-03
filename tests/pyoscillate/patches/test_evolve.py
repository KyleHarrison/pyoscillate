"""`Evolution`: a patch's own timer rotates its ticked phrases on bar lines,
and its progress and settings are readable for the UI."""

import unittest

from pyoscillate.clock import Division
from pyoscillate.patches.drums.kick.kick import Kick, KickLofi
from pyoscillate.patches.evolve import Evolution, Evolve
from pyoscillate.patches.tonal.drone.wash import SoundscapeWash
from pyoscillate.theory.phrase import Rhythms


class StubClock:
    """A `Clock` without the pyo `Pattern`, advanced by hand."""

    def __init__(self) -> None:
        self.bar = 32
        self.tick = 0
        self.divisions: list[Division] = []

    def subscribe(self, steps, callback) -> Division:
        return Division(clock=self, steps=steps, callback=callback)  # type: ignore[arg-type]

    def _register(self, division: Division) -> None:
        self.divisions.append(division)

    def _unregister(self, division: Division) -> None:
        self.divisions.remove(division)

    def advance(self, ticks: int) -> None:
        for _ in range(ticks):
            for division in list(self.divisions):
                if self.tick % division.steps == 0:
                    division.callback()
            self.tick += 1


class EvolutionSettingsTests(unittest.TestCase):
    def test_only_the_starting_phrase_is_ticked_and_it_starts_off(self) -> None:
        kick = KickLofi()

        self.assertFalse(kick.evolution.enabled)
        self.assertEqual(kick.evolution.choices, (Rhythms.KICK_LOFI,))

    def test_a_rack_declaration_switches_it_on_with_its_choices(self) -> None:
        kick = KickLofi()

        kick.declare_evolution(Evolve(4, (Rhythms.KICK_LOFI_FULL, Rhythms.KICK_LOFI)))

        self.assertTrue(kick.evolution.enabled)
        self.assertEqual(kick.evolution.bars, 4)
        # kept in the dropdown's order, whatever order the rack listed them
        self.assertEqual(
            kick.evolution.choices, (Rhythms.KICK_LOFI, Rhythms.KICK_LOFI_FULL)
        )

    def test_bars_are_kept_inside_their_range(self) -> None:
        evolution = KickLofi().evolution

        evolution.configure(0)
        self.assertEqual(evolution.bars, Evolution.MIN_BARS)
        evolution.configure(1000)
        self.assertEqual(evolution.bars, Evolution.MAX_BARS)

    def test_ticking_a_choice_keeps_catalog_order(self) -> None:
        kick = KickLofi()

        kick.evolution.set_choice(Rhythms.KICK_LOFI_FULL, True)
        self.assertEqual(
            kick.evolution.choices, (Rhythms.KICK_LOFI, Rhythms.KICK_LOFI_FULL)
        )
        kick.evolution.set_choice(Rhythms.KICK_LOFI, False)
        self.assertEqual(kick.evolution.choices, (Rhythms.KICK_LOFI_FULL,))

    def test_a_patch_with_nothing_to_change_is_not_evolvable(self) -> None:
        self.assertTrue(KickLofi().evolvable)
        self.assertTrue(SoundscapeWash().evolvable)


class PhraseRotationTests(unittest.TestCase):
    def kick(self) -> KickLofi:
        kick = KickLofi()
        kick.evolution.set_choice(Rhythms.KICK_LOFI_FULL, True)
        return kick

    def test_each_fire_moves_to_the_next_ticked_phrase_and_wraps(self) -> None:
        kick = self.kick()

        kick.on_evolve(0)
        self.assertIs(kick.selected_phrase, Rhythms.KICK_LOFI_FULL)
        kick.on_evolve(1)
        self.assertIs(kick.selected_phrase, Rhythms.KICK_LOFI)

    def test_one_ticked_phrase_leaves_the_dropdown_alone(self) -> None:
        kick = KickLofi()

        kick.on_evolve(0)

        self.assertIs(kick.selected_phrase, Rhythms.KICK_LOFI)

    def test_a_phrase_picked_by_hand_continues_from_there(self) -> None:
        kick = self.kick()
        kick.evolution.set_choice(Rhythms.QUARTER_PULSE, True)
        kick.phrase = Rhythms.KICK_LOFI_FULL

        kick.on_evolve(0)

        # the next ticked phrase after the one picked, not after the first
        self.assertIsNot(kick.selected_phrase, Rhythms.KICK_LOFI_FULL)

    def test_a_phrase_that_is_not_ticked_enters_the_rotation_at_its_start(self) -> None:
        kick = self.kick()
        kick.phrase = Rhythms.QUARTER_PULSE

        kick.on_evolve(0)

        self.assertIs(kick.selected_phrase, kick.evolution.choices[0])


class EvolutionTimerTests(unittest.TestCase):
    def clock(self) -> StubClock:
        return StubClock()

    def test_it_only_runs_when_enabled_and_started_on_a_clock(self) -> None:
        kick = KickLofi()
        clock = self.clock()

        kick.evolution.run(clock)  # type: ignore[arg-type]
        self.assertFalse(kick.evolution.running)
        kick.evolution.enabled = True
        clockless = KickLofi()
        clockless.evolution.enabled = True
        clockless.evolution.run(None)
        self.assertFalse(clockless.evolution.running)
        kick.evolution.run(clock)  # type: ignore[arg-type]
        self.assertTrue(kick.evolution.running)
        kick.evolution.halt()
        self.assertFalse(kick.evolution.running)

    def test_it_fires_on_bar_lines_every_n_bars(self) -> None:
        kick = KickLofi()
        fired: list[int] = []
        kick.on_evolve = fired.append  # type: ignore[method-assign]
        clock = self.clock()
        kick.declare_evolution(Evolve(2))
        kick.evolution.run(clock)  # type: ignore[arg-type]

        clock.advance(clock.bar * 5)

        # ticks 0, 64 and 128 are multiples of two bars
        self.assertEqual(fired, [0, 1, 2])

    def test_progress_fills_between_changes(self) -> None:
        kick = KickLofi()
        clock = self.clock()
        kick.declare_evolution(Evolve(4))
        kick.evolution.run(clock)  # type: ignore[arg-type]

        self.assertEqual(kick.evolution.progress, 0)
        clock.tick = clock.bar * 3
        self.assertAlmostEqual(kick.evolution.progress, 0.75)
        self.assertAlmostEqual(kick.evolution.bars_left, 1.0)

    def test_changing_bars_retunes_a_running_timer(self) -> None:
        kick = KickLofi()
        clock = self.clock()
        kick.declare_evolution(Evolve(4))
        kick.evolution.run(clock)  # type: ignore[arg-type]

        kick.evolution.configure(2)

        self.assertEqual(kick.evolution._division.steps, clock.bar * 2)

    def test_progress_is_zero_when_not_running(self) -> None:
        self.assertEqual(KickLofi().evolution.progress, 0.0)
        self.assertEqual(Kick().evolution.bars_left, Evolution.DEFAULT_BARS)


if __name__ == "__main__":
    unittest.main()
