#!/bin/sh
# DevTeam money gate (PreToolUse hook).
#
# Why: the CLAUDE.md money rule is a prompt rule, so it holds only as long as the
# model remembers it. This hook is the mechanical floor under it: any tool call
# that can bill the user's account gets a permission prompt, even in auto mode.
# It never approves anything (silence = normal flow) and never denies outright,
# because the rule asks for explicit per-instance approval, which is exactly
# what the prompt is. Users who want a hard wall add a deny rule in settings.json.
#
# The prompt must be answerable on its own: it quotes the command segment (or
# file) that matched, says what it does, and classifies the cost as one of
# "bills now", "can bill now", "bills later", "no charge, but public and
# permanent", or "free by itself". When several segments match, the most
# expensive is shown. Spec: docs/specs/money-gate-precision.md.
#
# Contract: reads the PreToolUse JSON on stdin, prints one compact decision JSON
# or nothing, always exits 0. Needs only POSIX sh, grep -E, sed and tr, so it
# runs in Git Bash on Windows and /bin/sh on macOS and Linux. It runs on every
# shell call, and each external process costs tens of milliseconds on Windows,
# so most commands are dismissed by shell pattern matching alone.
#
# Known limits: writes made inside an interpreter (python -c, node -e), through
# shell variables, or to a quoted destination containing a space are not seen;
# the Write/Edit rule covers the normal way Claude writes files.

set -f   # no filename globbing: patterns below must never expand against the cwd
input=$(cat)

# One JSON string field, still JSON-escaped (so it can be echoed back into JSON).
field() {
  printf '%s' "$input" | tr -d '\n\r' \
    | sed -n -E 's/.*"'"$1"'"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p'
}

# mentions TEXT PATTERN... -> true if TEXT contains any glob PATTERN. Builtin
# only; the patterns are spelled with [Aa] classes so matching ignores case.
mentions() {
  t=$1; shift
  for w; do case "$t" in *$w*) return 0 ;; esac; done
  return 1
}

# ask LABEL SUBJECT WHAT CLASS DETAIL
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
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"DevTeam money gate. %s: `%s`. What it does: %s. Cost: %s - %s. Approve only if you asked for exactly this; otherwise deny and ask Claude why it ran it."}}\n' \
    "$1" "$subject" "$3" "$4" "$5"
  exit 0
}

CI_WHAT='writes CI/CD pipeline config'
CI_COST='writing the file costs nothing; it starts billing on the first push to a repository with CI enabled, then on every matching trigger (Actions or build minutes)'
WORKFLOWS='[Ww][Oo][Rr][Kk][Ff][Ll][Oo][Ww][Ss]'

case "$input" in
  *'"tool_name":"Bash"'*|*'"tool_name": "Bash"'*|*'"tool_name":"PowerShell"'*|*'"tool_name": "PowerShell"'*) kind=shell ;;
  *'"tool_name":"Write"'*|*'"tool_name": "Write"'*|*'"tool_name":"Edit"'*|*'"tool_name": "Edit"'*|\
  *'"tool_name":"MultiEdit"'*|*'"tool_name": "MultiEdit"'*|*'"tool_name":"NotebookEdit"'*|*'"tool_name": "NotebookEdit"'*) kind=file ;;
  *'"tool_name"'*)
    # Unusual spacing: fall back to a real parse (costs processes, so only here).
    case "$(field tool_name)" in
      Bash|PowerShell) kind=shell ;;
      Write|Edit|MultiEdit|NotebookEdit) kind=file ;;
      *) exit 0 ;;
    esac ;;
  *) exit 0 ;;
esac

if [ "$kind" = file ]; then
  mentions "$input" "$WORKFLOWS" '[Gg]itlab-ci' '[Cc]ircleci' '[Jj]enkinsfile' '[Aa]zure-pipelines' \
    '[Bb]itbucket-pipelines' '[Bb]uildkite' '[Tt]ravis' '[Cc]loudbuild' || exit 0
  path=$(field file_path)
  if printf '%s' "$path" | grep -q -i -E '(^|[\\/])(\.github[\\/]+workflows[\\/]|\.gitlab-ci\.ya?ml$|\.circleci[\\/]|Jenkinsfile$|azure-pipelines\.ya?ml$|bitbucket-pipelines\.ya?ml$|\.buildkite[\\/]|\.travis\.ya?ml$|cloudbuild\.ya?ml$)'; then
    ask File "$path" "$CI_WHAT" 'free by itself' "$CI_COST"
  fi
  exit 0
