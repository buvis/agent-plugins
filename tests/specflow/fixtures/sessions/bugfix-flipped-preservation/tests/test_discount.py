import unittest

from src.checkout import total


class DiscountTest(unittest.TestCase):
    def test_discount_before_tax(self) -> None:
        self.assertEqual(total(100, 0.10), 99.0)
