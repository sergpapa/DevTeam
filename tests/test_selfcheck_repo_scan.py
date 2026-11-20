"""check_repo(root): which files the repo-wide run looks at (spec criteria 1-5).

Builds a throwaway git repo per test, because the file list comes from git:
tracked files plus new files git would add, never ignored ones.
"""
import os
import shutil
import subprocess
import tempfile
import unittest

from selfcheck.checks import check_repo

GOOD_SKILL = "---\nname: %s\ndescription: Does a thing. Use when x.\n---\nBody.\n"
EM_DASH_MOJIBAKE = "\u00e2\u20ac\u201d"


class RepoScan(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="selfcheck-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        subprocess.run(["git", "init", "-q", self.root], check=True)
        # Isolate from the machine's global config (core.autocrlf=true on Windows
        # prints an LF-to-CRLF warning for every staged file).
        subprocess.run(["git", "-C", self.root, "config", "core.autocrlf", "false"], check=True)

    def write(self, relpath, text):
        path = os.path.join(self.root, *relpath.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def stage_all(self):
        subprocess.run(["git", "-C", self.root, "add", "-A"], check=True)

    def test_clean_repo_has_no_problems(self):
        self.write("skills/adr/SKILL.md", GOOD_SKILL % "adr")
        self.write("agents/architect.md", "---\nname: architect\ndescription: Designs.\n---\n")
        self.write("output-styles/plain.md", "---\nname: Plain\ndescription: Plain.\n---\n")
        self.write("README.md", "# Title \u2014 ok\n")
        self.stage_all()
        self.assertEqual([], check_repo(self.root))

    def test_finds_problems_in_every_kind_of_file(self):
        self.write("skills/adr/SKILL.md", GOOD_SKILL % "adrx")
        self.write("agents/architect.md", "---\nname: architect\ndescription: Does: things.\n---\n")
        self.write("output-styles/plain.md", "---\nname: Plain\n---\n")
        self.stage_all()
        joined = "\n".join(check_repo(self.root))
        self.assertIn("skills/adr/SKILL.md", joined)
        self.assertIn("agents/architect.md", joined)
        self.assertIn("output-styles/plain.md", joined)

    def test_untracked_new_file_is_checked(self):
        self.write("skills/adr/SKILL.md", GOOD_SKILL % "adr")
        self.stage_all()
        self.write("docs/new.md", "a " + EM_DASH_MOJIBAKE + " b\n")
        self.write("skills/debug/SKILL.md", GOOD_SKILL % "debugx")
        joined = "\n".join(check_repo(self.root))
        self.assertIn("docs/new.md:1", joined)
        self.assertIn("skills/debug/SKILL.md", joined)

    def test_ignored_files_are_skipped(self):
        self.write(".gitignore", "results/\n")
        self.write("results/out.md", "a " + EM_DASH_MOJIBAKE + " b\n")
        self.stage_all()
        self.assertEqual([], check_repo(self.root))

    def test_reference_files_are_neither_capped_nor_parsed(self):
        self.write("skills/edge/SKILL.md", GOOD_SKILL % "edge")
        self.write("skills/edge/references/big.md", "no frontmatter here\n" + "x" * 30000 + "\n")
        self.stage_all()
        self.assertEqual([], check_repo(self.root))

    def test_encoding_is_checked_in_every_text_file_not_just_skills(self):
        self.write("hooks/gate.sh", "#!/bin/sh\necho '" + EM_DASH_MOJIBAKE + "'\n")
        self.stage_all()
        self.assertIn("hooks/gate.sh:2", "\n".join(check_repo(self.root)))

    def test_binary_file_is_skipped(self):
        path = os.path.join(self.root, "logo.png")
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xfe")
        self.stage_all()
        self.assertEqual([], check_repo(self.root))

    def test_a_folder_that_is_not_a_git_repo_raises(self):
        # An empty file list would report "no problems" without checking anything.
        plain = tempfile.mkdtemp(prefix="selfcheck-nogit-")
        self.addCleanup(shutil.rmtree, plain, ignore_errors=True)
        with self.assertRaisesRegex(RuntimeError, "git"):
            check_repo(plain)

    def test_deleted_but_still_tracked_file_is_skipped(self):
        self.write("skills/adr/SKILL.md", GOOD_SKILL % "adr")
        self.write("notes.md", "temp\n")
        self.stage_all()
        os.remove(os.path.join(self.root, "notes.md"))
        self.assertEqual([], check_repo(self.root))


if __name__ == "__main__":
    unittest.main()
