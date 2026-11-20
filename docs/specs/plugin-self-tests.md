# Plugin self-tests: catch a broken skill before it ships

## Why
A skill whose frontmatter fails to parse loads with empty metadata and disappears from the skill list without an error. `/project` was dead this way until 2.0.3 because of an unquoted colon in its description. On 2026-11-20 `claude plugin validate .` was run on a copy with that same colon put back and with `adr`'s `name` changed to `adrx`: it printed `✔ Validation passed` for both. Nothing in the release flow catches either failure, nor a description that stopped matching how people ask for the skill, nor the double-encoded dash that shipped in the 2.0.3 README.

## Decisions (user, 2026-11-20)
- **Router:** a lexical ranker (BM25) over the skill descriptions plus a table of realistic prompts. No model calls.
- **Runtime:** Python standard library only. Frontmatter is checked against a strict YAML subset, not a YAML library.
- **Trigger phrase:** accept a set of phrasings; no description is rewritten to pass the check.
- **When it runs:** by hand, and as step 0 of the release flow next to `claude plugin validate .`. No git hook.

## Acceptance criteria
One command runs everything: `python -m unittest discover -s tests -v`. It exits 0 only if every check passes on the repo, uses only the standard library (Python 3.8+), makes no network or model calls, and finishes in under 5 seconds. Every failure line names the file (and line where there is one) and says what to change.

1. **Strict frontmatter** on `skills/*/SKILL.md`, `agents/*.md` and `output-styles/*.md`:
   - Line 1 is exactly `---` and a later line is exactly `---`. CRLF line endings are accepted. A UTF-8 BOM before line 1 fails.
   - Every line between them is `key: value`. A key is `[A-Za-z][A-Za-z0-9_-]*`. Blank lines are allowed. An indented line, a comment line, a duplicate key, or a line with no `: ` fails.
   - A value is one of:
     - double-quoted: `"..."` filling the whole value; the only escapes allowed inside are `\"` and `\\`;
     - single-quoted: `'...'` filling the whole value; `''` is the only escape;
     - plain: non-empty; does not start with any of ``- ? : , [ ] { } # & * ! | > ' " % @ ` ``; does not contain `: ` or ` #`; does not end with `:`.
   - An empty value fails.
   - `name` and `description` are required in all three kinds of file.
   - The failure for a plain value containing `: ` says to wrap the value in double quotes.
2. **Name matches its file.** A skill's `name` equals its directory name; an agent's `name` equals its file name without `.md`. A skill name is lowercase `[a-z0-9-]+`, at most 64 characters. Output styles are exempt (`Plain` lives in `plain.md`).
3. **Skill descriptions say when to use them.** Each skill description contains, as whole words and ignoring case, one of: `use when`, `use whenever`, `use for`, `use before`, `use after`, `invoke before`. "Abuse whenever" does not count. Each description is at most 1,024 characters (characters, not bytes).
4. **Size cap.** Each `skills/*/SKILL.md` is at most 20,480 bytes (bytes, not characters). The failure shows the actual size. Files under `references/` are not capped.
5. **Encoding.** Every text file git knows about or would add (`git ls-files --cached --others --exclude-standard`) decodes as UTF-8, has no BOM, and contains no mojibake. Binary files (any NUL byte) and tracked files deleted from disk are skipped. If git cannot list the files (not a repo, git missing), the check raises `RuntimeError`. It never returns an empty list, because that would read as a pass. Mojibake is a run of 2 to 4 characters that, encoded as Windows-1252 (Latin-1 for the five bytes 1252 leaves undefined), forms one valid multi-byte UTF-8 character, such as `â€”` for `—`. The failure gives file, line, the bad run, and the character it should be. Ordinary accented text (`café`, `naïve`, `Ångström`) does not fail.
6. **Router.** `tests/router/cases.tsv` holds `prompt<TAB>expected` rows. `expected` is a skill name, several names joined by `|` when either is a correct route, or `none`.
   - Each skill document is its `name` plus its `description`. The ranker lowercases, splits on anything that is not a letter or digit, drops a fixed stopword list, applies light suffix stripping, and scores with BM25.
   - A routed case passes when its top-ranked skill is one of `expected` and that score is at or above the threshold. A `none` case passes when the top score is below the threshold. The threshold is one constant in the ranker.
   - At least 2 single-skill cases per skill, at least 5 `none` cases (some developer-adjacent, such as "What does git rebase do?"), and near-miss pairs: debug vs feature, discover vs project, tdd vs feature, adopt vs project, hygiene vs debug. A test pins the first sentence of every eval prompt as a case.
   - Cases are written the way a person asks. They do not copy a description's own trigger words.
   - A `none` case that only a reader of negation could get right is left out, and the reason is given. For example, "Fix the typo in the README" matches the "skip for typos" wording in feature and debug.
   - A failing case prints the prompt, the expected skill, and the top 3 skills with their scores.
7. **Each check is proven to catch its bug.** Unit tests feed every check a known-bad input and assert the failure, and a known-good input and assert no failure. This includes the real 2.0.3 colon, a `name` that does not match its folder, a 20,481-byte skill, and `â€”`. Mojibake samples are written as `\u` escapes so the test source stays ASCII and does not trip the encoding check.
8. **The repo passes.** If a check finds a real problem in the current repo, the problem gets fixed in this slice. A router case is never fixed by deleting or rewording it. If a reasonable prompt routes wrong, the case stays red and goes to the user.
9. **Docs.** README "Local development" gives the command, and a test pins it. The release flow gains the command as step 0.

## Slice record
- 2026-11-20, test-guardian PRE: FAIL. 1 wrong expectation (em-dash column 4, should be 5). 3 tests a wrong implementation would pass: IDF tie broken by dict order, 2 of 3 stemming asserts satisfiable without stemming, and character-vs-byte caps untested. Gaps: check_file on BOM/invalid UTF-8/CRLF, fence trailing space, tab indent, quoted empty value, multiple runs per file, check_repo on a non-repo, eval prompts not pinned, weak `none` cases. All were fixed before the red commit. The trigger rule is now whole-word in the spec. Router cases that copied description wording were replaced (edge, retro, project, the second slugify case), and the adopt near-miss now accepts `adopt|feature`. The README command is pinned by a test, but the release-flow step lives outside the repo and is not tested.

## Scope fence
- No skill description is edited unless criterion 8 forces it, and then only with the user's approval.
- No git hook, no CI workflow, no paid eval run.
- `tests/money-gate.test.sh` is unchanged and stays a separate command.
- `claude plugin validate .` stays in the release flow. This slice covers only what it misses.

## Assumptions (proposed defaults, not asked)
- Agents and output styles get the frontmatter parse and the name check, not the trigger or size checks. Agents are called by skills, not routed from prompts.
- The 1,024-character description cap and the lowercase-name rule follow the Agent Skills format. Every current skill already meets both.
- BOM and invalid UTF-8 count as encoding failures.
- Layout: the checker is a package at `tests/selfcheck/` (`frontmatter.py`, `checks.py`, `mojibake.py`, `router.py`). Unit tests are `tests/test_selfcheck_*.py`. The repo-wide run and the router run are test cases in `tests/test_repo.py`.
