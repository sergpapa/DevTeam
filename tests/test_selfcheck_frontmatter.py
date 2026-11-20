"""Strict frontmatter parse: spec criterion 1 (docs/specs/plugin-self-tests.md).

Each failing case is a shape that YAML rejects or reads differently, or one
the strict subset bans because it is easy to get wrong (several leading
indicator characters are legal YAML but read as syntax by a human editor).
A rejected frontmatter loads with empty metadata and the skill vanishes
without any error.
"""
import unittest

from selfcheck.frontmatter import parse

NL = chr(10)


def doc(*lines):
    return "---\n" + "\n".join(lines) + "\n---\nBody text.\n"


class ValidFrontmatter(unittest.TestCase):
    def test_plain_values_are_read(self):
        fields, errors = parse(doc("name: adr", "description: Record a decision. Use when x."))
        self.assertEqual([], errors)
        self.assertEqual({"name": "adr", "description": "Record a decision. Use when x."}, fields)

    def test_double_quoted_value_is_unwrapped(self):
        fields, errors = parse(doc("name: project", 'description: "Pipeline: a to b."'))
        self.assertEqual([], errors)
        self.assertEqual("Pipeline: a to b.", fields["description"])

    def test_double_quoted_escapes_are_decoded(self):
        fields, errors = parse(doc("name: x", r'description: "say \"hi\" to C:\\dir"'))
        self.assertEqual([], errors)
        self.assertEqual('say "hi" to C:\\dir', fields["description"])

    def test_single_quoted_value_with_doubled_quote(self):
        fields, errors = parse(doc("name: x", "description: 'it''s: fine'"))
        self.assertEqual([], errors)
        self.assertEqual("it's: fine", fields["description"])

    def test_plain_value_may_hold_quotes_colons_without_space_and_unicode(self):
        value = 'Edgy \u2014 triggers on "edgy", "brutalist"; see https://x.io/a#b, ratio 16:9 \u2192 done.'
        fields, errors = parse(doc("name: edge", "description: " + value))
        self.assertEqual([], errors)
        self.assertEqual(value, fields["description"])

    def test_crlf_line_endings_are_accepted(self):
        fields, errors = parse("---\r\nname: adr\r\ndescription: Use when x.\r\n---\r\nBody\r\n")
        self.assertEqual([], errors)
        self.assertEqual({"name": "adr", "description": "Use when x."}, fields)

    def test_blank_line_inside_block_is_allowed(self):
        fields, errors = parse(doc("name: adr", "", "description: Use when x."))
        self.assertEqual([], errors)
        self.assertEqual("adr", fields["name"])

    def test_fence_lines_in_the_body_are_ignored(self):
        fields, errors = parse(doc("name: a", "description: d") + "---" + NL + "not: frontmatter: here" + NL)
        self.assertEqual([], errors)
        self.assertEqual({"name": "a", "description": "d"}, fields)

    def test_other_keys_are_kept(self):
        fields, errors = parse(doc("name: a", "description: d", "keep-coding-instructions: true", "model: sonnet"))
        self.assertEqual([], errors)
        self.assertEqual("true", fields["keep-coding-instructions"])
        self.assertEqual("sonnet", fields["model"])


