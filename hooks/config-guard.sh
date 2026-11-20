#!/bin/sh
# DevTeam config guard (PreToolUse hook).
#
# Why: the cheapest way to make a failing lint, format, type or test check pass
# is to change the check instead of the code, or to commit with --no-verify.
# CLAUDE.md forbids both, but it is a prompt rule; this hook is the mechanical
# floor under it, the way money-gate.sh is under the money rule. It never
# approves and never denies: it asks, because the user may well have asked for
# the change. Spec: docs/specs/config-guard.md.
#
# What asks: Write/Edit/MultiEdit on an EXISTING guarded config file (a new one
# passes, so scaffolds are not interrupted); a change to the tool-config part of
# a shared file (package.json, pyproject.toml, setup.cfg, Cargo.toml,
# tsconfig); a shell write, move or delete of an existing guarded file; and a
# git hook bypass (--no-verify, commit -n, core.hooksPath, HUSKY=0, SKIP=,
# skipped signing).
#
# Contract: reads the PreToolUse JSON on stdin, prints one compact decision JSON
# or nothing, always exits 0. Ordinary calls are dismissed with shell builtins
# only (no process starts, which costs tens of ms each on Windows); the slow
# path is one awk process running config-guard.awk next to this file.
#
# Known limits: see the spec's Assumptions (case-sensitive names, no shell
# edits of shared files, no writes from inside interpreters or via variables).

