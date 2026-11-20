#!/bin/sh
# Regression suite for hooks/money-gate.sh.
#
# Why: the hook decides which tool calls interrupt the user with a money
# prompt. A miss lets a billable command run unasked; a false positive teaches
# the user to click through the prompt, and a prompt that does not say what is
# being approved cannot be answered at all. Each case pins one of those.
#
# Cases: tests/money-gate/cases.tsv (tab-separated: name, expect, cost-class,
# fragment, payload JSON). Fixtures: tests/money-gate/fixtures/allow-*.json are
# real commands that once raised a false prompt and must produce no decision.
#
# Run: sh tests/money-gate.test.sh   Exit 0 = every case passed.
# Needs sh, plus node or python for the JSON validity check.

here=$(cd "$(dirname "$0")" && pwd)
hook="$here/../hooks/money-gate.sh"
cases="$here/money-gate/cases.tsv"
fixtures="$here/money-gate/fixtures"
tab=$(printf '\t')
pass=0
fail=0

if command -v node >/dev/null 2>&1; then
  json_ok() { node -e 'JSON.parse(require("fs").readFileSync(0,"utf8"))' 2>/dev/null; }
elif command -v python3 >/dev/null 2>&1; then
  json_ok() { python3 -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; }
elif command -v python >/dev/null 2>&1; then
  json_ok() { python -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; }
else
  echo "FAIL: neither node nor python found; cannot check that the hook prints valid JSON" >&2
  exit 1
fi

bad() { fail=$((fail + 1)); printf 'FAIL %s: %s\n' "$1" "$2"; }

closing='Approve only if you asked for exactly this'

# run_case NAME EXPECT CLASS FRAGMENT PAYLOAD   (PAYLOAD "<empty>" = empty stdin)
run_case() {
  payload=$5
  [ "$payload" = '<empty>' ] && payload=''
  out=$(printf '%s' "$payload" | sh "$hook")
  rc=$?
  if [ "$rc" -ne 0 ]; then bad "$1" "hook exited $rc (must always exit 0)"; return; fi
  case "$2" in
    allow)
      if [ -n "$out" ]; then bad "$1" "expected no decision, got: $out"; return; fi
      pass=$((pass + 1)); return ;;
    ask) ;;
    *) bad "$1" "expect must be ask or allow, got '$2'"; return ;;
  esac
  case "$out" in
    '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"'*'"}}') ;;
    *) bad "$1" "expected a compact ask decision, got: ${out:-<nothing>}"; return ;;
  esac
  if ! printf '%s' "$out" | json_ok; then bad "$1" "output is not valid JSON: $out"; return; fi
  case "$out" in
    *"Command: \`$4\`"*|*"File: \`$4\`"*) ;;
    *) bad "$1" "reason does not quote the command or file as \`$4\`: $out"; return ;;
  esac
  case "$out" in
    *"\`$4\`"*"What it does: "*"Cost: $3 - "*"$closing"*) ;;
    *) bad "$1" "reason lacks, in order, 'What it does:', 'Cost: $3 - ', '$closing': $out"; return ;;
  esac
  pass=$((pass + 1))
}

if [ ! -r "$cases" ]; then
  echo "FAIL: case table $cases is missing or unreadable" >&2
  exit 1
fi

ran=0
while IFS="$tab" read -r name expect class frag payload; do
  case "$name" in ''|'#'*) continue ;; esac
  ran=$((ran + 1))
  run_case "$name" "$expect" "$class" "$frag" "$payload"
done < "$cases"

min_cases=150
if [ "$ran" -lt "$min_cases" ]; then
  bad "case-table" "only $ran cases ran from $cases (expected at least $min_cases); the table is truncated or misparsed"
fi

for f in "$fixtures"/allow-*.json; do
  [ -e "$f" ] || continue
  run_case "fixture:$(basename "$f" .json)" allow - - "$(cat "$f")"
done

printf '%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
