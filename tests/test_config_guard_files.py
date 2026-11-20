"""Config guard, file tools (docs/specs/config-guard.md criteria 1-3).

Each case pins one decision: an existing lint/format/type/test/hook config that
Write/Edit/MultiEdit would change must ask; a new config file, an unrelated
file, and a shared file whose tool-config part is untouched must stay silent.
A miss lets a check be loosened unasked; a false ask teaches the user to click
through the prompt.
"""
import os
import shutil
import unittest

from configguard.harness import GuardCase, make_project, payload, run_all, PYPROJECT, PACKAGE


def p(root, rel):
    return os.path.join(root, *rel.split("/"))


def edit(root, rel, old, new, **extra):
    return payload("Edit", root, file_path=p(root, rel), old_string=old, new_string=new, **extra)


def write(root, rel, content):
    return payload("Write", root, file_path=p(root, rel), content=content)


def multi(root, rel):
    return payload("MultiEdit", root, file_path=p(root, rel),
                   edits=[{"old_string": "a", "new_string": "b"}])


class FileToolCases(GuardCase):
    @classmethod
    def setUpClass(cls):
        root = cls.root = make_project()
        fwd = root.replace("\\", "/")
        # (name, payload, expected) where expected is None (silent) or (subject, what-word).
        cls.cases = [
            # --- criterion 1+2: fully guarded files, one per category and naming form ---
            ("edit-eslintrc", edit(root, ".eslintrc.json", '"error"', '"off"'), (p(root, ".eslintrc.json"), "lint")),
            ("edit-eslint-flat-nested", edit(root, "sub/eslint.config.mjs", "[]", "[{}]"), (p(root, "sub/eslint.config.mjs"), "lint")),
            ("edit-biome", edit(root, "biome.json", "true", "false"), (p(root, "biome.json"), "lint")),
            ("edit-prettierrc", edit(root, ".prettierrc", "true", "false"), (p(root, ".prettierrc"), "formatter")),
            ("edit-editorconfig", edit(root, ".editorconfig", "root = true", "root = false"), (p(root, ".editorconfig"), "formatter")),
            ("edit-mypy", edit(root, "mypy.ini", "True", "False"), (p(root, "mypy.ini"), "type-checker")),
            ("edit-jest-config", edit(root, "jest.config.ts", "true", "false"), (p(root, "jest.config.ts"), "test-runner")),
            ("edit-pytest-ini", edit(root, "pytest.ini", "-q", "-q -p no:warnings"), (p(root, "pytest.ini"), "test-runner")),
            ("edit-tox", edit(root, "tox.ini", "py312", "py311"), (p(root, "tox.ini"), "test-runner")),
            ("edit-coveragerc", edit(root, ".coveragerc", "90", "0"), (p(root, ".coveragerc"), "test-runner")),
            ("edit-pre-commit", edit(root, ".pre-commit-config.yaml", "[]", "[1]"), (p(root, ".pre-commit-config.yaml"), "git hook")),
            ("edit-husky", edit(root, ".husky/pre-commit", "npm test", "true"), (p(root, ".husky/pre-commit"), "git hook")),
            ("edit-git-hook", edit(root, ".git/hooks/pre-commit", "npm test", "exit 0"), (p(root, ".git/hooks/pre-commit"), "git hook")),
            ("write-overwrite-eslintrc", write(root, ".eslintrc.json", "{}"), (p(root, ".eslintrc.json"), "lint")),
            ("multiedit-prettierrc", multi(root, ".prettierrc"), (p(root, ".prettierrc"), "formatter")),
            ("forward-slash-path", payload("Edit", root, file_path=fwd + "/.eslintrc.json", old_string="a", new_string="b"), (fwd + "/.eslintrc.json", "lint")),
            ("relative-path", payload("Edit", root, file_path=".eslintrc.json", old_string="a", new_string="b"), (".eslintrc.json", "lint")),
            # --- criterion 2: new files and unrelated files stay silent ---
            ("write-new-eslintrc", write(root, "fresh/.eslintrc.json", "{}"), None),
            ("write-new-jest-config", write(root, "jest.config.js", "module.exports = {};"), None),
            ("write-new-husky-hook", write(root, ".husky/pre-push", "npm test"), None),
            ("edit-source", edit(root, "src/app.ts", "1", "2"), None),
            ("edit-readme-mentions-tools", edit(root, "README.md", "eslint", "eslint and prettier"), None),
            ("edit-hook-sample", edit(root, ".git/hooks/pre-commit.sample", "sh", "bash"), None),
            ("edit-near-miss-names", edit(root, "notes-jest.config.md", "notes", "n"), None),
            ("edit-no-leading-dot", edit(root, "eslintrc.md", "notes", "n"), None),
            ("notebook-edit", payload("NotebookEdit", root, notebook_path=p(root, ".eslintrc.json"), new_source="x"), None),
            ("read-tool", payload("Read", root, file_path=p(root, ".eslintrc.json")), None),
            # --- criterion 3: pyproject.toml ---
            ("pyproject-ruff-inside-section", edit(root, "pyproject.toml", "ignore = []", 'ignore = ["F401"]'), (p(root, "pyproject.toml"), "tool config")),
            ("pyproject-pytest-addopts", edit(root, "pyproject.toml", 'addopts = "-q"', 'addopts = "-q -x"'), (p(root, "pyproject.toml"), "tool config")),
            ("pyproject-remove-section", edit(root, "pyproject.toml", '[tool.pytest.ini_options]\naddopts = "-q"\n', ""), (p(root, "pyproject.toml"), "tool config")),
            ("pyproject-dependency", edit(root, "pyproject.toml", '"requests>=2",', '"requests>=2.31",'), None),
            ("pyproject-name", edit(root, "pyproject.toml", 'name = "demo"', 'name = "demo2"'), None),
            ("pyproject-write-deps-only", write(root, "pyproject.toml", PYPROJECT.replace("requests>=2", "requests>=3")), None),
            ("pyproject-write-drops-ruff", write(root, "pyproject.toml", PYPROJECT.split("[tool.ruff]")[0]), (p(root, "pyproject.toml"), "tool config")),
            ("pyproject-plain-adds-ruff", edit(root, "plain/pyproject.toml", 'name = "plain"\n', 'name = "plain"\n\n[tool.ruff]\nignore = ["E501"]\n'), None),
            ("pyproject-crlf-tool-edit", edit(root, "crlf/pyproject.toml", 'select = ["E", "F"]\nignore = []', 'select = ["E"]\nignore = []'), (p(root, "crlf/pyproject.toml"), "tool config")),
            ("pyproject-crlf-deps-multiline", edit(root, "crlf/pyproject.toml", 'dependencies = [\n    "requests>=2",', 'dependencies = [\n    "requests>=3",'), None),
            # --- criterion 3: setup.cfg and Cargo.toml ---
            ("setupcfg-flake8", edit(root, "setup.cfg", "max-line-length = 100", "max-line-length = 200"), (p(root, "setup.cfg"), "tool config")),
            ("setupcfg-metadata", edit(root, "setup.cfg", "name = demo", "name = demo2"), None),
            ("cargo-lints", edit(root, "Cargo.toml", 'unsafe_code = "forbid"', 'unsafe_code = "allow"'), (p(root, "Cargo.toml"), "tool config")),
            ("cargo-dependency", edit(root, "Cargo.toml", 'serde = "1"', 'serde = "1.0.200"'), None),
            # --- criterion 3: package.json ---
            ("package-jest-block", edit(root, "package.json", '"testTimeout": 5000', '"testTimeout": 60000'), (p(root, "package.json"), "tool config")),
            ("package-test-script", edit(root, "package.json", '"test": "jest"', '"test": "jest --passWithNoTests"'), (p(root, "package.json"), "tool config")),
            ("package-lint-colon-script", edit(root, "package.json", '"lint:fix": "eslint . --fix"', '"lint:fix": "echo ok"'), (p(root, "package.json"), "tool config")),
            ("package-replace-all-reaches-jest", edit(root, "package.json", "true", "false", replace_all=True), (p(root, "package.json"), "tool config")),
            ("package-old-string-missing", edit(root, "package.json", '"nope": 1', '"nope": 2'), (p(root, "package.json"), "tool config")),
            ("package-multiedit", multi(root, "package.json"), (p(root, "package.json"), "tool config")),
            ("package-write-drops-jest", write(root, "package.json", PACKAGE.split(',\n  "jest"')[0] + "\n}\n"), (p(root, "package.json"), "tool config")),
            ("package-build-script", edit(root, "package.json", '"build": "tsc"', '"build": "tsc -p ."'), None),
            ("package-add-dev-script", edit(root, "package.json", '"build": "tsc",', '"build": "tsc",\n    "dev": "vite",'), None),
            ("package-bump-jest-dependency", edit(root, "package.json", '"jest": "^29.0.0"', '"jest": "^29.7.0"'), None),
            ("package-bump-lint-staged-dependency", edit(root, "package.json", '"lint-staged": "^15.0.0"', '"lint-staged": "^15.2.0"'), None),
            ("package-write-rename", write(root, "package.json", PACKAGE.replace('"demo"', '"demo2"')), None),
            ("package-plain-adds-test-script", edit(root, "plain/package.json", '"build": "tsc"', '"build": "tsc",\n    "test": "vitest"'), None),
            ("package-plain-old-string-missing", edit(root, "plain/package.json", '"nope": 1', '"nope": 2'), None),
            ("package-plain-multiedit", multi(root, "plain/package.json"), None),
            # --- criterion 3: tsconfig ---
            ("tsconfig-strict-off", edit(root, "tsconfig.json", '"strict": true', '"strict": false'), (p(root, "tsconfig.json"), "tool config")),
            ("tsconfig-drop-no-unused", edit(root, "tsconfig.json", ',\n    "noUnusedLocals": true', ""), (p(root, "tsconfig.json"), "tool config")),
            ("tsconfig-build-variant", edit(root, "tsconfig.build.json", '"strict": true', '"strict": false'), (p(root, "tsconfig.build.json"), "tool config")),
            ("tsconfig-target", edit(root, "tsconfig.json", '"ES2022"', '"ES2023"'), None),
            ("tsconfig-plain-adds-strict", edit(root, "plain/tsconfig.json", '"target": "ES2022"', '"target": "ES2022",\n    "strict": false'), None),
        ]
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