fi

# Trigger words, case-insensitive. A payload with none of them is dismissed here.
NOW_WORDS='[Gg][Hh]\ |[Gg][Hh].[Ee][Xx][Ee]|[Aa][Pp][Ii].|[Gg]enerativelanguage|[Vv][Ee][Rr][Cc][Ee][Ll]|[Nn][Ee][Tt][Ll][Ii][Ff][Yy]|[Ww][Rr][Aa][Nn][Gg][Ll][Ee][Rr]|[Ff][Ll][Yy]|[Dd][Oo][Cc][Kk][Ee][Rr]|[Tt][Ee][Rr][Rr][Aa][Ff][Oo][Rr][Mm]|[Pp][Uu][Ll][Uu][Mm][Ii]|[Cc][Dd][Kk]|[Ss][Aa][Mm]\ |[Ss][Ee][Rr][Vv][Ee][Rr][Ll][Ee][Ss][Ss]|[Ss][Ll][Ss]|[Ff][Ii][Rr][Ee][Bb][Aa][Ss][Ee]|[Rr][Aa][Ii][Ll][Ww][Aa][Yy]|[Hh][Ee][Rr][Oo][Kk][Uu]|[Ss][Uu][Pp][Aa][Bb][Aa][Ss][Ee]|[Aa][Ww][Ss]|[Gg][Cc][Ll][Oo][Uu][Dd]|[Aa][Zz]\ '
PUSH_WORDS='[Pp][Uu][Ss][Hh]|[Gg][Hh]\ |[Gg][Hh].[Ee][Xx][Ee]'
PUB_WORDS='[Pp][Uu][Bb][Ll][Ii][Ss][Hh]|[Tt][Ww][Ii][Nn][Ee]|[Pp][Uu][Ss][Hh]'
# shellcheck disable=SC2086 # split the |-lists into separate glob words on purpose
words() { old=$IFS; IFS='|'; set -- $1; IFS=$old; mentions "$text" "$@"; }

text=$input
words "$NOW_WORDS|$PUSH_WORDS|$PUB_WORDS|$WORKFLOWS" || exit 0

cmd=$(field command)
[ -z "$cmd" ] && exit 0
text=$cmd

# One segment per line:
#   1. join line continuations (\ or PowerShell ` before an escaped newline);
#   2. protect escaped backslashes so \n detection cannot misfire on them;
#   3. turn JSON \n escapes into real newlines;
#   4. encode & ; | inside a quoted URL (where they are not shell separators)
#      as %26 %3B %7C; in an unquoted URL they really do split the command;
#   5. split on ; & | and newlines, restore backslashes, trim, drop empties.
segs=$(printf '%s' "$cmd" | sed -E \
    -e 's/\\\\\\n/ /g' \
    -e 's/`\\n/ /g' \
    -e 's/\\\\/@@BS@@/g' \
    -e 's/\\n/\
/g' \
    -e ':a' \
    -e 's#(\\"https?://[^\\[:space:]]*)&#\1%26#' -e 'ta' \
    -e 's#(\\"https?://[^\\[:space:]]*);#\1%3B#' -e 'ta' \
    -e 's#(\\"https?://[^\\[:space:]]*)[|]#\1%7C#' -e 'ta' \
    -e "s#('https?://[^'[:space:]]*)&#\\1%26#" -e 'ta' \
    -e "s#('https?://[^'[:space:]]*);#\\1%3B#" -e 'ta' \
    -e "s#('https?://[^'[:space:]]*)[|]#\\1%7C#" -e 'ta' \
  | tr ';&|' '\n\n\n' \
  | sed -E -e 's/@@BS@@/\\\\/g' -e 's/^[[:space:]]+//' -e 's/[[:space:]]+$//' -e '/^$/d')

