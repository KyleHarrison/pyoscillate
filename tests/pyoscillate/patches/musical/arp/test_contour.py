import unittest

from pyoscillate.intervals import ArpOrder, Scale


class ArpOrderTests(unittest.TestCase):
    def test_arch_reproduces_the_original_pentatonic_walk(self) -> None:
        self.assertEqual(
            ArpOrder.ARCH.intervals(Scale.MAJOR_PENTATONIC_OCTAVE.value),
            (0, 2, 4, 7, 9, 12, 9, 7, 4, 2),
        )

    def test_index_wraps_around_a_short_pool(self) -> None:
        self.assertEqual(
            ArpOrder.UP_DOWN_FOURS.intervals((0, 4, 7)),
            (0, 4, 7, 0, 0, 7, 4, 0, 0, 4, 7, 0, 0, 7, 4, 0),
        )

    def test_by_index_clamps(self) -> None:
        self.assertIs(ArpOrder.by_index(-3), ArpOrder.ARCH)
        self.assertIs(ArpOrder.by_index(99), ArpOrder.RISE_RESET)

    def test_every_order_stays_inside_the_pool(self) -> None:
        pool = Scale.MAJOR_PENTATONIC_OCTAVE.value
        for order in ArpOrder:
            self.assertTrue(set(order.intervals(pool)) <= set(pool), order)


if __name__ == "__main__":
    unittest.main()
