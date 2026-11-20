"""Config guard, shell tools (docs/specs/config-guard.md criteria 4-6).

Bypass cases pin each way a commit can skip the repository's hooks; write cases
pin each shell form that changes, moves or deletes an existing config file;
the silent cases pin reads, new files, shared files, and look-alikes (a flag
on a non-git command, a guarded name that is not the write target) that must
not interrupt. Contract tests live in test_config_guard_contract.py.
"""
import shutil
import unittest

from configguard.harness import GuardCase, make_project, payload, run_all

SKIPS = "skips the repository's git hooks"
HOOKS_PATH = "points git at a different hooks folder"
RUNNER_OFF = "turns off the hook runner"
SIGNING = "skips commit signing"


def bypass_cases(bash, pwsh):
    return [
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
        ("husky-powershell-bare", pwsh("$env:HUSKY=0; git push"), ("$env:HUSKY=0", RUNNER_OFF)),
        ("lefthook-zero", bash("LEFTHOOK=0 git push"), ("LEFTHOOK=0 git push", RUNNER_OFF)),
        ("pre-commit-skip", bash("SKIP=ruff,mypy git commit -m x"), ("SKIP=ruff,mypy git commit -m x", SKIPS)),
        ("no-gpg-sign", bash("git commit --no-gpg-sign -m x"), ("git commit --no-gpg-sign -m x", SIGNING)),
        ("gpgsign-false", bash("git -c commit.gpgsign=false commit -m x"), ("git -c commit.gpgsign=false commit -m x", SIGNING)),
        ("gpgsign-0", bash("git -c commit.gpgsign=0 commit -m x"), ("git -c commit.gpgsign=0 commit -m x", SIGNING)),
        ("gpgsign-no", bash("git -c commit.gpgsign=no commit -m x"), ("git -c commit.gpgsign=no commit -m x", SIGNING)),
        ("gpgsign-off", bash("git -c commit.gpgsign=off commit -m x"), ("git -c commit.gpgsign=off commit -m x", SIGNING)),
        ("bypass-beats-write", bash("rm .eslintrc.json && git commit --no-verify -m x"), ("git commit --no-verify -m x", SKIPS)),
        ("two-bypasses-leftmost", bash("git commit --no-verify -m x && git push --no-verify"), ("git commit --no-verify -m x", SKIPS)),
        # look-alikes
        ("commit-message-mentions-flags", bash('git commit -m "fix -n and --no-verify docs"'), None),
        ("commit-message-single-quoted", bash("git commit -m 'x --no-verify'"), None),
        ("commit-mn-is-a-message", bash("git commit -mn"), None),
        ("git-log-n", bash("git log -n 5"), None),
        ("git-push-n-is-dry-run", bash("git push -n"), None),
        ("npm-no-verify", bash("npm publish --no-verify"), None),
        ("echo-no-verify", bash("echo --no-verify"), None),
        ("hookspath-read", bash("git config core.hooksPath"), None),
        ("hookspath-get", bash("git config --get core.hooksPath"), None),
        ("husky-one", bash("HUSKY=1 git commit -m x"), None),
        ("gpgsign-true", bash("git -c commit.gpgsign=true commit -m x"), None),
        ("skip-without-git", bash("SKIP=1 npm test"), None),
        ("plain-commit", bash('git commit -m "add feature"'), None),
    ]


