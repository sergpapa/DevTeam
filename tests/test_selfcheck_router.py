"""Lexical router unit tests: spec criterion 6 (docs/specs/plugin-self-tests.md).

rank(prompt, skills) takes {name: description} and returns every skill as
(name, score), best first. The document for a skill is its name plus its
description. These cases use toy skills so they test the ranker, not the
real descriptions (tests/test_repo.py does that).
"""
import os
import shutil
import tempfile
import unittest

from selfcheck import router

TOY = {
    "debug": "Systematic debugging. Use when behaviour is wrong and nobody knows why.",
    "adr": "Record an architecture decision. Use when a decision is made about the database or stack.",
    "hygiene": "Repo cleanup pass: dead code, secrets, oversized files. Use before committing.",
}


class Rank(unittest.TestCase):
    def top(self, prompt):
        return router.rank(prompt, TOY)[0][0]

    def test_returns_every_skill_best_first(self):
        ranked = router.rank("record the decision", TOY)
        self.assertEqual(sorted(TOY), sorted(name for name, _ in ranked))
        scores = [score for _, score in ranked]
        self.assertEqual(sorted(scores, reverse=True), scores)

    def test_matching_words_route_to_the_right_skill(self):
        self.assertEqual("adr", self.top("Record why we chose this database"))
        self.assertEqual("hygiene", self.top("Find the dead code and any secrets"))

    def test_word_forms_match_through_suffix_stripping(self):
        # Each prompt shares no exact word with any toy description, so only
        # suffix stripping can produce a positive score.
        for prompt, expected in (("behaviours", "debug"), ("decisions please", "adr"),
                                 ("committed secret", "hygiene")):
            with self.subTest(prompt=prompt):
                name, score = router.rank(prompt, TOY)[0]
                self.assertEqual(expected, name)
                self.assertGreater(score, 0)

    def test_skill_name_counts_as_a_word_of_its_document(self):
        skills = {"edge": "Bold web design direction.", "tdd": "Rules for writing tests first."}
        self.assertEqual("edge", router.rank("make it edge", skills)[0][0])

    def test_stopwords_alone_score_zero(self):
        for prompt in ("the and of to a is it", "", "   ", "?!"):
            with self.subTest(prompt=prompt):
                self.assertTrue(all(score == 0 for _, score in router.rank(prompt, TOY)))

    def test_matching_is_case_and_punctuation_insensitive(self):
        self.assertEqual(router.rank("record the decision", TOY),
                         router.rank("RECORD, the... decision!", TOY))

    def test_rare_word_outweighs_common_word(self):
        # Raw term counts favour b (4 against 3); only IDF lifts a, and b is
        # listed first so a tie cannot fall to a by dict order.
        skills = {"b": "code code code code", "a": "code code rare"}
        self.assertEqual("a", router.rank("rare code", skills)[0][0])

    def test_non_ascii_letters_and_digits_are_words(self):
        skills = {"greek": "\u03b5\u03c0\u03b9\u03c3\u03ba\u03b5\u03c5\u03ae \u03c3\u03c6\u03b1\u03bb\u03bc\u03ac\u03c4\u03c9\u03bd",
                  "ship": "Release version v2 to production."}
        self.assertEqual("greek", router.rank("\u03c3\u03c6\u03b1\u03bb\u03bc\u03ac\u03c4\u03c9\u03bd", skills)[0][0])
        self.assertEqual("ship", router.rank("v2", skills)[0][0])

    def test_verb_forms_meet_and_short_stems_are_kept(self):
        same = [("use", "used", "using", "uses"), ("code", "coded", "coding", "codes"),
                ("file", "files", "filed"), ("commit", "committed", "committing")]
        for forms in same:
            with self.subTest(forms=forms):
                self.assertEqual(1, len({tuple(router.tokens(f)) for f in forms}))
        for word in ("speed", "string", "need"):
            with self.subTest(word=word):
                self.assertNotEqual([word[:-2]], router.tokens(word))
                self.assertNotEqual([word[:-3]], router.tokens(word))

    def test_load_skills_keys_by_directory_and_refuses_broken_frontmatter(self):
        root = tempfile.mkdtemp(prefix="selfcheck-skills-")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)

        def write(directory, text):
            os.makedirs(os.path.join(root, "skills", directory))
            with open(os.path.join(root, "skills", directory, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(text)

        write("adr", "---\nname: adr\ndescription: Record decisions.\n---\n")
        write("copy", "---\nname: adr\ndescription: Copied, name never changed.\n---\n")
        self.assertEqual({"adr": "Record decisions.", "copy": "Copied, name never changed."},
                         router.load_skills(root))
        write("broken", "---\nname: broken\ndescription: Pipeline: a to b.\n---\n")
        with self.assertRaisesRegex(ValueError, "broken"):
            router.load_skills(root)

    def test_no_skills_gives_empty_ranking(self):
        self.assertEqual([], router.rank("record the decision", {}))


if __name__ == "__main__":
    unittest.main()