# Word start: line start or any character that cannot be part of a command
# name (a path separator counts, so /usr/bin/git and C:\...\gh.exe match).
W='(^|[^[:alnum:]_.-])'
# Optional Windows suffix and closing quote after a command name.
X='(\.(exe|cmd))?(\\")?'
# Word end: whitespace, segment end, an escape, or the close of ( ) / $( ) / backticks.
E='([[:space:]]|$|\\|[)`])'
first() { printf '%s\n' "$segs" | grep -i -m 1 -E -- "$1"; }
is() { printf '%s' "$seg" | grep -q -i -E -- "$1"; }

GH_RUN="${W}gh${X}[[:space:]]+(workflow[[:space:]]+run|run[[:space:]]+rerun)${E}"
CLIENT="${W}(curl|wget|http|https|Invoke-RestMethod|irm|Invoke-WebRequest|iwr)${X}[[:space:]]"
API_HOST='(api\.(openai|anthropic|cohere|mistral)\.(com|ai)|generativelanguage\.googleapis\.com)'
API="${CLIENT}.*${API_HOST}"
# Bare `vercel` deploys to production too; it counts as the whole segment, a
# path to it, or a word after a space or quote (bash -c "vercel", env X=1 vercel).
DEPLOY="^(npx[[:space:]]+)?([^[:space:]]*[\\/])?vercel${X}\$|(^|[[:space:]]|\\\\\"|')vercel${X}'?\$|${W}(vercel${X}[[:space:]]+(deploy|--prod|--yes|-y)${E}|netlify${X}[[:space:]]+deploy|wrangler${X}[[:space:]]+(deploy|publish|pages[[:space:]]+(deploy|publish)|versions[[:space:]]+upload)|(fly|flyctl)${X}[[:space:]]+(deploy|launch|scale|machine)|docker${X}[[:space:]]+push|terraform${X}[[:space:]]+apply|pulumi${X}[[:space:]]+up|cdk${X}[[:space:]]+deploy|sam${X}[[:space:]]+deploy|(serverless|sls)${X}[[:space:]]+deploy|firebase${X}[[:space:]]+deploy|railway${X}[[:space:]]+up|heroku${X}[[:space:]]+(create|container:push|container:release)|supabase${X}[[:space:]]+(functions[[:space:]]+deploy|db[[:space:]]+push|projects[[:space:]]+create)|aws${X}[[:space:]]+[[:alnum:]-]+[[:space:]]+(create|run|start|put|deploy|invoke|launch|update)[[:alnum:]-]*|gcloud${X}[[:space:]]+.*[[:space:]](deploy|create|submit)${E}|az${X}[[:space:]]+.*[[:space:]]create${E})"
GIT="${W}git${X}([[:space:]]+(-C[[:space:]]+[^[:space:]]+|-c[[:space:]]+[^[:space:]]+|--[^[:space:]]+))*[[:space:]]+"
PUSH="${GIT}push${E}"
PR="${W}gh${X}[[:space:]]+pr[[:space:]]+(create|merge)${E}"
ENABLE="${W}gh${X}[[:space:]]+workflow[[:space:]]+enable${E}"
PUBLISH="${W}((npm|pnpm|yarn)${X}[[:space:]]+publish|cargo${X}[[:space:]]+publish|twine${X}[[:space:]]+upload|gem${X}[[:space:]]+push|nuget${X}[[:space:]]+push|dotnet${X}[[:space:]]+nuget[[:space:]]+push)${E}"

# Ranked from most to least expensive; the first class with a match wins, and
# within a class the leftmost segment. Each class is skipped by a builtin word
# check when none of its words appear, saving a process per class.
seg=
if words "$NOW_WORDS"; then
  seg=$(first "$GH_RUN|$API|$DEPLOY")
  # The API URL may sit in another segment than the client (a variable, or a
  # request body that split the line): a full URL plus any client still asks.
  if [ -z "$seg" ]; then
    hostseg=$(first "https?://${API_HOST}")
    [ -n "$hostseg" ] && [ -n "$(first "$CLIENT")" ] && \
      ask Command "$hostseg" 'calls a paid model API' 'bills now' 'per-token charges on the API key this command uses'
  fi
