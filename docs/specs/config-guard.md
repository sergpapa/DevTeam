# Config guard: a prompt before Claude loosens the checks

## Why
The cheapest way to make a failing lint, format, type or test check pass is to change the check, not the code: add an ignore to `.eslintrc.json`, drop a rule from `[tool.ruff]`, set `"test": "echo ok"`, or commit with `--no-verify`. CLAUDE.md forbids this, but CLAUDE.md is a prompt rule and holds only while the model remembers it. This hook is the mechanical floor under it, the same way the money gate is under the money rule. Source: roadmap M1 slice 4, from the 2026-11-20 comparison (ECC's config-protection hook).

## Decisions (user, 2026-11-20)
- **Ask, never deny.** The hook only ever returns a permission prompt; the user approves when they asked for the change.
- **Existing files only.** Writing a config file that does not exist yet passes silently, so `/project` scaffolds are not interrupted. Changing, overwriting, moving or deleting an existing one asks.
- **Shared files ask only when the tool-config part changes.** Adding a dependency to `package.json` stays silent; changing `[tool.ruff]` asks.
- **Shell writes count** in the common forms, not only the Write/Edit tools.

## Acceptance criteria
1. **Guarded files, matched by basename in any directory** (exact, case-sensitive names; `*` is any suffix):

   | Category | Files |
   |---|---|
   | lint | `.eslintrc`, `.eslintrc.*`, `eslint.config.*`, `.eslintignore`, `.stylelintrc`, `.stylelintrc.*`, `stylelint.config.*`, `.oxlintrc.json`, `biome.json`, `biome.jsonc`, `.flake8`, `.pylintrc`, `pylintrc`, `ruff.toml`, `.ruff.toml`, `.rubocop.yml`, `.golangci.yml`, `.golangci.yaml`, `.golangci.toml`, `.golangci.json`, `clippy.toml`, `.clippy.toml`, `.shellcheckrc`, `.swiftlint.yml`, `.clang-tidy`, `.markdownlint.json`, `.markdownlint.yaml`, `.markdownlint.yml`, `.markdownlint.jsonc`, `.markdownlintrc`, `phpstan.neon`, `phpstan.neon.dist`, `phpcs.xml`, `phpcs.xml.dist` |
   | formatter | `.prettierrc`, `.prettierrc.*`, `prettier.config.*`, `.prettierignore`, `.editorconfig`, `.clang-format`, `rustfmt.toml`, `.rustfmt.toml`, `.isort.cfg`, `dprint.json`, `.dprint.json`, `.scalafmt.conf`, `.php-cs-fixer.php`, `.php-cs-fixer.dist.php` |
   | type-checker | `mypy.ini`, `.mypy.ini`, `pyrightconfig.json` |
   | test-runner | `jest.config.*`, `vitest.config.*`, `vitest.workspace.*`, `playwright.config.*`, `cypress.config.*`, `karma.conf.*`, `.mocharc`, `.mocharc.*`, `ava.config.*`, `pytest.ini`, `tox.ini`, `.coveragerc`, `.nycrc`, `.nycrc.*`, `.c8rc`, `.c8rc.*`, `phpunit.xml`, `phpunit.xml.dist` |
   | git hook | `.pre-commit-config.yaml`, `lefthook.yml`, `lefthook.yaml`, `.lefthook.yml`, `.lintstagedrc`, `.lintstagedrc.*`, `lint-staged.config.*`, any file inside a `.husky` folder, any file inside `.git/hooks` except `*.sample` |

2. **Write, Edit or MultiEdit on a guarded file asks when the file already exists**, and is silent when it does not. NotebookEdit and every other tool produce no output. The path is `tool_input.file_path`, absolute or relative to the payload's `cwd`, with `/` or `\` separators.
3. **Shared files ask only when their tool-config part changes.** For these files the hook computes the file's tool-config lines before and after the call (for Edit: the file with `old_string` replaced by `new_string`, every occurrence when `replace_all` is true; for Write: `content`). It asks when the file exists, the *before* set is not empty, and *before* differs from *after*. An Edit whose `old_string` is not found in the file, or any MultiEdit, asks when the *before* set is not empty.

   | File | Tool-config lines |
   |---|---|
   | `pyproject.toml` | every line in a section whose header starts with `[tool.ruff`, `[tool.black`, `[tool.isort`, `[tool.pytest`, `[tool.mypy`, `[tool.pylint`, `[tool.coverage`, `[tool.pyright`, `[tool.flake8`, `[tool.tox`, `[tool.pydocstyle`, `[tool.bandit`, header included |
   | `setup.cfg` | every line in a section whose header starts with `[flake8`, `[tool:pytest`, `[mypy`, `[isort`, `[pycodestyle`, `[pydocstyle`, `[coverage:`, `[pylint`, header included |
   | `Cargo.toml` | every line in a `[lints` or `[workspace.lints` section, header included |
   | `package.json` | every line of a top-level `eslintConfig`, `prettier`, `stylelint`, `jest`, `ava`, `mocha`, `nyc`, `c8`, `lint-staged`, `husky` or `vitest` block; and each line inside the top-level `scripts` block whose key is `test`, `lint`, `format` or `typecheck`, alone or followed by `:<anything>` (`test:unit`) |
   | `tsconfig.json`, `tsconfig.*.json`, `jsconfig.json` | each line whose key is `strict`, starts with `strict`, `noImplicit`, `noUnused`, `noUnchecked`, or is `noFallthroughCasesInSwitch`, `noPropertyAccessFromIndexSignature`, `exactOptionalPropertyTypes`, `useUnknownInCatchVariables`, `alwaysStrict`, `skipLibCheck`, `checkJs`, `allowUnreachableCode`, `allowUnusedLabels` |

   A top-level `package.json` key is one at the indentation of the file's first key. Blank lines are ignored in the comparison; any other change inside the set (a value, a reorder, a comment) counts. The file is read with carriage returns removed, so an `old_string` with `\n` line breaks is found in a CRLF file.

4. **Hook bypasses ask** (Bash or PowerShell, any segment of the command):
   - any `git` command carrying `--no-verify`;
   - `git commit` whose short-flag cluster contains `n` before any flag that takes an argument (`-n`, `-an`, `-anm "msg"`; but `-mn` is a message, not a bypass);
   - `git -c core.hooksPath=...` on any command, and `git config` that sets or unsets `core.hooksPath` (reading it with no value, or with `--get`, is silent);
   - `HUSKY=0` or `LEFTHOOK=0` set in the command, in any letter case (`VAR=0 git ...`, `export VAR=0`, PowerShell `$env:VAR = '0'` or `$env:var=0`; Windows environment names ignore case): what it does is `turns off the hook runner`. `HUSKY=1` is silent;
   - `SKIP=<hooks>` placed before a `git` command, or exported in an earlier segment (`export [NAME=v ...] SKIP=...`, a bare `export SKIP`, `declare -x SKIP=...`, `$env:SKIP=...`) of a command that later runs `git` (the pre-commit framework skips the named hooks): what it does is `skips the repository's git hooks`, and the prompt quotes the segment that sets it;
   - skipped signing: `--no-gpg-sign`, or `-c commit.gpgsign=false`.

   `git` may be called by a quoted name or path (`"git"`, `& "C:\Program Files\Git\cmd\git.exe" commit`), and global options before the subcommand may take a separate value (`-C`, `-c`, `--git-dir`, `--work-tree`, `--namespace`, `--config-env`). `git config unset core.hooksPath` (Git 2.46+) counts like `--unset`. `;`, `&` and `|` inside quotes do not split a command into segments; a backslash-escaped quote (`\"`, `\'`) does not open or close a quote. Because an apostrophe in a comment or heredoc body (`# don't`) is not shell quoting, every command is also checked split without regard to quotes, and it asks if either view matches (the quote-aware view is reported first). The flag rules apply only to a segment that runs `git`, and `-n` only to `git commit` (`git push -n` is a dry run). `--no-gpg-sign` and `commit.gpgsign=false|0|no|off` count; `commit.gpgsign=true` is silent. The flag rules (`--no-verify`, `-n`, `hooksPath`, signing) ignore text inside single or double quotes, so `git commit -m "fix -n and --no-verify docs"` is silent. The variable rules read a quoted value right after `=` (`$env:HUSKY = '0'` asks) but ignore other quoted text (`git commit -m "explain husky=0"` is silent). `SKIP=1 npm test` is silent: no `git` follows it.
5. **Shell writes to an existing guarded file ask** (the same categories as criterion 1; shared files are out of scope for shell, see Assumptions). A segment counts when a guarded path token is:
   - the target of `>` or `>>`;
   - an argument of `tee`, of `sed` / `perl` run with an in-place flag (`-i`, `-i.bak`, `--in-place`, `-pi`), of `truncate`, of `Set-Content` / `Add-Content` / `Out-File` / `Clear-Content` / `New-Item`;
   - the last argument of `cp`, `install` or `ln` (redirects such as `2>/dev/null` or `< /dev/null` are not arguments), or the `-Destination` of `Copy-Item`;
   - any argument of `mv`, `git mv`, `Move-Item`, `ren`, `rename` (moving a config away turns it off);
   - any argument of `rm`, `del`, `erase`, `unlink`, `Remove-Item`, `git rm`;
   - the output file of `curl` / `wget` / `Invoke-WebRequest`: the token after `-o`, `--output`, `--output-document`, `-OutFile`, or wget's `-O`, or the value of `--output=` / `--output-document=`. curl's `-O` (save under the remote name) names no local path and is not counted;
   - an argument of `chmod` when the path is inside `.git/hooks` or `.husky`.

   Surrounding single or double quotes on a token are ignored, `>` needs no spaces around it (`echo x>.eslintrc.json`), and tokens may use `/` or `\`. A shared file (criterion 3) written from the shell is silent. A relative token is resolved against the payload's `cwd`. If an earlier segment of the same command changes directory (`cd`, `pushd`, `Set-Location`, `sl`), the file is assumed to exist and the hook asks. Reads (`cat`, `grep`, `Get-Content`, `cp .eslintrc.json backup/`) never ask.
6. **Every prompt is decidable on its own.** The output is one compact JSON line: `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"..."}}`. The reason reads, in this order:
   - `DevTeam config guard.`
   - `File: \`<path as given>\`` for file tools, or `Command: \`<segment>\`` for shell (trimmed; a subject over 160 bytes of JSON-escaped text is cut to at most 160 bytes, never inside a JSON escape or a UTF-8 character, and `...` is appended);
   - `What it does: ...` naming the category word from criterion 1 (`lint`, `formatter`, `type-checker`, `test-runner`, `git hook`), or `tool config` for a shared file, or for a bypass one of: `skips the repository's git hooks`, `points git at a different hooks folder`, `turns off the hook runner`, `skips commit signing`;
   - `Why it matters: ...` one sentence on how this can make a failing check pass without fixing the code;
   - `Approve only if you asked for this change; otherwise deny and ask Claude why it did it.`
   - The parts are joined exactly like the money gate: `DevTeam config guard. File: \`x\`. What it does: ... . Why it matters: ... . Approve only ...` (each part ends with `. `). The category word or bypass phrase appears as a whole word: `formatter` is the word, not `formatters`.
   - When a shell command matches several rules, a bypass wins over a file write; ties go to the leftmost segment.