class RejectedFrontmatter(unittest.TestCase):
    def assertRejected(self, text, *fragments):
        _, errors = parse(text)
        self.assertTrue(errors, "expected an error, got none")
        joined = "\n".join(errors)
        for fragment in fragments:
            self.assertIn(fragment, joined)

    def test_the_real_2_0_3_unquoted_colon_says_to_double_quote(self):
        line = ("description: Whole-system pipeline \u2014 take a product idea from conception to a "
                "working v1 across many sessions: discovery \u2192 architecture.")
        self.assertRejected(doc("name: project", line), "line 3", "double quotes")

    def test_plain_value_ending_in_colon(self):
        self.assertRejected(doc("name: a", "description: Steps:"), "line 3")

    def test_plain_value_with_colon_then_tab(self):
        self.assertRejected(doc("name: a", "description: Use when:" + chr(9) + "things"), "line 3", "double quotes")

    def test_name_or_description_that_yaml_reads_as_null_bool_or_number(self):
        for line in ("name: 123", "name: ~", "description: null", "description: True",
                     "description: false", "description: 1.5", "description: -2", "description: .inf"):
            with self.subTest(line=line):
                key = line.split(":")[0]
                other = "description: d" if key == "name" else "name: a"
                self.assertRejected(doc(other, line) if key == "description" else doc(line, other),
                                    "double quotes")

    def test_quoted_number_and_other_keys_with_booleans_are_fine(self):
        fields, errors = parse(doc('name: "123"', "description: d", "keep-coding-instructions: true",
                                   "force-for-plugin: false"))
        self.assertEqual([], errors)
        self.assertEqual("123", fields["name"])

    def test_plain_value_with_space_hash_comment(self):
        self.assertRejected(doc("name: a", "description: Use when x #not a comment"), "line 3")

    def test_plain_value_starting_with_an_indicator(self):
        for first in "-?:,[]{}#&*!|>'\"%@`":
            with self.subTest(first=first):
                self.assertRejected(doc("name: a", "description: " + first + "x y"), "line 3")

    def test_empty_value(self):
        for line in ("name:", "name: ", "name:   "):
            with self.subTest(line=line):
                self.assertRejected(doc(line, "description: d"), "line 2")

    def test_line_without_colon_space(self):
        for line in ("name:adr", "just some text"):
            with self.subTest(line=line):
                self.assertRejected(doc(line, "description: d"), "line 2")

    def test_bad_key(self):
        for line in ("1name: x", "na me: x", "_name: x"):
            with self.subTest(line=line):
                self.assertRejected(doc(line, "description: d"), "line 2")

    def test_indented_continuation_line(self):
        self.assertRejected(doc("name: a", "description: first part", "  second part"), "line 4")

    def test_comment_line(self):
        self.assertRejected(doc("# a comment", "name: a", "description: d"), "line 2")

    def test_duplicate_key(self):
        self.assertRejected(doc("name: a", "description: d", "name: b"), "line 4", "name")

    def test_unterminated_double_quote(self):
        self.assertRejected(doc("name: a", 'description: "never closed'), "line 3")

    def test_text_after_closing_quote(self):
        self.assertRejected(doc("name: a", 'description: "quoted" tail'), "line 3")
        self.assertRejected(doc("name: a", "description: 'quoted' tail"), "line 3")

    def test_unsupported_escape_in_double_quotes(self):
        self.assertRejected(doc("name: a", r'description: "a\nb"'), "line 3")

    def test_lone_quote_inside_single_quotes(self):
        self.assertRejected(doc("name: a", "description: 'it's'"), "line 3")

    def test_missing_opening_fence(self):
        self.assertRejected("name: a\ndescription: d\n---\nBody\n", "line 1")

    def test_missing_closing_fence(self):
        self.assertRejected("---\nname: a\ndescription: d\nBody\n", "---")

    def test_byte_order_mark_before_fence(self):
        self.assertRejected("\ufeff" + doc("name: a", "description: d"), "line 1")

    def test_fence_with_trailing_space(self):
        self.assertRejected(NL.join(["--- ", "name: a", "description: d", "---", ""]), "line 1")
        self.assertRejected(NL.join(["---", "name: a", "description: d", "--- ", ""]), "---")

    def test_tab_indented_line(self):
        self.assertRejected(doc("name: a", "description: d", chr(9) + "more"), "line 4")

    def test_quoted_empty_value(self):
        self.assertRejected(doc('name: ""', "description: d"), "line 2")
        self.assertRejected(doc("name: ''", "description: d"), "line 2")

    def test_empty_file(self):
        self.assertRejected("", "line 1")


if __name__ == "__main__":
    unittest.main()
