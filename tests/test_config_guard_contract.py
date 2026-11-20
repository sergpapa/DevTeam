"""Config guard, hook contract (docs/specs/config-guard.md criteria 6-9).

Pins what Claude Code relies on regardless of the rules: the output is valid
JSON or nothing, the hook always exits 0, a long subject is cut on the escaped
text without leaving a broken escape, ordinary calls start no external
program, and hooks.json plus the executable bit make Claude Code run it.
"""
import json
import os
import shutil
import subprocess
import unittest

from configguard.harness import GuardCase, HOOK, ROOT, SH, make_project, payload, reason_of, run_all, run_hook


def quoted_subject(out):
    return reason_of(out).split("Command: `", 1)[1].split("`. What it does: ", 1)[0]


class Contract(GuardCase):
    @classmethod
    def setUpClass(cls):
        cls.root = make_project()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_malformed_input_is_silent(self):
        cases = ["", "{}", "not json", '{"tool_name":"Edit"}', '{"tool_name":"Bash","tool_input":{}}',
                 '{"tool_name":"Bash","tool_input":{"command":5}}',
                 '{"tool_name":"Edit","tool_input":{"file_path":null}}']
        for stdin, result in zip(cases, run_all(cases)):
            with self.subTest(stdin):
                self.assert_silent(result, repr(stdin))

    def test_any_input_gives_valid_json_or_nothing(self):
        r = self.root
        cases = [payload("Bash", r, command="rm .eslintrc.json\r\nls"),
                 payload("Bash", r, command="echo \x07\x1b[0m > .eslintrc.json"),
                 payload("Edit", r, file_path=os.path.join(r, 'we"ird\\.eslintrc.json'), old_string="a", new_string="b"),
                 payload("Edit", r, file_path=os.path.join(r, 'a"b', ".eslintrc.json"), old_string="a", new_string="b"),
                 json.dumps({"tool_name": "Edit", "tool_input": {"file_path": ".eslintrc.json", "old_string": "a", "new_string": "b"}})]
        for i, (rc, out, err) in enumerate(run_all(cases)):
            with self.subTest(i):
                self.assertEqual(rc, 0, err)
                if out:
                    json.loads(out)

    def test_awkward_text_still_gives_valid_json(self):
        cmd = "sed -i 's/\"a\\\\b\"\t/ü/' .eslintrc.json"
        result = run_hook(payload("Bash", self.root, command=cmd))
        self.assert_ask(result, "awkward", "Command", cmd, "lint")

    def test_cut_at_160_boundaries(self):
        tail = " > .eslintrc.json"
        exact = "echo " + "x" * (160 - 5 - len(tail)) + tail
        over = "echo " + "x" * (161 - 5 - len(tail)) + tail
        (_, out_exact, _), (_, out_over, _) = run_all([payload("Bash", self.root, command=exact),
                                                      payload("Bash", self.root, command=over)])
        self.assertEqual(quoted_subject(out_exact), exact)
        self.assertEqual(quoted_subject(out_over), over[:160] + "...")

    def test_cut_never_splits_an_escape(self):
        for filler in ('\\', '"', "\x01"):
            for pad in range(4):
                cmd = "echo " + "y" * pad + filler * 120 + " > .eslintrc.json"
                with self.subTest(filler=repr(filler), pad=pad):
                    rc, out, err = run_hook(payload("Bash", self.root, command=cmd))
                    self.assertEqual(rc, 0, err)
                    subject = quoted_subject(out)
                    self.assertTrue(subject.endswith("..."), subject)
                    shown = subject[:-3]
                    self.assertTrue(cmd.startswith(shown), "the cut text must be a prefix of the command")
                    self.assertLessEqual(len(json.dumps(shown, ensure_ascii=False)) - 2, 160)

    def test_cut_never_splits_a_utf8_character(self):
        # Found by /code-review: a byte cut inside a multibyte character made the
        # output undecodable, so Claude Code dropped the decision.
        for n in range(4):  # shift where byte 160 lands relative to the 2-byte letters
            d = os.path.join(self.root, "u" + "p" * n, "αβγδεζηθ" * 10)
            os.makedirs(d, exist_ok=True)
            target = os.path.join(d, ".eslintrc.json")
            with open(target, "w", encoding="utf-8") as f:
                f.write("{}\n")
            # LC_ALL=C: Claude Code may run hooks with no UTF-8 locale, where printf counts bytes.
            proc = subprocess.run([SH, HOOK], input=payload("Write", self.root, file_path=target, content="x").encode("utf-8"),
                                  capture_output=True, timeout=60, env=dict(os.environ, LC_ALL="C"))
            with self.subTest(n=n):
                self.assertEqual(proc.returncode, 0)
                out = proc.stdout.decode("utf-8")  # strict: invalid UTF-8 raises here
                subject = reason_of(out).split("File: `", 1)[1].split("`. What it does: ", 1)[0]
                self.assertTrue(subject.endswith("..."), subject)
                self.assertTrue(target.startswith(subject[:-3]), "the cut text must be a prefix of the path")

    def test_ordinary_calls_use_builtins_only(self):
        env = dict(os.environ, PATH="")
        r = self.root
        cases = [payload("Bash", r, command="npm test"),
                 payload("Bash", r, command="git status"),
                 payload("Bash", r, command="pytest -k smoke --skip-slow"),
                 payload("PowerShell", r, command="Get-ChildItem src"),
                 payload("Write", r, file_path=os.path.join(r, "src", "new.ts"), content="x"),
                 payload("Edit", r, file_path=os.path.join(r, "README.md"), old_string="Run", new_string="Use"),
                 payload("Read", r, file_path=os.path.join(r, ".eslintrc.json"))]
        for i, stdin in enumerate(cases):
            with self.subTest(i):
                rc, out, err = run_hook(stdin, env=env)
                self.assertEqual((rc, out, err), (0, "", ""), "a fast-path call started an external program")

    def test_hooks_json_wiring(self):
        with open(os.path.join(ROOT, "hooks", "hooks.json"), encoding="utf-8") as f:
            groups = json.load(f)["hooks"]["PreToolUse"]
        flat = [(g["matcher"], h) for g in groups for h in g["hooks"]]
        money = [(m, h) for m, h in flat if h["command"].endswith("/hooks/money-gate.sh")]
        guard = [(m, h) for m, h in flat if h["command"].endswith("/hooks/config-guard.sh")]
        self.assertEqual(money, [("Bash|PowerShell|Write|Edit|MultiEdit|NotebookEdit",
                                  {"type": "command", "command": '"${CLAUDE_PLUGIN_ROOT}"/hooks/money-gate.sh', "timeout": 10})])
        self.assertEqual(len(guard), 1, "config-guard.sh must be registered exactly once")
        matcher, hook = guard[0]
        self.assertEqual(matcher, "Bash|PowerShell|Write|Edit|MultiEdit")
        self.assertEqual(hook["type"], "command")
        self.assertEqual(hook["command"], '"${CLAUDE_PLUGIN_ROOT}"/hooks/config-guard.sh')
        self.assertIsInstance(hook.get("timeout"), int)

    def test_script_is_executable_sh(self):
        with open(HOOK, encoding="utf-8") as f:
            self.assertEqual(f.readline().rstrip("\r\n"), "#!/bin/sh")
        staged = subprocess.run(["git", "ls-files", "-s", "hooks/config-guard.sh"], cwd=ROOT,
                                capture_output=True, text=True).stdout
        self.assertTrue(staged.startswith("100755 "), f"hooks/config-guard.sh must be tracked as 100755, got: {staged!r}")

    def test_readme_documents_the_hook(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertRegex(text, r"(?im)^#+ .*config[- ]guard")
        self.assertIn("hooks/config-guard.sh", text)


if __name__ == "__main__":
    unittest.main()
