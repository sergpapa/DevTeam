# Plugin self-tests: catch a broken skill before it ships

## Why
A skill whose frontmatter fails to parse loads with empty metadata and disappears from the skill list without an error. `/project` was dead this way until 2.0.3 because of an unquoted colon in its description. On 2026-11-20 `claude plugin validate .` was run on a copy with that same colon put back and with `adr`'s `name` changed to `adrx`: it printed `✔ Validation passed` for both. Nothing in the release flow catches either failure, nor a description that stopped matching how people ask for the skill, nor the double-encoded dash that shipped in the 2.0.3 README.

## Decisions (user, 2026-11-20)
- **Router:** a lexical ranker (BM25) over the skill descriptions plus a table of realistic prompts. No model calls.
- **Runtime:** Python standard library only. Frontmatter is checked against a strict YAML subset, not a YAML library.
- **Trigger phrase:** accept a set of phrasings; no description is rewritten to pass the check.
- **When it runs:** by hand, and as step 0 of the release flow next to `claude plugin validate .`. No git hook.

## Acceptance criteria
One command runs everything: `python -m unittest discover -s tests -v`. It exits 0 only if every check passes on the repo, uses only the standard library (Python 3.8+), makes no network or model calls, and the repo check plus router finish in under 5 seconds (the full suite, with its throwaway git repos, takes about 8 to 12 seconds on Windows). Every failure line names the file (and line where there is one) and says what to change.

1. **Strict frontmatter** on `skills/*/SKILL.md`, `agents/*.md` and `output-styles/*.md`:
   - Line 1 is exactly `---` and a later line is exactly `---`. CRLF line endings are accepted. A UTF-8 BOM before line 1 fails.
   - Every line between them is `key: value`. A key is `[A-Za-z][A-Za-z0-9_-]*`. Blank lines are allowed. An indented line, a comment line, a duplicate key, or a line with no `: ` fails.
   - A value is one of:
     - double-quoted: `"..."` filling the whole value; the only escapes allowed inside are `\"` and `\\`;
     - single-quoted: `'...'` filling the whole value; `''` is the only escape;
     - plain: non-empty; does not start with any of ``- ? : , [ ] { } # & * ! | > ' " % @ ` ``; does not contain a colon followed by a space or tab or ` #`; does not end with `:`.
   - An empty value fails. A plain `name` or `description` that YAML loads as null, a boolean or a number (`null`, `~`, `true`, `123`, `.inf`) fails; other keys may hold booleans.
   - `name` and `description` are required in all three kinds of file.
   - The failure for a plain value containing `: ` says to wrap the value in double quotes.
2. **Name matches its file.** A skill's `name` equals its directory name; an agent's `name` equals its file name without `.md`. A skill name is lowercase `[a-z0-9-]+`, at most 64 characters. Output styles are exempt (`Plain` lives in `plain.md`).
3. **Skill descriptions say when to use them.** Each skill description contains, as whole words and ignoring case, one of: `use when`, `use whenever`, `use for`, `use before`, `use after`, `invoke before`. "Abuse whenever" does not count. Each description is at most 1,024 characters (characters, not bytes).
4. **Size cap.** Each `skills/*/SKILL.md` is at most 20,480 bytes (bytes, not characters). The failure shows the actual size. Files under `references/` are not capped.
5. **Encoding.** Every text file git knows about or would add (`git ls-files --cached --others --exclude-standard`) decodes as UTF-8, has no BOM, and contains no mojibake. Binary files (any NUL byte) and tracked files deleted from disk are skipped. If git cannot list the files (not a repo, git missing), the check raises `RuntimeError`. It never returns an empty list, because that would read as a pass. Mojibake is a run of 2 to 4 characters that, encoded as Windows-1252 (Latin-1 for the five bytes 1252 leaves undefined), forms one valid multi-byte UTF-8 character, such as U+00E2 U+20AC U+201D (three characters) where `—` was meant. The failure gives file, line, the bad run, and the character it should be. A two-character run counts only when it decodes to Latin, Greek or Cyrillic (U+0080-U+027F, U+0370-U+04FF), so a letter before a curly quote or an ellipsis in German or French is not flagged. Ordinary accented text (`café`, `naïve`, `Ångström`) does not fail.
6. **Router.** `tests/router/cases.tsv` holds `prompt<TAB>expected` rows. `expected` is a skill name, or several names joined by `|` when either is a correct route.
   - Each skill document is its `name` plus its `description`. The ranker lowercases, splits on anything that is not a letter or digit, drops a fixed stopword list, applies light suffix stripping, and scores with BM25.
   - A case routes when an expected skill scores strictly higher than every other skill; a tie or an all-zero ranking does not route. There is no score threshold and no `none` case (see the slice record). A row whose third column is `miss` is a known misroute: it fails if it starts to route, so it gets promoted rather than silently kept.
   - At least 2 single-skill cases per skill, and near-miss pairs: debug vs feature, discover vs project, tdd vs feature, adopt vs project, hygiene vs debug. A test pins the first sentence of every eval prompt as a case.
   - Cases are written the way a person asks. They do not copy a description's own trigger words.
   - A failing case prints the prompt, the expected skill, and the top 3 skills with their scores.
