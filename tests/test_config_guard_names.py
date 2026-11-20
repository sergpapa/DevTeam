"""Config guard, every guarded basename (docs/specs/config-guard.md criterion 1).

The table of guarded names is read from the spec itself, so a name that the
spec lists but the hook forgets (or misspells) fails here, and the test cannot
drift from the spec. Each `*` is expanded with a sample suffix. Near-misses
pin that matching is on the whole basename, exact and case-sensitive.
"""
import os
import re
import shutil
import unittest

from configguard.harness import SPEC, GuardCase, make_project, payload, run_all


def spec_table():
    """[(category, basename-pattern)] from the criterion-1 table in the spec."""
    with open(SPEC, encoding="utf-8") as f:
        text = f.read()
    rows = re.findall(r"(?m)^\s*\|\s*(lint|formatter|type-checker|test-runner|git hook)\s*\|(.*)\|\s*$", text)
    out = []
    for cat, cell in rows:
        for name in re.findall(r"`([^`]+)`", cell):
            if name in (".husky", ".git/hooks", "*.sample"):
                continue
            out.append((cat, name))
    return out


def expand(pattern):
    return pattern.replace("*", "json")


NEAR_MISSES = ["jest.config", "pytest.ini.bak", "xeslint.config.js", "pylintrc2", "my.prettierrc",
               "tox.ini.orig", "ruff.toml.txt", "lefthook.yml.bak", ".ESLINTRC.json", "Pytest.ini"]


class EveryGuardedName(GuardCase):
    @classmethod
    def setUpClass(cls):
        cls.table = spec_table()
        names = {expand(n): "x\n" for _, n in cls.table}
        names.update({f"near/{n}": "x\n" for n in NEAR_MISSES})
        cls.root = make_project(names)
        cls.cases = [(cat, expand(n)) for cat, n in cls.table]
        cls.results = run_all([payload("Edit", cls.root, file_path=os.path.join(cls.root, n),
                                       old_string="x", new_string="y") for _, n in cls.cases])
        cls.near = run_all([payload("Edit", cls.root, file_path=os.path.join(cls.root, "near", n),
                                    old_string="x", new_string="y") for n in NEAR_MISSES])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_table_was_read(self):
        self.assertGreaterEqual(len(self.table), 70,"the criterion-1 table in the spec was not parsed")

    def test_every_listed_name_asks_with_its_category(self):
        for (cat, name), result in zip(self.cases, self.results):
            with self.subTest(name):
                self.assert_ask(result, name, "File", os.path.join(self.root, name), cat)

    def test_near_misses_are_silent(self):
        for name, result in zip(NEAR_MISSES, self.near):
            with self.subTest(name):
                self.assert_silent(result, name)


if __name__ == "__main__":
    unittest.main()