7. **Output stays valid JSON** for any input, and the hook always exits 0. Empty, `{}`, or malformed stdin produces no output.
8. **Ordinary calls stay cheap.** A Write/Edit whose basename is not guarded or shared, and a shell command that names no guarded file and no bypass word, are dismissed by shell builtins alone: run with an empty `PATH`, the hook prints nothing on stdout or stderr.
9. **Wired and documented.** `hooks/hooks.json` registers `hooks/config-guard.sh` as a second `PreToolUse` hook (`type: command`, with a `timeout`) for `Bash|PowerShell|Write|Edit|MultiEdit`; the money gate's entry is unchanged. The script starts with `#!/bin/sh` and is committed executable (mode `100755`), because Claude Code runs it directly. The README describes the hook next to the money gate.
10. **A local test suite** (`tests/test_config_guard_*.py` with helpers in `tests/configguard/`, run by `python -m unittest discover -s tests`) covers every rule above as must-ask with its fragment, every listed non-case as must-not-ask, and works on Windows paths.

## Assumptions
- Basename matching is case-sensitive; a Windows checkout with `.ESLintrc.json` is not seen. Config files are lowercase by convention.
- Shell edits of shared files (`sed -i` on `pyproject.toml`, `npm pkg set`) are not checked: the hook cannot tell which part of the file they touch without running them.
- Writes from inside an interpreter (`python -c`, `node -e`), through shell variables, or to a path containing a space are not seen, as with the money gate.
- Vitest config inside `vite.config.*` is not guarded: telling its `test` block from build settings needs a JS parser.
- Minified (single-line) `package.json` has no indentation to find top-level keys from; its tool lines are not detected.
- Checking each command also with quotes ignored (criterion 4) has a known false positive: a quoted message that itself contains a separator and a guarded write or bypass (`git commit -m "a; rm .eslintrc.json"`) asks. It errs toward asking and is rare.
- An `old_string` with `\u` escapes (non-ASCII written as escapes) will usually not be found in the file and falls back to asking when the file has tool config. Claude Code sends UTF-8 unescaped, so this is rare and errs toward asking.

