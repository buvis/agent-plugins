import unittest

from src.cart import total


class TotalTest(unittest.TestCase):
    def test_sum(self) -> None:
        self.assertEqual(total([1.0, 2.0]), 3.0)

    def test_round(self) -> None:
        self.assertEqual(total([0.1, 0.2]), 0.3)
