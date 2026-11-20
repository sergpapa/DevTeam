# Money gate: precise matches and prompts a person can decide from

## Why
On 2026-11-20 four background-subagent commands raised the money-gate prompt. Each one only read or downloaded other repos' files; the trigger was the text `.github/workflows` appearing anywhere in the command (a URL, a regex filter, a list of paths to fetch). The prompt then said "this touches .github/workflows, a standing charge that bills on the first push. Write the file and leave it unpushed", which named no command, implied the command itself cost money, and was written to Claude rather than to the person approving it. The user could not tell what they were approving.

## Acceptance criteria
1. **CI config rule fires only on writes.** A Bash/PowerShell command asks only when one of its command segments writes a CI workflow path (`.github/workflows` with `/` or `\`):
   - redirection into the path (`>`, `>>`, heredoc into the path);
   - `tee` onto the path;
   - `mkdir` / `touch` / `New-Item` naming the path;
   - `cp` / `mv` / `install` / `ln` / `Copy-Item` / `Move-Item` whose **destination** (last argument, or `-Destination`) is the path;
   - `sed -i` / `sed --in-place` on the path;
   - `curl` / `wget` / `Invoke-WebRequest` writing output to the path (`-o`, `-O`, `--output`, `--output-document`, `--output-dir`, `-P`, `--directory-prefix`, `-OutFile`, with or without a space before the path);
   - `Set-Content` / `Add-Content` / `Out-File` naming the path;
   - `git add` / `git mv` / `git commit` / `git checkout` / `git restore` naming the path (checkout and restore rewrite the file's contents, so they write CI config too; the prompt calls them free by itself).
   - `install` counts only as the first word of a segment, so `pip install -r .github/workflows/x.txt` is a read.
2. **Reads never ask.** `cat`, `grep` (including `grep -o`), `ls`, `Get-Content`, `-match` filters, `curl` to stdout or to a non-workflow file, and copying a file *out of* a workflows folder produce no decision. URLs are stripped from a segment before the CI rule looks at it.
3. **Matching is per segment.** The command is split on `;`, `&`, `|` and newlines. `--dry-run` exempts only the segment it is in, so `git push --dry-run && git push origin main` asks.
4. **Paid model API rule fires only on a network call.** It asks when a segment that runs `curl`, `wget`, `http`/`https` (HTTPie), `Invoke-RestMethod`/`irm` or `Invoke-WebRequest`/`iwr` targets a metered model API host, or when a full `https://` URL to such a host appears anywhere in the command and any segment runs one of those clients (a URL held in a variable, or a request body that splits the segment). A `grep` that mentions the bare host does not ask.
5. **Every prompt is decidable on its own.** The reason contains, in this order:
   - `Command: \`<segment>\`` (the matching segment, trimmed, at most 160 characters) for shell tools, or `File: \`<path>\`` for Write/Edit;
   - `What it does: ...` in plain words;
   - `Cost: <class> - <meter, account, and when it would bill>`, where `<class>` is exactly one of: `bills now`, `can bill now`, `bills later`, `free by itself`, `no charge, but public and permanent`;
   - a closing line telling the person to approve only if they asked for exactly this.
   - The quoted segment is measured in its JSON-escaped form. If it is longer than 160 characters it is cut at 160, any trailing backslashes are dropped (so no escape is left half-open), and `...` is appended.
   - When several segments or rules match, the prompt shows the most expensive one, ranked `bills now` > `can bill now` > `bills later` > `no charge, but public and permanent` > `free by itself`; ties go to the leftmost segment.
   - The output is compact JSON: `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"..."}}`.
6. **Output stays valid JSON** for any command text, including quotes, backslashes, tabs, and non-ASCII, and the hook always exits 0. Empty, `{}`, or malformed stdin produces no output.
   - Before splitting, line continuations (a backslash or PowerShell backtick before a newline) are joined with one space, and `&`, `;` and `|` inside a **quoted** URL are replaced with `%26`, `%3B` and `%7C`, so a quoted query string never splits a command. A quoted segment may therefore show `%26` where the command had `&`. In an unquoted URL these characters are real shell separators and do split.
   - A command word may carry a path (`/usr/bin/git`, `C:\...\gh.exe`), a `.exe` or `.cmd` suffix, a closing quote, or sit inside `( )`, `$( )` or backticks; matching ignores case.
   - Only the `command` field (shell tools) or `file_path` field (Write/Edit/MultiEdit/NotebookEdit) is examined; a `description` or any other field never triggers a match. Other tools (Read, Grep, ...) produce no output.
7. **All existing true positives still ask** (push, gh workflow/run/pr, CI config writes via Write/Edit, deploy and provisioning CLIs, package publishing, paid model API calls); `vercel dev` and `wrangler dev` still pass.
8. **A local regression suite** (`sh tests/money-gate.test.sh`) covers every rule as must-ask with its cost class and fragment, every known false positive as must-not-ask, and the four real 2026-11-20 commands (local paths removed) as fixtures that must not ask. It needs only `sh` plus `node` or `python` for the JSON validity check.

## Cost classes
| Rule | Class | Why |
|---|---|---|
| `git push` | can bill now | bills only if the branch has armed workflows |
| `gh workflow run`, `gh run rerun` | bills now | starts a run |
| `gh workflow enable` | bills later | arms future runs |
| `gh pr create`, `gh pr merge` | can bill now | starts pull_request / base-branch workflows if armed |
| CI config write (shell or Write/Edit) | free by itself | the file costs nothing until pushed |
| deploy / provision | bills now | provider compute, build minutes, egress |
| package publish | no charge, but public and permanent | outward-facing and hard to undo, not metered |
| paid model API call | bills now | per-token charge on the key used |

## Assumptions
- A write to a workflow path in any directory asks, including scratch folders: a false ask on a real write costs one click and is rare.
- Writes made from inside an interpreter (`python -c "open(...)"`, `node -e`) or through shell variables (`for p in ...; do curl -o "$p"`) are not detected. The Write/Edit rule covers the normal way Claude writes files.
- The hook still never approves and never denies; it only asks.
- Heredoc bodies are checked line by line like commands, so a heredoc whose text mentions `git push` asks. Fixing it needs heredoc-tag tracking beyond `sed`; the error is on the safe side, and Claude writes files with the Write tool. Recorded after the second review.
- A destination path containing a space is not recognised.

## Out of scope
- The other ten slices in `docs/roadmap.md`.
- Changing which commands count as billable (no new rules, no removed rules beyond the narrowing above).

## Slice log
- 2026-11-20: spec written from the false-positive incident; user approved the fix.
- 2026-11-20: test-guardian PRE failed the first suite (missing rule coverage); suite grown to 195 cases; decisions added for ranking, truncation, URL handling.
- 2026-11-20: /code-review round 1 found continuation, glued-separator, unicode-escape truncation, case, .exe and tool_name gaps; 24 cases added; one expected value (cont-api-backslash) corrected with user approval.
- 2026-11-20: /code-review round 2 found API-URL-in-variable, quoted-URL, wrapped-vercel, subshell, install and download-flag gaps; 18 cases added. Refused: heredoc body handling (known limit above). Kept: git checkout/restore as CI writes, because they do rewrite the file.
