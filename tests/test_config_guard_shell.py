"""Config guard, shell tools and the hook contract (docs/specs/config-guard.md criteria 4-9).

Bypass cases pin each way a commit can skip the repository's hooks; write cases
pin each shell form that changes, moves or deletes an existing config file;
the silent cases pin reads, new files, and look-alikes that must not interrupt.
The contract cases pin valid JSON, exit 0, the builtin-only fast path, and the
hooks.json wiring that makes Claude Code run the hook at all.
"""
import json
import os
import shutil
import unittest

from configguard.harness import GuardCase, HOOK, ROOT, SH, make_project, payload, run_all, run_hook

SKIPS = "skips the repository's git hooks"
HOOKS_PATH = "points git at a different hooks folder"
RUNNER_OFF = "turns off the hook runner"
SIGNING = "skips commit signing"


class ShellCases(GuardCase):
    @classmethod
    def setUpClass(cls):
        root = cls.root = make_project()
        fwd = root.replace("\\", "/")

        def bash(cmd):
            return payload("Bash", root, command=cmd)

        def pwsh(cmd):
            return payload("PowerShell", root, command=cmd)

        # (name, payload, expected) where expected is None (silent) or (segment, what).
        cls.cases = [
            # --- criterion 4: bypasses ---
            ("no-verify-commit", bash('git commit --no-verify -m "wip"'), ('git commit --no-verify -m "wip"', SKIPS)),
            ("no-verify-push", bash("git push --no-verify origin main"), ("git push --no-verify origin main", SKIPS)),
            ("no-verify-in-chain", bash('git add . && git commit -am "x" --no-verify'), ('git commit -am "x" --no-verify', SKIPS)),
            ("commit-dash-n", bash("git commit -n -m wip"), ("git commit -n -m wip", SKIPS)),
            ("commit-cluster-anm", bash('git commit -anm "wip"'), ('git commit -anm "wip"', SKIPS)),
            ("commit-dash-n-with-C", bash("git -C repo commit -n"), ("git -C repo commit -n", SKIPS)),
            ("hookspath-c", bash("git -c core.hooksPath=/dev/null commit -m x"), ("git -c core.hooksPath=/dev/null commit -m x", HOOKS_PATH)),
            ("hookspath-config-set", bash("git config core.hooksPath .nohooks"), ("git config core.hooksPath .nohooks", HOOKS_PATH)),
            ("hookspath-config-global", bash("git config --global core.hooksPath /tmp/none"), ("git config --global core.hooksPath /tmp/none", HOOKS_PATH)),
            ("hookspath-config-unset", bash("git config --unset core.hooksPath"), ("git config --unset core.hooksPath", HOOKS_PATH)),
            ("husky-zero-prefix", bash("HUSKY=0 git commit -m x"), ("HUSKY=0 git commit -m x", RUNNER_OFF)),
            ("husky-export", bash("export HUSKY=0 && git commit -m x"), ("export HUSKY=0", RUNNER_OFF)),
            ("husky-powershell", pwsh("$env:HUSKY = '0'; git commit -m x"), ("$env:HUSKY = '0'", RUNNER_OFF)),
            ("lefthook-zero", bash("LEFTHOOK=0 git push"), ("LEFTHOOK=0 git push", RUNNER_OFF)),
            ("pre-commit-skip", bash("SKIP=ruff,mypy git commit -m x"), ("SKIP=ruff,mypy git commit -m x", RUNNER_OFF)),
            ("no-gpg-sign", bash("git commit --no-gpg-sign -m x"), ("git commit --no-gpg-sign -m x", SIGNING)),
            ("gpgsign-false", bash("git -c commit.gpgsign=false commit -m x"), ("git -c commit.gpgsign=false commit -m x", SIGNING)),
            ("bypass-beats-write", bash("rm .eslintrc.json && git commit --no-verify -m x"), ("git commit --no-verify -m x", SKIPS)),
            # --- criterion 4: look-alikes stay silent ---
            ("commit-message-mentions-flags", bash('git commit -m "fix -n and --no-verify docs"'), None),
            ("commit-mn-is-a-message", bash("git commit -mn"), None),
            ("git-log-n", bash("git log -n 5"), None),
            ("hookspath-read", bash("git config core.hooksPath"), None),
            ("hookspath-get", bash("git config --get core.hooksPath"), None),
            ("skip-without-git", bash("SKIP=1 npm test"), None),
            ("plain-commit", bash('git commit -m "add feature"'), None),
            # --- criterion 5: shell writes to existing guarded files ---
            ("redirect-eslintrc", bash("echo '{}' > .eslintrc.json"), ("echo '{}' > .eslintrc.json", "lint")),
            ("append-prettierrc", bash("cat x >> .prettierrc"), ("cat x >> .prettierrc", "formatter")),
            ("tee-jest-config", bash("echo x | tee jest.config.ts"), ("tee jest.config.ts", "test-runner")),
            ("sed-inplace", bash("sed -i 's/error/off/' .eslintrc.json"), ("sed -i 's/error/off/' .eslintrc.json", "lint")),
            ("sed-inplace-backup", bash("sed -i.bak 's/90/0/' .coveragerc"), ("sed -i.bak 's/90/0/' .coveragerc", "test-runner")),
            ("perl-pi", bash("perl -pi -e 's/q/x/' pytest.ini"), ("perl -pi -e 's/q/x/' pytest.ini", "test-runner")),
            ("truncate-coveragerc", bash("truncate -s 0 .coveragerc"), ("truncate -s 0 .coveragerc", "test-runner")),
            ("cp-onto", bash("cp /tmp/loose.json .eslintrc.json"), ("cp /tmp/loose.json .eslintrc.json", "lint")),
            ("copy-item-destination", pwsh("Copy-Item loose.json -Destination .prettierrc"), ("Copy-Item loose.json -Destination .prettierrc", "formatter")),
            ("mv-away", bash("mv .eslintrc.json .eslintrc.json.off"), ("mv .eslintrc.json .eslintrc.json.off", "lint")),
            ("rm-config", bash("rm .eslintrc.json"), ("rm .eslintrc.json", "lint")),
            ("rm-nested", bash("rm -f sub/eslint.config.mjs"), ("rm -f sub/eslint.config.mjs", "lint")),
            ("rm-absolute", bash(f"rm {fwd}/mypy.ini"), (f"rm {fwd}/mypy.ini", "type-checker")),
            ("remove-item", pwsh("Remove-Item .prettierrc"), ("Remove-Item .prettierrc", "formatter")),
            ("git-rm", bash("git rm tox.ini"), ("git rm tox.ini", "test-runner")),
            ("set-content", pwsh("Set-Content -Path mypy.ini -Value x"), ("Set-Content -Path mypy.ini -Value x", "type-checker")),
            ("curl-output", bash("curl -o .editorconfig https://example.com/ec"), ("curl -o .editorconfig https://example.com/ec", "formatter")),
            ("chmod-git-hook", bash("chmod -x .git/hooks/pre-commit"), ("chmod -x .git/hooks/pre-commit", "git hook")),
            ("cd-then-write", bash("cd sub && echo x > .stylelintrc"), ("echo x > .stylelintrc", "lint")),
            # --- criterion 5: reads and new files stay silent ---
            ("redirect-new-file", bash("echo '{}' > .stylelintrc"), None),
            ("redirect-new-nested", bash("echo '{}' > fresh/.eslintrc.json"), None),
            ("cat-config", bash("cat .eslintrc.json"), None),
            ("grep-config", bash("grep rules .eslintrc.json"), None),
            ("get-content", pwsh("Get-Content .prettierrc"), None),
            ("cp-out", bash("cp .eslintrc.json backup/"), None),
            ("run-eslint", bash("npx eslint ."), None),
            ("prettier-write-src", bash("npx prettier --write src"), None),
            ("rm-hook-sample", bash("rm .git/hooks/pre-commit.sample"), None),
            ("npm-test", bash("npm test"), None),
        ]
        cls.results = run_all([c[1] for c in cls.cases])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_shell_cases(self):
        for (name, _, expected), result in zip(self.cases, self.results):
            with self.subTest(name):
                if expected is None:
                    self.assert_silent(result, name)
                else:
                    self.assert_ask(result, name, "Command", expected[0], expected[1])


