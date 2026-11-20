"""Config guard, file tools (docs/specs/config-guard.md criteria 2-3).

Each case pins one decision: an existing lint/format/type/test/hook config that
Write/Edit/MultiEdit would change must ask; a new config file, an unrelated
file, and a shared file whose tool-config part is untouched must stay silent.
A miss lets a check be loosened unasked; a false ask teaches the user to click
through the prompt. Every basename in the criterion-1 table is covered by
test_config_guard_names.py.
"""
import os
import shutil
import unittest

from configguard.harness import GuardCase, make_project, payload, run_all, PYPROJECT, PACKAGE

TOOL = "tool config"


def p(root, rel):
    return os.path.join(root, *rel.split("/"))


def edit(root, rel, old, new, **extra):
    return payload("Edit", root, file_path=p(root, rel), old_string=old, new_string=new, **extra)


def write(root, rel, content):
    return payload("Write", root, file_path=p(root, rel), content=content)


def multi(root, rel):
    return payload("MultiEdit", root, file_path=p(root, rel), edits=[{"old_string": "a", "new_string": "b"}])


def guarded_cases(root):
    fwd = root.replace("\\", "/")
    return [
        # --- criterion 2: fully guarded files, each tool and path form ---
        ("edit-eslintrc", edit(root, ".eslintrc.json", '"error"', '"off"'), (p(root, ".eslintrc.json"), "lint")),
        ("edit-git-hook", edit(root, ".git/hooks/pre-commit", "npm test", "exit 0"), (p(root, ".git/hooks/pre-commit"), "git hook")),
        ("edit-husky-nested", edit(root, ".husky/_/husky.sh", "sh", "bash"), (p(root, ".husky/_/husky.sh"), "git hook")),
        ("write-overwrite-eslintrc", write(root, ".eslintrc.json", "{}"), (p(root, ".eslintrc.json"), "lint")),
        ("multiedit-prettierrc", multi(root, ".prettierrc"), (p(root, ".prettierrc"), "formatter")),
        ("forward-slash-path", payload("Edit", root, file_path=fwd + "/.eslintrc.json", old_string="a", new_string="b"), (fwd + "/.eslintrc.json", "lint")),
        ("relative-path", payload("Edit", root, file_path=".eslintrc.json", old_string="a", new_string="b"), (".eslintrc.json", "lint")),
        ("relative-dot-slash", payload("Edit", root, file_path="./.eslintrc.json", old_string="a", new_string="b"), ("./.eslintrc.json", "lint")),
        ("relative-backslash", payload("Edit", root, file_path="sub\\eslint.config.mjs", old_string="a", new_string="b"), ("sub\\eslint.config.mjs", "lint")),
        # --- criterion 2: new files and unrelated files stay silent ---
        ("write-new-eslintrc", write(root, "fresh/.eslintrc.json", "{}"), None),
        ("write-new-jest-config", write(root, "jest.config.js", "module.exports = {};"), None),
        ("write-new-husky-hook", write(root, ".husky/pre-push", "npm test"), None),
        ("edit-source", edit(root, "src/app.ts", "1", "2"), None),
        ("edit-readme-mentions-tools", edit(root, "README.md", "eslint", "eslint and prettier"), None),
        ("edit-hook-sample", edit(root, ".git/hooks/pre-commit.sample", "sh", "bash"), None),
        ("write-hook-sample", write(root, ".git/hooks/pre-commit.sample", "x"), None),
        ("edit-near-miss-names", edit(root, "notes-jest.config.md", "notes", "n"), None),
        ("edit-no-leading-dot", edit(root, "eslintrc.md", "notes", "n"), None),
        ("notebook-edit", payload("NotebookEdit", root, notebook_path=p(root, ".eslintrc.json"), new_source="x"), None),
        ("read-tool", payload("Read", root, file_path=p(root, ".eslintrc.json")), None),
    ]


