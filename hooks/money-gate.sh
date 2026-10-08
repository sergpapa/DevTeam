#!/bin/sh
# DevTeam money gate (PreToolUse hook).
#
# Why: the CLAUDE.md money rule is a prompt rule, so it holds only as long as the
# model remembers it. This hook is the mechanical floor under it: any tool call
# that can bill the user's account gets a permission prompt that names the
# charge, even in auto mode. It never approves anything (silence = normal flow)
# and never denies outright, because the rule asks for explicit per-instance
# approval, which is exactly what the prompt is. Users who want a hard wall add
# a deny rule in settings.json instead.
#
# Contract: reads the PreToolUse JSON on stdin, prints a PreToolUse decision JSON
# on stdout, always exits 0. Needs only POSIX sh + grep -E + sed, so it runs in
# Git Bash on Windows and in /bin/sh on macOS and Linux with nothing installed.

input=$(cat)

# One string field out of the hook JSON (first occurrence), still JSON-escaped.
field() {
  pat='"'"$1"'"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"'
  printf '%s' "$input" | tr -d '\n' | grep -o -E "$pat" | head -n 1 \
    | sed -e 's/^"[A-Za-z_]*"[[:space:]]*:[[:space:]]*"//' -e 's/"$//'
}

ask() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"DevTeam money gate: %s. CLAUDE.md requires explicit per-instance approval that names the account, the meter, the estimate, and whether it recurs. Approve only if that was given for this exact run."}}\n' "$1"
  exit 0
}

has() { printf '%s' "$1" | grep -q -E -- "$2"; }

tool=$(field tool_name)
W='(^|[^[:alnum:]_./-]|\\n)'      # word start: not part of a path or flag, or after a JSON \n escape
E='([[:space:]]|$|[;&|\\])'       # word end: space, end, separator, or a JSON \n escape

case "$tool" in
  Bash|PowerShell)
    cmd=$(field command)
    [ -z "$cmd" ] && exit 0

    if has "$cmd" "${W}git([[:space:]]+(-C[[:space:]]+[^[:space:]]+|-c[[:space:]]+[^[:space:]]+|--[^[:space:]]+))*[[:space:]]+push${E}" && ! has "$cmd" '--dry-run'; then
      ask "git push lands commits on a remote, and any workflow armed on that branch starts a billed run (Actions minutes). The free alternative is git push --dry-run, or leaving the commit local"
    fi
    if has "$cmd" "${W}gh[[:space:]]+(workflow[[:space:]]+(run|enable)|run[[:space:]]+rerun|pr[[:space:]]+(create|merge))"; then
      ask "this gh command triggers or arms a GitHub Actions run, which bills Actions minutes"
    fi
    if has "$cmd" '\.github[\\/]+workflows'; then
      ask "this touches .github/workflows, a standing charge that bills on the first push. Write the file and leave it unpushed"
    fi
    if has "$cmd" "${W}(vercel([[:space:]]+(deploy|--prod|--yes|-y)|[[:space:]]*($|[;&|\\]))|netlify[[:space:]]+deploy|wrangler[[:space:]]+(deploy|publish|pages[[:space:]]+(deploy|publish)|versions[[:space:]]+upload)|(fly|flyctl)[[:space:]]+(deploy|launch|scale|machine)|docker[[:space:]]+push|terraform[[:space:]]+apply|pulumi[[:space:]]+up|cdk[[:space:]]+deploy|sam[[:space:]]+deploy|(serverless|sls)[[:space:]]+deploy|firebase[[:space:]]+deploy|railway[[:space:]]+up|heroku[[:space:]]+(create|container:push|container:release)|supabase[[:space:]]+(functions[[:space:]]+deploy|db[[:space:]]+push|projects[[:space:]]+create)|aws[[:space:]]+[[:alnum:]-]+[[:space:]]+(create|run|start|put|deploy|invoke|launch|update)[[:alnum:]-]*|gcloud[[:space:]]+.*[[:space:]](deploy|create|submit)${E}|az[[:space:]]+.*[[:space:]]create${E})"; then
      ask "this deploys or provisions hosted infrastructure, which bills build minutes, compute, or egress on the provider account"
    fi
    if has "$cmd" "${W}((npm|pnpm|yarn)[[:space:]]+publish|cargo[[:space:]]+publish|twine[[:space:]]+upload|gem[[:space:]]+push|nuget[[:space:]]+push|dotnet[[:space:]]+nuget[[:space:]]+push)"; then
      ask "this publishes a package to a public registry, which is outward-facing and cannot be undone"
    fi
    if has "$cmd" 'api\.(openai|anthropic|cohere|mistral)\.(com|ai)|generativelanguage\.googleapis\.com'; then
      ask "this calls a metered model API with the user's key, billed per request"
    fi
    ;;
  Write|Edit|MultiEdit|NotebookEdit)
    path=$(field file_path)
    [ -z "$path" ] && exit 0
    if has "$path" '(^|[\\/])(\.github[\\/]+workflows[\\/]|\.gitlab-ci\.ya?ml$|\.circleci[\\/]|Jenkinsfile$|azure-pipelines\.ya?ml$|bitbucket-pipelines\.ya?ml$|\.buildkite[\\/]|\.travis\.ya?ml$|cloudbuild\.ya?ml$)'; then
      ask "this writes CI/CD pipeline config, a standing charge that bills on the first push. Writing it is fine only if the user asked for it; it must stay unpushed"
    fi
    ;;
esac
exit 0