set -f
case $0 in */*|*\\*) here=${0%[/\\]*} ;; *) here=. ;; esac

# The guarded basenames: the single source for both the builtin fast path and
# the awk slow path. Keep in step with the criterion-1 table in the spec (the
# names test reads that table).
LINT='.eslintrc .eslintrc.* eslint.config.* .eslintignore .stylelintrc .stylelintrc.* stylelint.config.* .oxlintrc.json biome.json biome.jsonc .flake8 .pylintrc pylintrc ruff.toml .ruff.toml .rubocop.yml .golangci.yml .golangci.yaml .golangci.toml .golangci.json clippy.toml .clippy.toml .shellcheckrc .swiftlint.yml .clang-tidy .markdownlint.json .markdownlint.yaml .markdownlint.yml .markdownlint.jsonc .markdownlintrc phpstan.neon phpstan.neon.dist phpcs.xml phpcs.xml.dist'
FORMAT='.prettierrc .prettierrc.* prettier.config.* .prettierignore .editorconfig .clang-format rustfmt.toml .rustfmt.toml .isort.cfg dprint.json .dprint.json .scalafmt.conf .php-cs-fixer.php .php-cs-fixer.dist.php'
TYPES='mypy.ini .mypy.ini pyrightconfig.json'
TESTS='jest.config.* vitest.config.* vitest.workspace.* playwright.config.* cypress.config.* karma.conf.* .mocharc .mocharc.* ava.config.* pytest.ini tox.ini .coveragerc .nycrc .nycrc.* .c8rc .c8rc.* phpunit.xml phpunit.xml.dist'
HOOKCFG='.pre-commit-config.yaml lefthook.yml lefthook.yaml .lefthook.yml .lintstagedrc .lintstagedrc.* lint-staged.config.*'
SHARED='pyproject.toml setup.cfg Cargo.toml package.json tsconfig.json tsconfig.*.json jsconfig.json'
TABLE="lint $LINT
formatter $FORMAT
type-checker $TYPES
test-runner $TESTS
git_hook $HOOKCFG
shared $SHARED"

WHY_CFG='loosening a lint, format, type or test setting can make a failing check pass without fixing the code'
WHY_HOOK='git hooks run the checks a commit must pass, so changing or removing them can let a failing commit through'
WHY_SKIP='the hooks run the checks (lint, tests, secret scans) a commit or push must pass, so skipping them lets a failing change through'
WHY_SIGN='the repository expects signed commits, and an unsigned commit cannot be verified as coming from you'

# Read stdin with the read builtin (a `cat` would cost a process on every call).
input=
while IFS= read -r line || [ -n "$line" ]; do input="$input$line"; done

# ask LABEL SUBJECT WHAT WHY   (SUBJECT is still JSON-escaped)
ask() {
  subject=$2
  if [ "${#subject}" -gt 160 ]; then
    subject=$(printf '%.160s' "$subject")
    # Never leave a JSON escape half-open: drop a cut \uXXXX, then lone backslashes.
    case "$subject" in *\\u|*\\u?|*\\u??|*\\u???) subject=${subject%\\u*} ;; esac
    while :; do
      case "$subject" in *\\) subject=${subject%\\} ;; *) break ;; esac
    done
    subject="$subject..."
  fi
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"DevTeam config guard. %s: `%s`. What it does: %s. Why it matters: %s. Approve only if you asked for this change; otherwise deny and ask Claude why it did it."}}\n' \
    "$1" "$subject" "$3" "$4"
  exit 0
}

# value KEY -> the raw (escaped) string value of the first "KEY":"..." in the
# payload, cut at the next quote; empty when absent or not a string.
value() {
  case "$input" in
    *"\"$1\":\""*) v=${input#*\"$1\":\"} ;;
    *"\"$1\": \""*) v=${input#*\"$1\": \"} ;;
    *) v=; return ;;
  esac
  v=${v%%\"*}
}

# classify BASENAME PATH -> sets cat (category, "shared" or empty) and shape.
classify() {
  cat=; shape=
  case "$1" in *.sample) return ;; esac
  for g in $LINT; do case "$1" in $g) cat=lint; return ;; esac; done
  for g in $FORMAT; do case "$1" in $g) cat=formatter; return ;; esac; done
  for g in $TYPES; do case "$1" in $g) cat=type-checker; return ;; esac; done
  for g in $TESTS; do case "$1" in $g) cat=test-runner; return ;; esac; done
  for g in $HOOKCFG; do case "$1" in $g) cat='git hook'; return ;; esac; done
  case "$1" in
    pyproject.toml) cat=shared; shape=pyproject; return ;;
    setup.cfg) cat=shared; shape=setupcfg; return ;;
    Cargo.toml) cat=shared; shape=cargo; return ;;
    package.json) cat=shared; shape=pkg; return ;;
    tsconfig.json|tsconfig.*.json|jsconfig.json) cat=shared; shape=ts; return ;;
  esac
  case "$2" in
    .husky[\\/]*|*[\\/].husky[\\/]*|.git[\\/]hooks[\\/]*|*[\\/].git[\\/]hooks[\\/]*|*.git\\\\hooks\\\\*) cat='git hook' ;;
  esac
}

case "$input" in
  *'"tool_name":"Bash"'*|*'"tool_name": "Bash"'*|*'"tool_name":"PowerShell"'*|*'"tool_name": "PowerShell"'*) tool=shell ;;
  *'"tool_name":"Write"'*|*'"tool_name": "Write"'*) tool=Write ;;
  *'"tool_name":"Edit"'*|*'"tool_name": "Edit"'*) tool=Edit ;;
  *'"tool_name":"MultiEdit"'*|*'"tool_name": "MultiEdit"'*) tool=MultiEdit ;;
  *) exit 0 ;;
esac

if [ "$tool" != shell ]; then
  value file_path; path=$v
  [ -n "$path" ] || exit 0
  base=${path##*/}; base=${base##*\\}
  [ -n "$base" ] || exit 0
  classify "$base" "$path"
  [ -n "$cat" ] || exit 0
  case "$path" in
    /*|[A-Za-z]:*|\\\\*) full=$path ;;
    *) value cwd; if [ -n "$v" ]; then full="$v/$path"; else full=$path; fi ;;
  esac
  [ -e "$full" ] || exit 0
  if [ "$cat" != shared ]; then
    if [ "$cat" = 'git hook' ]; then why=$WHY_HOOK; else why=$WHY_CFG; fi
    ask File "$path" "changes existing $cat config" "$why"
  fi
  verdict=$(printf '%s' "$input" | CG_MODE=shared CG_FILE="$full" CG_SHAPE="$shape" CG_TOOL="$tool" awk -f "$here/config-guard.awk")
  [ "$verdict" = ask ] && ask File "$path" 'changes the tool config (lint, format, type or test settings) in this file' "$WHY_CFG"
  exit 0
fi

# Shell: dismiss with builtins unless the command names a guarded file or a
# bypass word. The text after "command": may run into later fields; a stray
# match there only costs the slow path, which reads the command field alone.
case "$input" in
  *'"command":"'*) rest=${input#*\"command\":\"} ;;
  *'"command": "'*) rest=${input#*\"command\": \"} ;;
  *) exit 0 ;;
esac
slow=
case "$rest" in
  *no-verify*|*[Hh][Oo][Oo][Kk][Ss][Pp][Aa][Tt][Hh]*|*HUSKY*|*LEFTHOOK*|*SKIP=*|*gpg*|*commit*|*.husky*|*hooks*) slow=1 ;;
esac
if [ -z "$slow" ]; then
  for g in $LINT $FORMAT $TYPES $TESTS $HOOKCFG; do
    core=${g%%\**}
    case "$rest" in *"$core"*) slow=1; break ;; esac
  done
fi
[ -n "$slow" ] || exit 0

res=$(printf '%s' "$input" | CG_MODE=shell CG_TABLE="$TABLE" awk -f "$here/config-guard.awk")
[ -n "$res" ] || exit 0
tab=$(printf '\t')
kind=${res%%"$tab"*}; res=${res#*"$tab"}
what=${res%%"$tab"*}; seg=${res#*"$tab"}
if [ "$kind" = B ]; then
  case "$what" in *signing*) why=$WHY_SIGN ;; *) why=$WHY_SKIP ;; esac
else
  case "$what" in *'git hook'*) why=$WHY_HOOK ;; *) why=$WHY_CFG ;; esac
fi
ask Command "$seg" "$what" "$why"
