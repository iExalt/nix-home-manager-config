"""Tests for export_plain. Run: python3 -I -m unittest discover -s <scripts dir>."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_plain import NoAppendixError, convert, problems, words

DRAFT = """# Review

<!-- draft note: not for the review tool -->

---

## 1. Contributions

Draft designs for the cache shipped in May. #4521 fixed the leak.

**1. I cut the build.** It went from 60 to 8 minutes ([PR](https://example.com/pr/1)).
- **I fixed it upstream** in *two* ~~days~~ ([wiki](https://example.com/Foo_(bar)) "t").
  - Ran `make check` on snake__case and file_name_here daily.
> A quote from a [reviewer](https://example.com/q "title").

### Evidence appendix process

Body text that must survive.

## Evidence appendix (not submitted)

- https://example.com/secret
"""


class ExportTest(unittest.TestCase):
    def test_converts_real_markup_and_keeps_lookalikes(self):
        text = convert(DRAFT)
        self.assertEqual(problems(text), [])
        self.assertIn("Draft designs for the cache shipped in May. #4521 fixed the leak.", text)
        self.assertIn("1. I cut the build. It went from 60 to 8 minutes (PR).", text)
        self.assertIn('• I fixed it upstream in two days (wiki "t").', text)
        self.assertIn("  • Ran make check on snake__case and file_name_here daily.", text)
        self.assertIn("A quote from a reviewer.", text)
        self.assertIn("Body text that must survive.", text)
        self.assertNotIn("secret", text)
        self.assertNotIn("draft note", text)

    def test_missing_appendix_is_an_error(self):
        with self.assertRaises(NoAppendixError):
            convert("# Review\n\nText.\n")
        self.assertEqual(convert("# Review\n\nText.\n", None), "Review\n\nText.\n")

    def test_flags_urls_dashes_and_open_markers(self):
        found = problems("See https://example.com/x.\nShipped it — fast.\nGoal [confirm level].\n")
        self.assertEqual([p.split(": ")[1] for p in found], ["URL", "em or en dash", "open marker"])

    def test_word_count_skips_bullets(self):
        self.assertEqual(words("• one two\n• three\n"), 3)


if __name__ == "__main__":
    unittest.main()
