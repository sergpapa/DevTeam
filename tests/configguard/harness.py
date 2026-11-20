"""Shared harness for the config-guard tests (docs/specs/config-guard.md).

Why a real temporary project: the hook's answer depends on whether a config
file already exists and on what is in it, so every case runs against files on
disk, not mocks. Cases run the real hook through `sh`, in parallel, because
each process start costs a noticeable fraction of a second on Windows.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, "hooks", "config-guard.sh")
SPEC = os.path.join(ROOT, "docs", "specs", "config-guard.md")
SH = shutil.which("sh")
if SH is None:
    raise RuntimeError("config-guard tests need `sh` on PATH (Git for Windows provides it)")
PREFIX = '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"'
CLOSING = "Approve only if you asked for this change; otherwise deny and ask Claude why it did it."

PYPROJECT = """[project]
name = "demo"
dependencies = [
    "requests>=2",
]

[tool.poetry]
packages = []

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F"]
ignore = []

[tool.pytest.ini_options]
addopts = "-q"

[build-system]
requires = ["hatchling"]
"""

PACKAGE = """{
  "name": "demo",
  "private": true,
  "eslintConfig": {
    "extends": "eslint:recommended"
  },
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "pretest": "tsc",
    "testing": "node t.js",
    "lint:fix": "eslint . --fix",
    "format": "prettier --check .",
    "format-docs": "mdfmt",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "eslint": "^9.0.0",
    "jest": "^29.0.0",
    "lint-staged": "^15.0.0"
  },
  "prettier": {
    "semi": false
  },
  "husky": {
    "hooks": {}
  },
  "lint-staged": {
    "*.ts": "eslint"
  },
  "jest": {
    "collectCoverage": true,
    "testTimeout": 5000
  }
}
"""

TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2022",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUncheckedIndexedAccess": true,
    "skipLibCheck": false,
    "checkJs": true,
    "allowUnreachableCode": false,
    "noUnusedLocals": true
  },
  "include": ["strict-src"]
}
"""


def reindent(text, unit):
    """Re-indent 2-space JSON with another indent unit (4 spaces, a tab)."""
    return re.sub(r"(?m)^((?:  )+)", lambda m: unit * (len(m.group(1)) // 2), text)


FILES = {
    ".eslintrc.json": '{ "rules": { "no-unused-vars": "error" } }\n',
    "sub/eslint.config.mjs": "export default [];\n",
    "biome.json": '{ "linter": { "enabled": true } }\n',
    ".prettierrc": '{ "semi": true }\n',
    ".editorconfig": "root = true\n",
    "mypy.ini": "[mypy]\nstrict = True\n",
    "jest.config.ts": "export default { bail: true };\n",
    "pytest.ini": "[pytest]\naddopts = -q\n",
    "tox.ini": "[tox]\nenvlist = py312\n",
    ".coveragerc": "[report]\nfail_under = 90\n",
    ".pre-commit-config.yaml": "repos: []\n",
    ".husky/pre-commit": "npm test\n",
    ".husky/_/husky.sh": "#!/bin/sh\n",
    ".git/hooks/pre-commit": "#!/bin/sh\nnpm test\n",
    ".git/hooks/pre-commit.sample": "#!/bin/sh\n",
    "script.sh": "#!/bin/sh\n",
    "src/app.ts": "export const x = 1;\n",
    "README.md": "Run eslint and jest.\n",
    "notes-jest.config.md": "notes\n",
    "eslintrc.md": "notes\n",
    "notes.txt": "notes\n",
    "pyproject.toml": PYPROJECT,
    "plain/pyproject.toml": '[project]\nname = "plain"\n',
    "crlf/pyproject.toml": PYPROJECT.replace("\n", "\r\n"),
    "setup.cfg": ("[metadata]\nname = demo\n\n[flake8]\nmax-line-length = 100\n\n"
                  "[coverage:run]\nbranch = True\n\n[options]\npackages = find:\n"),
    "Cargo.toml": ('[package]\nname = "demo"\nversion = "0.1.0"\n\n[dependencies]\nserde = "1"\n\n'
                   '[lints.rust]\nunsafe_code = "forbid"\n\n[profile.release]\nlto = true\n'),
    "package.json": PACKAGE,
    "pkg4/package.json": reindent(PACKAGE, "    "),
    "pkgtab/package.json": reindent(PACKAGE, "\t"),
    "plain/package.json": '{\n  "name": "plain",\n  "scripts": {\n    "build": "tsc"\n  }\n}\n',
    "tsconfig.json": TSCONFIG,
    "tsconfig.build.json": TSCONFIG,
    "jsconfig.json": '{\n  "compilerOptions": {\n    "checkJs": true\n  }\n}\n',
    "plain/tsconfig.json": '{\n  "compilerOptions": {\n    "target": "ES2022"\n  }\n}\n',
}


def make_project(files=None):
    """Create a temporary project and return its absolute path (native separators)."""
    root = tempfile.mkdtemp(prefix="cfgguard-")
    for rel, text in (FILES if files is None else files).items():
        path = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    return root


def payload(tool, cwd, **tool_input):
    """A PreToolUse payload as Claude Code sends it (UTF-8, not \\u-escaped)."""
    return json.dumps({"session_id": "t", "hook_event_name": "PreToolUse", "cwd": cwd,
                       "tool_name": tool, "tool_input": tool_input}, ensure_ascii=False)


def run_hook(stdin, env=None):
    """Run the hook once; return (returncode, stdout, stderr) as text."""
    proc = subprocess.run([SH, HOOK], input=stdin.encode("utf-8"), capture_output=True,
                          env=env, timeout=60)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def run_all(stdins):
    """Run many payloads in parallel; results come back in input order."""
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(run_hook, stdins))


def reason_of(out):
    return json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]


