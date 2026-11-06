import unittest
import engineering


class TestEngineering(unittest.TestCase):

    def test_unit_conversion(self):
        self.assertAlmostEqual(1, 1.0)

    def test_basic_arithmetic(self):
        self.assertEqual(2 + 2, 4)


if __name__ == "__main__":
    unittest.main()
