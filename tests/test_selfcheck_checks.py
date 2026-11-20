"""Per-file checks: spec criteria 2-4 (docs/specs/plugin-self-tests.md).

check_file(relpath, data) takes a repo-relative path with forward slashes and
the file's bytes, and returns a list of problem strings, each starting with
the path. An empty list means the file passes.
"""
import unittest

from selfcheck.checks import check_file

TRIGGER = "Record a decision. Use when a choice is made."


def skill(name="adr", description=TRIGGER, body="Body.\n"):
    return ("---\nname: %s\ndescription: %s\n---\n%s" % (name, description, body)).encode("utf-8")


class Assertions(unittest.TestCase):
    def assertClean(self, relpath, data):
        self.assertEqual([], check_file(relpath, data))

    def assertProblem(self, relpath, data, *fragments):
        problems = check_file(relpath, data)
        self.assertTrue(problems, "expected a problem, got none")
        for p in problems:
            self.assertTrue(p.startswith(relpath), "problem does not start with the path: %r" % p)
        joined = "\n".join(problems)
        for fragment in fragments:
            self.assertIn(fragment, joined)


class SkillFiles(Assertions):
    def test_good_skill_passes(self):
        self.assertClean("skills/adr/SKILL.md", skill())

    def test_frontmatter_error_is_reported_with_path_and_line(self):
        data = skill(name="project", description="Pipeline across sessions: discovery. Use when x.")
        self.assertProblem("skills/project/SKILL.md", data, "line 3", "double quotes")

    def test_name_must_match_directory(self):
        self.assertProblem("skills/adr/SKILL.md", skill(name="adrx"), "adrx", "directory")

    def test_name_must_be_lowercase_letters_digits_hyphens(self):
        for bad in ("Adr", "my_skill", "two.words"):
            with self.subTest(name=bad):
                self.assertProblem("skills/%s/SKILL.md" % bad, skill(name=bad), bad)

    def test_name_at_most_64_characters(self):
        ok, long = "a" * 64, "a" * 65
        self.assertClean("skills/%s/SKILL.md" % ok, skill(name=ok))
        self.assertProblem("skills/%s/SKILL.md" % long, skill(name=long), "64")

    def test_missing_name_or_description(self):
        no_desc = b"---\nname: adr\n---\nBody\n"
        no_name = ("---\ndescription: %s\n---\nBody\n" % TRIGGER).encode()
        self.assertProblem("skills/adr/SKILL.md", no_desc, "description")
        self.assertProblem("skills/adr/SKILL.md", no_name, "name")

    def test_every_accepted_trigger_phrase_passes_in_any_case(self):
        for phrase in ("Use when", "use whenever", "Use for", "Use before", "USE AFTER", "Invoke BEFORE"):
            with self.subTest(phrase=phrase):
                self.assertClean("skills/adr/SKILL.md", skill(description="Does a thing. %s x." % phrase))

    def test_description_without_trigger_phrase_fails(self):
        for desc in ("Records decisions about architecture.", "A user can choose to use it.", "Abuse whenever."):
            with self.subTest(desc=desc):
                self.assertProblem("skills/adr/SKILL.md", skill(description=desc), "Use when")

    def test_description_at_most_1024_characters(self):
        base = "Use when x. "
        ok = base + "y" * (1024 - len(base))
        self.assertClean("skills/adr/SKILL.md", skill(description=ok))
        self.assertProblem("skills/adr/SKILL.md", skill(description=ok + "y"), "1024")

    def test_description_cap_counts_characters_not_bytes(self):
        dashes = "Use when x. " + "\u2014" * 1000
        self.assertGreater(len(dashes.encode("utf-8")), 1024)
        self.assertClean("skills/adr/SKILL.md", skill(description=dashes))

    def test_skill_file_size_cap_is_20480_bytes(self):
        head = skill(body="")
        exact = head + b"x" * (20480 - len(head))
        self.assertEqual(20480, len(exact))
        self.assertClean("skills/adr/SKILL.md", exact)
        self.assertProblem("skills/adr/SKILL.md", exact + b"x", "20481", "20480")

    def test_size_cap_counts_bytes_not_characters(self):
        data = skill(body="\u2014" * 7000)
        self.assertLess(len(data.decode("utf-8")), 20480)
        self.assertProblem("skills/adr/SKILL.md", data, "20480")

    def test_byte_order_mark_fails(self):
        self.assertProblem("skills/adr/SKILL.md", bytes([0xEF, 0xBB, 0xBF]) + skill(), "line 1")

    def test_invalid_utf8_is_reported_not_raised(self):
        self.assertProblem("skills/adr/SKILL.md", skill() + bytes([0xFF, 0xFE]), "UTF-8")

    def test_crlf_skill_passes(self):
        self.assertClean("skills/adr/SKILL.md", skill().replace(bytes([10]), bytes([13, 10])))


class AgentFiles(Assertions):
    def agent(self, name="architect", description="Designs systems."):
        return ("---\nname: %s\ndescription: %s\ntools: Read, Grep\nmodel: inherit\n---\nBody\n"
                % (name, description)).encode()

    def test_good_agent_passes_without_trigger_phrase(self):
        self.assertClean("agents/architect.md", self.agent())

    def test_agent_name_must_match_file_name(self):
        self.assertProblem("agents/architect.md", self.agent(name="architects"), "architects", "file name")

    def test_agent_is_not_size_capped(self):
        big = self.agent() + b"x" * 30000
        self.assertClean("agents/architect.md", big)

    def test_agent_frontmatter_is_parsed_strictly(self):
        self.assertProblem("agents/architect.md", self.agent(description="Does: things"), "line 3")

    def test_agent_missing_name(self):
        self.assertProblem("agents/architect.md", b"---\ndescription: d\n---\nBody\n", "name")


class OutputStyleFiles(Assertions):
    def test_style_name_may_differ_from_file_name(self):
        data = b"---\nname: Plain\ndescription: Answer first.\nkeep-coding-instructions: true\n---\nBody\n"
        self.assertClean("output-styles/plain.md", data)

    def test_style_frontmatter_is_parsed_strictly(self):
        data = b"---\nname: Plain\ndescription: Answer first: always.\n---\nBody\n"
        self.assertProblem("output-styles/plain.md", data, "line 3")

    def test_style_missing_description(self):
        self.assertProblem("output-styles/plain.md", b"---\nname: Plain\n---\nBody\n", "description")


if __name__ == "__main__":
    unittest.main()