## Out of scope
- Deny mode, an on/off setting, or an allow-list.
- Test files themselves (test-guardian POST and slice 8 cover weakened tests).
- CI config (the money gate covers it).
- The other slices in `docs/roadmap.md`.

## Slice log
- 2026-11-20: spec written; the four forks answered by the user (ask, existing files only, shared files by tool-config part, shell writes included).
- 2026-11-20: test-guardian PRE failed the first suite (19 findings: most basenames and shell forms untested, no section-boundary or near-miss cases). Spec clarified: curl `-O` not counted, wget `-O` counted; `SKIP=` maps to "skips the repository's git hooks"; flag rules only on `git`; executable bit required. The basename test now reads the criterion-1 table from this file.
- 2026-11-20: test-guardian re-check PASS; 3 nits closed (joiner and whole-word rule written down, signing variants tested).
- 2026-11-20: implemented (`hooks/config-guard.sh` + `hooks/config-guard.awk`). One bug found by the suite: `$0` with only backslashes (a Windows path) lost the awk file's folder.
- 2026-11-20: /code-review (medium) found 9 important defects, all fixed test-first: a byte cut could split a UTF-8 character and make the output undecodable (the hook now runs with `LC_ALL=C` and trims a partial character); `;`/`&`/`|` inside a quoted message split the command and hid `-n`; a trailing `2>/dev/null` became the `cp` destination; lower-case `$env:husky`; `export SKIP=` in an earlier segment; `git --work-tree . commit -n`; `git` called by a quoted path; `git config unset`; `New-Item`/`Clear-Content`. The nit (missing doc comments in the awk file) is fixed too.
- 2026-11-20: second /code-review (medium) on the fixes found 4 important defects, all fixed test-first: an apostrophe in a comment or heredoc hid every later command (now each command is judged quote-aware and quote-blind); a backslash-escaped quote flipped quote state; bare `"git"`; `export CI=1 SKIP=x`, `declare -x SKIP`, bare `export SKIP`. Nits fixed: quoted prose such as `"explain husky=0"` no longer asks; `set SKIP=` dropped (it sets no environment variable in bash or PowerShell); the fast path no longer goes slow on any `skip` (`--skip-slow`); doc comments on `shell()` and `norm()`. Pre-existing gap fixed: `< /dev/null` no longer becomes the `cp` destination. Stopped after two review rounds: the remaining misses are recorded under Assumptions.
