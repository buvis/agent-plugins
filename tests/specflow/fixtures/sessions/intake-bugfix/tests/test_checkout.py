import unittest

from src.checkout import total


class TotalTest(unittest.TestCase):
    def test_no_discount(self) -> None:
        self.assertEqual(total(100, 0), 110.0)
