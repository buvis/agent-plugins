import unittest


class OrdersTest(unittest.TestCase):
    def test_empty_month(self) -> None:
        self.assertEqual([], [])