def write_cases(bash, pwsh, root):
    fwd = root.replace("\\", "/")
    return [
        ("redirect-eslintrc", bash("echo '{}' > .eslintrc.json"), ("echo '{}' > .eslintrc.json", "lint")),
        ("redirect-no-spaces", bash("echo x>.eslintrc.json"), ("echo x>.eslintrc.json", "lint")),
        ("redirect-dot-slash", bash("echo x > ./.eslintrc.json"), ("echo x > ./.eslintrc.json", "lint")),
        ("append-prettierrc", bash("cat x >> .prettierrc"), ("cat x >> .prettierrc", "formatter")),
        ("tee-jest-config", bash("echo x | tee jest.config.ts"), ("tee jest.config.ts", "test-runner")),
        ("sed-inplace", bash("sed -i 's/error/off/' .eslintrc.json"), ("sed -i 's/error/off/' .eslintrc.json", "lint")),
        ("sed-inplace-backup", bash("sed -i.bak 's/90/0/' .coveragerc"), ("sed -i.bak 's/90/0/' .coveragerc", "test-runner")),
        ("sed-in-place-long", bash("sed --in-place 's/90/0/' .coveragerc"), ("sed --in-place 's/90/0/' .coveragerc", "test-runner")),
        ("perl-pi", bash("perl -pi -e 's/q/x/' pytest.ini"), ("perl -pi -e 's/q/x/' pytest.ini", "test-runner")),
        ("truncate-coveragerc", bash("truncate -s 0 .coveragerc"), ("truncate -s 0 .coveragerc", "test-runner")),
        ("cp-onto", bash("cp /tmp/loose.json .eslintrc.json"), ("cp /tmp/loose.json .eslintrc.json", "lint")),
        ("install-onto", bash("install -m 644 loose.json .prettierrc"), ("install -m 644 loose.json .prettierrc", "formatter")),
        ("ln-onto", bash("ln -sf loose.json .prettierrc"), ("ln -sf loose.json .prettierrc", "formatter")),
        ("copy-item-destination", pwsh("Copy-Item -Destination .prettierrc -Path loose.json"), ("Copy-Item -Destination .prettierrc -Path loose.json", "formatter")),
        ("mv-away", bash("mv .eslintrc.json .eslintrc.json.off"), ("mv .eslintrc.json .eslintrc.json.off", "lint")),
        ("git-mv", bash("git mv tox.ini tox.ini.old"), ("git mv tox.ini tox.ini.old", "test-runner")),
        ("move-item", pwsh("Move-Item .prettierrc old.prettierrc"), ("Move-Item .prettierrc old.prettierrc", "formatter")),
        ("ren", pwsh("ren mypy.ini mypy.off"), ("ren mypy.ini mypy.off", "type-checker")),
        ("rename", bash("rename .ini .off pytest.ini"), ("rename .ini .off pytest.ini", "test-runner")),
        ("rm-config", bash("rm .eslintrc.json"), ("rm .eslintrc.json", "lint")),
        ("rm-quoted", bash('rm ".eslintrc.json"'), ('rm ".eslintrc.json"', "lint")),
        ("rm-nested", bash("rm -f sub/eslint.config.mjs"), ("rm -f sub/eslint.config.mjs", "lint")),
        ("rm-absolute", bash(f"rm {fwd}/mypy.ini"), (f"rm {fwd}/mypy.ini", "type-checker")),
        ("del", pwsh("del .coveragerc"), ("del .coveragerc", "test-runner")),
        ("erase", pwsh("erase .coveragerc"), ("erase .coveragerc", "test-runner")),
        ("unlink", bash("unlink .editorconfig"), ("unlink .editorconfig", "formatter")),
        ("remove-item", pwsh("Remove-Item .prettierrc"), ("Remove-Item .prettierrc", "formatter")),
        ("remove-item-quoted", pwsh("Remove-Item '.prettierrc'"), ("Remove-Item '.prettierrc'", "formatter")),
        ("remove-item-windows-path", pwsh(f"Remove-Item {root}\\.prettierrc"), (f"Remove-Item {root}\\.prettierrc", "formatter")),
        ("git-rm", bash("git rm tox.ini"), ("git rm tox.ini", "test-runner")),
        ("set-content", pwsh("Set-Content -Path mypy.ini -Value x"), ("Set-Content -Path mypy.ini -Value x", "type-checker")),
        ("add-content", pwsh("Add-Content mypy.ini 'x'"), ("Add-Content mypy.ini 'x'", "type-checker")),
        ("out-file", pwsh("'x' | Out-File .editorconfig"), ("Out-File .editorconfig", "formatter")),
        ("curl-o", bash("curl -o .editorconfig https://example.com/ec"), ("curl -o .editorconfig https://example.com/ec", "formatter")),
        ("curl-output", bash("curl --output .editorconfig https://example.com/ec"), ("curl --output .editorconfig https://example.com/ec", "formatter")),
        ("wget-O", bash("wget -O .editorconfig https://example.com/ec"), ("wget -O .editorconfig https://example.com/ec", "formatter")),
        ("wget-output-document", bash("wget --output-document=.editorconfig https://example.com/ec"), ("wget --output-document=.editorconfig https://example.com/ec", "formatter")),
        ("iwr-outfile", pwsh("Invoke-WebRequest https://example.com/ec -OutFile .editorconfig"), ("Invoke-WebRequest https://example.com/ec -OutFile .editorconfig", "formatter")),
        ("chmod-git-hook", bash("chmod -x .git/hooks/pre-commit"), ("chmod -x .git/hooks/pre-commit", "git hook")),
        ("chmod-husky", bash("chmod +x .husky/pre-commit"), ("chmod +x .husky/pre-commit", "git hook")),
        ("cd-then-write", bash("cd sub && echo x > .stylelintrc"), ("echo x > .stylelintrc", "lint")),
        ("pushd-then-rm", bash("pushd sub; rm .stylelintrc"), ("rm .stylelintrc", "lint")),
        ("set-location-then-rm", pwsh("Set-Location sub; Remove-Item .stylelintrc"), ("Remove-Item .stylelintrc", "lint")),
        ("sl-then-rm", pwsh("sl sub; Remove-Item .stylelintrc"), ("Remove-Item .stylelintrc", "lint")),
        ("two-writes-leftmost", bash("rm .eslintrc.json && rm .prettierrc"), ("rm .eslintrc.json", "lint")),
        # reads, new files, shared files and near-misses stay silent
        ("redirect-new-file", bash("echo '{}' > .stylelintrc"), None),
        ("redirect-new-nested", bash("echo '{}' > fresh/.eslintrc.json"), None),
        ("rm-missing", bash("rm .stylelintrc"), None),
        ("mv-missing", bash("mv .stylelintrc x"), None),
        ("remove-item-missing", pwsh("Remove-Item missing/.prettierrc"), None),
        ("write-then-cd", bash("echo x > .stylelintrc && cd sub"), None),
        ("curl-remote-name", bash("curl -O https://example.com/.editorconfig"), None),
        ("cat-config", bash("cat .eslintrc.json"), None),
        ("grep-config", bash("grep rules .eslintrc.json"), None),
        ("sed-without-i", bash("sed 's/a/b/' .eslintrc.json"), None),
        ("name-not-the-target", bash("echo .eslintrc.json > notes.txt"), None),
        ("get-content", pwsh("Get-Content .prettierrc"), None),
        ("cp-out", bash("cp .eslintrc.json backup/"), None),
        ("rm-near-miss", bash("rm notes-jest.config.md"), None),
        ("redirect-near-miss", bash("echo x > eslintrc.md"), None),
        ("sed-shared-pyproject", bash("sed -i 's/100/200/' pyproject.toml"), None),
        ("redirect-shared-package", bash("echo x > package.json"), None),
        ("chmod-plain-script", bash("chmod +x script.sh"), None),
        ("chmod-hook-sample", bash("chmod +x .git/hooks/pre-commit.sample"), None),
        ("rm-hook-sample", bash("rm .git/hooks/pre-commit.sample"), None),
        ("run-eslint", bash("npx eslint ."), None),
        ("prettier-write-src", bash("npx prettier --write src"), None),
        ("npm-test", bash("npm test"), None),
    ]


class ShellCases(GuardCase):
    @classmethod
    def setUpClass(cls):
        root = cls.root = make_project()

        def bash(cmd):
            return payload("Bash", root, command=cmd)

        def pwsh(cmd):
            return payload("PowerShell", root, command=cmd)

        # (name, payload, expected): expected is None (silent) or (segment, what).
        cls.cases = bypass_cases(bash, pwsh) + write_cases(bash, pwsh, root)
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


if __name__ == "__main__":
    unittest.main()