class Contract(GuardCase):
    @classmethod
    def setUpClass(cls):
        cls.root = make_project()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_malformed_input_is_silent(self):
        cases = ["", "{}", "not json", '{"tool_name":"Edit"}', '{"tool_name":"Bash","tool_input":{}}']
        for stdin, result in zip(cases, run_all(cases)):
            with self.subTest(stdin):
                self.assert_silent(result, repr(stdin))

    def test_awkward_text_still_gives_valid_json(self):
        cmd = "sed -i 's/\"a\\\\b\"\t/ü/' .eslintrc.json"
        result = run_hook(payload("Bash", self.root, command=cmd))
        self.assert_ask(result, "awkward", "Command", cmd, "lint")

    def test_long_segment_is_cut_at_160(self):
        cmd = "echo " + "x" * 200 + " > .eslintrc.json"
        rc, out, _ = run_hook(payload("Bash", self.root, command=cmd))
        reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
        quoted = reason.split("Command: `", 1)[1].split("`", 1)[0]
        self.assertEqual(quoted, cmd[:160] + "...")

    def test_ordinary_calls_use_builtins_only(self):
        env = dict(os.environ, PATH="")
        cases = [payload("Bash", self.root, command="npm test"),
                 payload("PowerShell", self.root, command="Get-ChildItem src"),
                 payload("Write", self.root, file_path=os.path.join(self.root, "src", "new.ts"), content="x"),
                 payload("Edit", self.root, file_path=os.path.join(self.root, "README.md"), old_string="Run", new_string="Use"),
                 payload("Read", self.root, file_path=os.path.join(self.root, ".eslintrc.json"))]
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
        self.assertEqual(guard[0][0], "Bash|PowerShell|Write|Edit|MultiEdit")
        self.assertTrue(os.path.isfile(HOOK))

    def test_readme_documents_the_hook(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertRegex(text, r"(?im)^#+ .*config[- ]guard")
        self.assertIn("hooks/config-guard.sh", text)


if __name__ == "__main__":
    unittest.main()
