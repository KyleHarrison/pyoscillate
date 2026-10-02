import unittest

from pyoscillate.projects.psyambient.rack import PsyambientRack


class PsyambientRackTests(unittest.TestCase):
    def test_atmosphere_nests_the_three_layers(self) -> None:
        rack = PsyambientRack()

        (atmosphere,) = rack.groups
        self.assertEqual(
            [group.title for group in atmosphere.children],
            ["Soundscapes", "Mid Voices", "Bass"],
        )

    def test_soundscapes_evolve_on_their_own_timer(self) -> None:
        rack = PsyambientRack()

        self.assertEqual(
            [group.title for group in rack.evolving_groups], ["Soundscapes"]
        )

    def test_intensity_moves_every_layer(self) -> None:
        rack = PsyambientRack()

        rack.atmosphere_group.apply(PsyambientRack.atmosphere_intensity, 1.0)

        self.assertAlmostEqual(rack.soundscape_fm.chaos_speed, 0.2)
        self.assertAlmostEqual(rack.mid_canon.fm_index, 4.0)
        self.assertAlmostEqual(rack.bass_drone.filter_base, 400)


if __name__ == "__main__":
    unittest.main()
