"""Issue #44 approximate display: worked examples for the unconfirmed reading in fathom.approximate."""

import unittest

from fathom.approximate import approximate, is_approximate


class ApproximateReading(unittest.TestCase):
    def test_worked_examples(self):
        cases = {
            4.93: 5, 4.99: 5, 4.9: 5, 4.8: 5, 4.7: 4.7, 4.1: 4, 4.0: 4,
            5.2: 5, 5.24: 5, 5.3: 5.3, 5.9: 6, 6.1: 6, 7: 7,
            48: 50, 52: 50, 91: 90, 47: 47, 1234: 1200, 0.0487: 0.05, 0.193: 0.2,
            9.96: 10, -4.93: -5,
        }
        for value, shown in cases.items():
            with self.subTest(value=value):
                self.assertEqual(approximate(value), shown)

    def test_non_numbers_and_edges_pass_through(self):
        for v in (None, True, 'x', 0, float('nan'), float('inf')):
            self.assertIs(approximate(v), v)

    def test_marks_only_changed_values(self):
        self.assertTrue(is_approximate(4.93))
        self.assertFalse(is_approximate(4.7))
        self.assertFalse(is_approximate(7))


if __name__ == '__main__':
    unittest.main()