7. **Each check is proven to catch its bug.** Unit tests feed every check a known-bad input and assert the failure, and a known-good input and assert no failure. This includes the real 2.0.3 colon, a `name` that does not match its folder, a 20,481-byte skill, and a double-encoded em dash. Mojibake samples are written as `\u` escapes so the test source stays ASCII and does not trip the encoding check.
8. **The repo passes.** If a check finds a real problem in the current repo, the problem gets fixed in this slice. A router case is never fixed by deleting or rewording it, except where the user approved it (the `none` rows and threshold, recorded in the slice record). If a reasonable prompt routes wrong, the case stays red and goes to the user.
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
- 2026-11-20, green: the first run of the real router misrouted 7 of 30 cases, and no threshold separated routed from `none` prompts. One generic verb scores the same either way: "Write a haiku" scored 2.42 for tdd, while the correct "Add a retry button" route scored 2.35. Dropping one-letter tokens (debris such as the "s" in "user's") fixed 1 of the 7. The user then decided two things:
  - Five descriptions gain the words people use. debug gains "randomly" and "no idea why". adr gains "write down why one option was picked over another". adopt gains "no docs or tests" and "get a codebase ready before adding features". project gains "from scratch (planning and building it across sessions)". tdd gains "adding", "unit tests" and "failing tests first, then the implementation". The 2026-10-08 eval baseline is no longer directly comparable for these five skills.
  - The threshold and the 8 `none` rows are removed. Telling "write a haiku" from "write tests" takes reading intent, so quiet-prompt checks move to the slice 11 evals.
- 2026-11-20, test changes after PRE: the threshold and `none` removal above (user-approved), and `core.autocrlf false` in the temp-repo setup so the machine's global git config cannot print warnings or change the bytes under test. No assertion was weakened.
- 2026-11-20, verify: on a copy of the repo with five breaks, the suite failed with one line for each. The breaks were the real 2.0.3 colon, `adr` renamed `adrx`, a double-encoded em dash in README, hygiene padded to 23,064 bytes, and tdd's trigger words removed. `claude plugin validate .` printed `✔ Validation passed` on the same copy.
- 2026-11-20, review. test-guardian POST passed: the only test changes since the red commit are the approved ones, and the ranker is not tuned to the case prompts. It noted that 4 of the description additions reuse the case wording. /code-review found 3 important defects, all fixed test-first:
  - A tie passed in alphabetical order. A case now routes only when it strictly outscores every other skill.
  - The mojibake check flagged German text such as a sharp s before a closing quote. Two-byte runs now count only when they decode to Latin, Greek or Cyrillic. Known remaining miss: a capital A-umlaut before a closing quote is still flagged.
  - A colon followed by a tab passed the frontmatter check. It is now rejected.
  Nits fixed:
  - `name` and `description` values that YAML loads as null, a boolean or a number are rejected.
  - load_skills keys skills by directory and raises on frontmatter that does not parse.
  - The stemmer now matches use/used/using/uses and keeps "speed", "string" and "need" whole.
  - Criterion 8 now points at the approved removals.
  For the copied-wording nit, 5 held-out prompts were added that avoid the added words: 3 route correctly, 2 miss. The tie rule also exposed the CSV-export feature case (feature and retro both at 1.71). The user chose to keep these 3 as expected-miss rows (`miss` column) instead of another round of description edits. One of the 2 misses, the tdd prompt, is caused by this slice's adopt edit ("no docs or tests" now competes for "tests").