class GuardCase(unittest.TestCase):
    """Assertions shared by the config-guard test modules."""

    def assert_silent(self, result, name):
        rc, out, err = result
        self.assertEqual(rc, 0, f"{name}: hook exited {rc}; stderr: {err}")
        self.assertEqual(out, "", f"{name}: expected no decision, got: {out}")

    def assert_ask(self, result, name, label, subject, what):
        """label is File or Command; subject is the quoted text as the user sees it;
        what must appear as a whole word or phrase in the 'What it does' part."""
        rc, out, err = result
        self.assertEqual(rc, 0, f"{name}: hook exited {rc}; stderr: {err}")
        line = out.rstrip("\n")
        self.assertNotIn("\n", line, f"{name}: output is not one line: {out!r}")
        self.assertTrue(line.startswith(PREFIX) and line.endswith('"}}'),
                        f"{name}: expected a compact ask decision, got: {out or '<nothing>'}")
        reason = reason_of(line)
        head = "DevTeam config guard. "
        self.assertTrue(reason.startswith(head), f"{name}: {reason}")
        quoted = f"{label}: `{subject}`. "
        self.assertTrue(reason[len(head):].startswith(quoted), f"{name}: expected {quoted!r} first: {reason}")
        i_what = reason.find("What it does: ")
        i_why = reason.find("Why it matters: ")
        i_end = len(reason) - len(CLOSING)
        self.assertEqual(i_what, len(head) + len(quoted), f"{name}: 'What it does:' must follow the subject: {reason}")
        self.assertTrue(i_what < i_why < i_end, f"{name}: needs What, then Why, then the closing line: {reason}")
        self.assertTrue(reason.endswith(" " + CLOSING), f"{name}: must end with the closing line: {reason}")
        why = reason[i_why + len("Why it matters: "):i_end].strip()
        self.assertGreater(len(why), 20, f"{name}: 'Why it matters' is empty or a stub: {reason}")
        what_text = reason[i_what:i_why]
        self.assertRegex(what_text, r"(?<![\w-])" + re.escape(what) + r"(?![\w-])",
                         f"{name}: 'What it does' lacks {what!r}: {reason}")