def toml_cases(root):
    py = p(root, "pyproject.toml")
    return [
        ("pyproject-ruff-inside-section", edit(root, "pyproject.toml", "ignore = []", 'ignore = ["F401"]'), (py, TOOL)),
        ("pyproject-pytest-addopts", edit(root, "pyproject.toml", 'addopts = "-q"', 'addopts = "-q -x"'), (py, TOOL)),
        ("pyproject-remove-section", edit(root, "pyproject.toml", '[tool.pytest.ini_options]\naddopts = "-q"\n', ""), (py, TOOL)),
        ("pyproject-comment-counts", edit(root, "pyproject.toml", "ignore = []", "# relaxed\nignore = []"), (py, TOOL)),
        ("pyproject-reorder-counts", edit(root, "pyproject.toml", 'select = ["E", "F"]\nignore = []', 'ignore = []\nselect = ["E", "F"]'), (py, TOOL)),
        ("pyproject-old-string-missing", edit(root, "pyproject.toml", "nope = 1", "nope = 2"), (py, TOOL)),
        ("pyproject-blank-line-only", edit(root, "pyproject.toml", "line-length = 100\n", "line-length = 100\n\n"), None),
        ("pyproject-dependency", edit(root, "pyproject.toml", '"requests>=2",', '"requests>=2.31",'), None),
        ("pyproject-name", edit(root, "pyproject.toml", 'name = "demo"', 'name = "demo2"'), None),
        ("pyproject-poetry-section", edit(root, "pyproject.toml", "packages = []", 'packages = ["src"]'), None),
        ("pyproject-build-system-after-tools", edit(root, "pyproject.toml", 'requires = ["hatchling"]', 'requires = ["setuptools"]'), None),
        ("pyproject-write-deps-only", write(root, "pyproject.toml", PYPROJECT.replace("requests>=2", "requests>=3")), None),
        ("pyproject-write-drops-ruff", write(root, "pyproject.toml", PYPROJECT.split("[tool.ruff]")[0]), (py, TOOL)),
        ("pyproject-write-new-file", write(root, "fresh/pyproject.toml", PYPROJECT), None),
        ("pyproject-plain-adds-ruff", edit(root, "plain/pyproject.toml", 'name = "plain"\n', 'name = "plain"\n\n[tool.ruff]\nignore = ["E501"]\n'), None),
        ("pyproject-crlf-tool-edit", edit(root, "crlf/pyproject.toml", 'select = ["E", "F"]\nignore = []', 'select = ["E"]\nignore = []'), (p(root, "crlf/pyproject.toml"), TOOL)),
        ("pyproject-crlf-deps-multiline", edit(root, "crlf/pyproject.toml", 'dependencies = [\n    "requests>=2",', 'dependencies = [\n    "requests>=3",'), None),
        ("setupcfg-flake8", edit(root, "setup.cfg", "max-line-length = 100", "max-line-length = 200"), (p(root, "setup.cfg"), TOOL)),
        ("setupcfg-coverage-run", edit(root, "setup.cfg", "branch = True", "branch = False"), (p(root, "setup.cfg"), TOOL)),
        ("setupcfg-metadata", edit(root, "setup.cfg", "name = demo", "name = demo2"), None),
        ("setupcfg-options-after-tools", edit(root, "setup.cfg", "packages = find:", "packages = find_namespace:"), None),
        ("cargo-lints", edit(root, "Cargo.toml", 'unsafe_code = "forbid"', 'unsafe_code = "allow"'), (p(root, "Cargo.toml"), TOOL)),
        ("cargo-dependency", edit(root, "Cargo.toml", 'serde = "1"', 'serde = "1.0.200"'), None),
        ("cargo-profile-after-lints", edit(root, "Cargo.toml", "lto = true", "lto = false"), None),
    ]