fi
if [ -n "$seg" ]; then
  if is "$GH_RUN"; then
    ask Command "$seg" 'starts a GitHub Actions run' 'bills now' 'Actions minutes on the GitHub account that owns the repository'
  elif is "$API"; then
    ask Command "$seg" 'calls a paid model API' 'bills now' 'per-token charges on the API key this command uses'
  else
    ask Command "$seg" 'deploys or provisions hosted infrastructure' 'bills now' 'build minutes, compute, or egress on the provider account this command is logged into, often recurring while it runs'
  fi
fi

seg=
words "$PUSH_WORDS" && seg=$(printf '%s\n' "$segs" | grep -v -F -e '--dry-run' | grep -i -m 1 -E -- "$PUSH|$PR")
if [ -n "$seg" ]; then
  if is "$PUSH"; then
    ask Command "$seg" 'pushes commits to a remote' 'can bill now' 'if the target branch has GitHub Actions workflows, the push starts runs billed as Actions minutes on the account that owns the repository; git push --dry-run or keeping the commit local costs nothing'
  elif is "${W}gh${X}[[:space:]]+pr[[:space:]]+create"; then
    ask Command "$seg" 'opens a pull request' 'can bill now' 'workflows armed on pull_request start runs billed as Actions minutes on the account that owns the repository'
  else
    ask Command "$seg" 'merges a pull request into its base branch' 'can bill now' 'the merge is a push to the base branch and starts any workflows armed there (Actions minutes)'
  fi
fi

if words "$PUSH_WORDS"; then
  seg=$(first "$ENABLE")
  [ -n "$seg" ] && ask Command "$seg" 'turns on a GitHub Actions workflow' 'bills later' 'every later trigger of that workflow runs billed Actions minutes, with nobody watching'
fi

seg=
words "$PUB_WORDS" && seg=$(first "$PUBLISH")
[ -n "$seg" ] && ask Command "$seg" 'publishes a package to a public registry' 'no charge, but public and permanent' 'anyone can install it at once, and a published version cannot be cleanly withdrawn'

# CI config written from the shell. Only writes count, and URLs are removed
# first so a download whose source path names the folder is not a write.
words "$WORKFLOWS" || exit 0
P='\.github[\\/]+workflows'
CI_WRITE=">[[:space:]]*[^[:space:]]*${P}|${W}tee${X}([[:space:]]+-[^[:space:]]+)*[[:space:]]+[^[:space:]]*${P}|${W}(mkdir|touch|New-Item)${X}[[:space:]].*${P}|${W}(cp|mv|ln|Copy-Item|Move-Item)${X}[[:space:]].*[[:space:]][^[:space:]]*${P}[^[:space:]]*$|^install${X}[[:space:]].*[[:space:]][^[:space:]]*${P}[^[:space:]]*$|[[:space:]]-Destination[[:space:]]+[^[:space:]]*${P}|${W}sed${X}[[:space:]](.*[[:space:]])?(-[[:alnum:]]*i[^[:space:]]*|--in-place[^[:space:]]*)[[:space:]].*${P}|${W}(curl|wget|Invoke-WebRequest|iwr)${X}([[:space:]].*)?[[:space:]](-o|--output|--output-document|--output-dir|-P|--directory-prefix|-OutFile)([[:space:]]+|=)?[^[:space:]]*${P}|${W}(Set-Content|Add-Content|Out-File)${X}[[:space:]].*${P}|${GIT}(add|mv|commit|checkout|restore)[[:space:]].*${P}"
hit=$(printf '%s\n' "$segs" | sed -E 's#https?://[^[:space:]\\"'"'"']*##g' | grep -n -i -m 1 -E -- "$CI_WRITE")
if [ -n "$hit" ]; then
  seg=$(printf '%s\n' "$segs" | sed -n "${hit%%:*}p")
  ask Command "$seg" "$CI_WHAT" 'free by itself' "$CI_COST"
fi
exit 0
