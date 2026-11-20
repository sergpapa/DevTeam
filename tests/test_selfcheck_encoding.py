"""Encoding checks: spec criterion 5 (docs/specs/plugin-self-tests.md).

Every mojibake sample is written as \\u escapes so this file stays ASCII and
does not trip the repo-wide encoding check itself.

find(text) returns (line, column, bad_run, intended_char) tuples, 1-based.
check_encoding(relpath, data) returns problem strings starting with the path.
"""
import unittest

from selfcheck.checks import check_encoding
from selfcheck.mojibake import find

EM_DASH_MOJIBAKE = "\u00e2\u20ac\u201d"    # what 2.0.3 shipped in README.md
ARROW_MOJIBAKE = "\u00e2\u2020\u2019"      # right arrow
E_ACUTE_MOJIBAKE = "\u00c3\u00a9"          # e acute
NBSP_MOJIBAKE = "\u00c2\u00a0"             # no-break space
EMOJI_MOJIBAKE = "\u00f0\u0178\u02dc\u20ac"  # U+1F600, four bytes
UNDEFINED_1252_MOJIBAKE = "\u00c3\u008d"   # I acute; 0x8D is undefined in 1252


class FindMojibake(unittest.TestCase):
    def test_double_encoded_em_dash(self):
        self.assertEqual([(1, 5, EM_DASH_MOJIBAKE, "\u2014")], find("a b " + EM_DASH_MOJIBAKE + " c"))

    def test_two_three_and_four_byte_characters(self):
        cases = [(E_ACUTE_MOJIBAKE, "\u00e9"), (ARROW_MOJIBAKE, "\u2192"),
                 (EMOJI_MOJIBAKE, "\U0001F600"), (NBSP_MOJIBAKE, "\u00a0"),
                 (UNDEFINED_1252_MOJIBAKE, "\u00cd")]
        for bad, intended in cases:
            with self.subTest(intended=intended):
                self.assertEqual([(1, 1, bad, intended)], find(bad))

    def test_reports_line_and_column_of_each_run(self):
        text = "clean line\nx " + EM_DASH_MOJIBAKE + " y " + ARROW_MOJIBAKE + "\n"
        self.assertEqual([(2, 3, EM_DASH_MOJIBAKE, "\u2014"), (2, 9, ARROW_MOJIBAKE, "\u2192")], find(text))

    def test_correct_unicode_is_not_flagged(self):
        clean = ("caf\u00e9 na\u00efve \u00c5ngstr\u00f6m \u00c6r\u00f8sk\u00f8bing "
                 "\u2014 \u2192 \u2713 \u039a\u03b1\u03bb\u03b7\u03bc\u03ad\u03c1\u03b1 \U0001F600 "
                 "\u00a9 2026 \u00bd \u00ab\u00bb \u00d7")
        self.assertEqual([], find(clean))

    def test_letter_before_curly_quote_or_ellipsis_is_not_flagged(self):
        # German and French text puts a closing quote or an ellipsis right after
        # a letter; those pairs also decode as UTF-8 (to NKo or Arabic letters).
        sharp_s, open_low, close, ellipsis = chr(0xdf), chr(0x201e), chr(0x201c), chr(0x2026)
        text = ("Er sagte " + open_low + "Gru" + sharp_s + close + " und ging zur Stra" + sharp_s + ellipsis
                + " " + chr(0xab) + "Fran" + chr(0xe7) + "ais" + chr(0xbb) + " na" + chr(0xef) + "ve" + chr(0x2019))
        self.assertEqual([], find(text))

    def test_double_encoded_greek_and_cyrillic_are_flagged(self):
        alpha_mojibake = chr(0xce) + chr(0xb1)    # Greek small alpha
        de_mojibake = chr(0xd0) + chr(0xb4)       # Cyrillic small de
        self.assertEqual([(1, 1, alpha_mojibake, chr(0x3b1)), (1, 4, de_mojibake, chr(0x434))],
                         find(alpha_mojibake + " " + de_mojibake))

    def test_lead_character_followed_by_ascii_is_not_flagged(self):
        self.assertEqual([], find("\u00c3x \u00e2 a \u00c2 b"))

    def test_incomplete_sequence_is_not_flagged(self):
        # 0xE2 0x80 alone is a truncated three-byte sequence, not a character.
        self.assertEqual([], find("\u00e2\u20ac x"))


class CheckEncoding(unittest.TestCase):
    def test_clean_utf8_passes(self):
        self.assertEqual([], check_encoding("README.md", "Plain \u2014 text \u2192 ok\n".encode("utf-8")))

    def test_invalid_utf8_fails(self):
        problems = check_encoding("notes.md", b"ok\n\xff\xfe broken\n")
        self.assertEqual(1, len(problems))
        self.assertTrue(problems[0].startswith("notes.md"))
        self.assertIn("UTF-8", problems[0])

    def test_byte_order_mark_fails(self):
        problems = check_encoding("README.md", b"\xef\xbb\xbf# Title\n")
        self.assertEqual(1, len(problems))
        self.assertIn("BOM", problems[0])

    def test_mojibake_is_reported_with_line_and_intended_character(self):
        data = ("# Title\nrow " + EM_DASH_MOJIBAKE + " here\n").encode("utf-8")
        problems = check_encoding("README.md", data)
        self.assertEqual(1, len(problems))
        self.assertTrue(problems[0].startswith("README.md:2"), problems[0])
        self.assertIn(EM_DASH_MOJIBAKE, problems[0])
        self.assertIn(chr(0x2014), problems[0])

    def test_one_problem_per_mojibake_run(self):
        nl = chr(10)
        text = "a " + EM_DASH_MOJIBAKE + nl + "b " + ARROW_MOJIBAKE + " " + EM_DASH_MOJIBAKE + nl
        problems = check_encoding("README.md", text.encode("utf-8"))
        self.assertEqual(["README.md:1", "README.md:2", "README.md:2"],
                         [":".join(p.split(":")[:2]) for p in problems])


if __name__ == "__main__":
    unittest.main()