def package_cases(root):
    pj = p(root, "package.json")
    cases = [
        ("package-jest-block", edit(root, "package.json", '"testTimeout": 5000', '"testTimeout": 60000'), (pj, TOOL)),
        ("package-eslintconfig-block", edit(root, "package.json", '"eslint:recommended"', '"eslint:all"'), (pj, TOOL)),
        ("package-prettier-block-not-first", edit(root, "package.json", '"semi": false', '"semi": true'), (pj, TOOL)),
        ("package-husky-block", edit(root, "package.json", '"hooks": {}', '"hooks": {"pre-commit": "true"}'), (pj, TOOL)),
        ("package-lint-staged-block", edit(root, "package.json", '"*.ts": "eslint"', '"*.ts": "true"'), (pj, TOOL)),
        ("package-test-script", edit(root, "package.json", '"test": "jest"', '"test": "jest --passWithNoTests"'), (pj, TOOL)),
        ("package-lint-colon-script", edit(root, "package.json", '"lint:fix": "eslint . --fix"', '"lint:fix": "echo ok"'), (pj, TOOL)),
        ("package-format-script", edit(root, "package.json", '"format": "prettier --check ."', '"format": "true"'), (pj, TOOL)),
        ("package-typecheck-script", edit(root, "package.json", '"typecheck": "tsc --noEmit"', '"typecheck": "true"'), (pj, TOOL)),
        ("package-replace-all-reaches-jest", edit(root, "package.json", "true", "false", replace_all=True), (pj, TOOL)),
        ("package-old-string-missing", edit(root, "package.json", '"nope": 1', '"nope": 2'), (pj, TOOL)),
        ("package-multiedit", multi(root, "package.json"), (pj, TOOL)),
        ("package-write-drops-jest", write(root, "package.json", PACKAGE.split(',\n  "jest"')[0] + "\n}\n"), (pj, TOOL)),
        ("package-build-script", edit(root, "package.json", '"build": "tsc"', '"build": "tsc -p ."'), None),
        ("package-pretest-script", edit(root, "package.json", '"pretest": "tsc"', '"pretest": "true"'), None),
        ("package-testing-script", edit(root, "package.json", '"testing": "node t.js"', '"testing": "true"'), None),
        ("package-format-docs-script", edit(root, "package.json", '"format-docs": "mdfmt"', '"format-docs": "true"'), None),
        ("package-add-dev-script", edit(root, "package.json", '"build": "tsc",', '"build": "tsc",\n    "dev": "vite",'), None),
        ("package-bump-jest-dependency", edit(root, "package.json", '"jest": "^29.0.0"', '"jest": "^29.7.0"'), None),
        ("package-bump-lint-staged-dependency", edit(root, "package.json", '"lint-staged": "^15.0.0"', '"lint-staged": "^15.2.0"'), None),
        ("package-write-rename", write(root, "package.json", PACKAGE.replace('"demo"', '"demo2"')), None),
        ("package-write-new-file", write(root, "fresh/package.json", PACKAGE), None),
        ("package-plain-adds-test-script", edit(root, "plain/package.json", '"build": "tsc"', '"build": "tsc",\n    "test": "vitest"'), None),
        ("package-plain-old-string-missing", edit(root, "plain/package.json", '"nope": 1', '"nope": 2'), None),
        ("package-plain-multiedit", multi(root, "plain/package.json"), None),
    ]
    for d in ("pkg4", "pkgtab"):
        f = p(root, d + "/package.json")
        cases += [
            (f"{d}-jest-block", edit(root, d + "/package.json", '"testTimeout": 5000', '"testTimeout": 60000'), (f, TOOL)),
            (f"{d}-bump-jest-dependency", edit(root, d + "/package.json", '"jest": "^29.0.0"', '"jest": "^29.7.0"'), None),
        ]
    return cases


def ts_cases(root):
    ts = p(root, "tsconfig.json")
    cases = [(f"tsconfig-{key}", edit(root, "tsconfig.json", f'"{key}": {old}', f'"{key}": {new}'), (ts, TOOL))
             for key, old, new in [("strict", "true", "false"), ("noImplicitAny", "true", "false"),
                                   ("strictNullChecks", "true", "false"), ("noUncheckedIndexedAccess", "true", "false"),
                                   ("skipLibCheck", "false", "true"), ("checkJs", "true", "false"),
                                   ("allowUnreachableCode", "false", "true")]]
    return cases + [
        ("tsconfig-drop-no-unused", edit(root, "tsconfig.json", ',\n    "noUnusedLocals": true', ""), (ts, TOOL)),
        ("tsconfig-build-variant", edit(root, "tsconfig.build.json", '"strict": true', '"strict": false'), (p(root, "tsconfig.build.json"), TOOL)),
        ("jsconfig-checkjs", edit(root, "jsconfig.json", '"checkJs": true', '"checkJs": false'), (p(root, "jsconfig.json"), TOOL)),
        ("tsconfig-target", edit(root, "tsconfig.json", '"ES2022"', '"ES2023"'), None),
        ("tsconfig-strict-in-a-value", edit(root, "tsconfig.json", '["strict-src"]', '["strict-src", "lib"]'), None),
        ("tsconfig-plain-adds-strict", edit(root, "plain/tsconfig.json", '"target": "ES2022"', '"target": "ES2022",\n    "strict": false'), None),
    ]


class FileToolCases(GuardCase):
    @classmethod
    def setUpClass(cls):
        root = cls.root = make_project()
        # (name, payload, expected): expected is None (silent) or (subject, what).
        cls.cases = guarded_cases(root) + toml_cases(root) + package_cases(root) + ts_cases(root)
        cls.results = run_all([c[1] for c in cls.cases])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_file_tool_cases(self):
        for (name, _, expected), result in zip(self.cases, self.results):
            with self.subTest(name):
                if expected is None:
                    self.assert_silent(result, name)
                else:
                    self.assert_ask(result, name, "File", expected[0], expected[1])


if __name__ == "__main__":
    unittest.main()
