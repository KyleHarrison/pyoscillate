import unittest

from pyoscillate.theory.phrase import Phrase
from pyoscillate.theory.phrase.arp import ArpOrders
from pyoscillate.theory.scale import Scales


class ArpOrderTests(unittest.TestCase):
    @staticmethod
    def sequence(order: Phrase, pool: tuple[int, ...]) -> tuple[int, ...]:
        """The pool note at each step of `order`, in step order."""
        return tuple(order.resolve(pool).values())

    def test_arch_reproduces_the_original_pentatonic_walk(self) -> None:
        self.assertEqual(
            self.sequence(ArpOrders.ARCH, Scales.MAJOR_PENTATONIC_OCTAVE.offsets),
            (0, 2, 4, 7, 9, 12, 9, 7, 4, 2),
        )

    def test_index_wraps_around_a_short_pool(self) -> None:
        self.assertEqual(
            self.sequence(ArpOrders.UP_DOWN_FOURS, (0, 4, 7)),
            (0, 4, 7, 0, 0, 7, 4, 0, 0, 4, 7, 0, 0, 7, 4, 0),
        )

    def test_by_index_clamps(self) -> None:
        self.assertIs(ArpOrders.by_index(-3), ArpOrders.ARCH)
        self.assertIs(ArpOrders.by_index(99), ArpOrders.RISE_RESET)

    def test_every_order_stays_inside_the_pool(self) -> None:
        pool = Scales.MAJOR_PENTATONIC_OCTAVE.offsets
        for order in ArpOrders.members():
            self.assertTrue(set(self.sequence(order, pool)) <= set(pool), order)


if __name__ == "__main__":
    unittest.main()
