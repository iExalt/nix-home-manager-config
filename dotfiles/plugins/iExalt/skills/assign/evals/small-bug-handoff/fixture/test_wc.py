import unittest

from wc import count_lines, count_words


class CountTest(unittest.TestCase):
    def test_lines_end_with_newline(self):
        self.assertEqual(count_lines("a\nb\n"), 2)

    def test_words(self):
        self.assertEqual(count_words("one two\nthree"), 3)


if __name__ == "__main__":
    unittest.main()
