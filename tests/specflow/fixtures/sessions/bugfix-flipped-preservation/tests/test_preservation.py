import unittest

from src.checkout import total


class PreservationTest(unittest.TestCase):
    def test_no_discount(self) -> None:
        self.assertEqual(total(100, 0), 110.0)

    def test_rounding(self) -> None:
        self.assertEqual(total(19.99, 0), 21.99)
