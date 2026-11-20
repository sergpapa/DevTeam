# Shared-file comparison for hooks/config-guard.sh (loaded with config-guard.awk).
# Why separate: keeps each awk file under the 350-line cap; see config-guard.awk
# for the input contract.

# ---- shared files: compare tool-config lines before and after ---------------

function shared(   F, text, line, before, after, tool, c, o, nw, p, all, res, rest, shape) {
  F = ENVIRON["CG_FILE"]; shape = ENVIRON["CG_SHAPE"]; tool = ENVIRON["CG_TOOL"]
  text = ""
  while ((getline line < F) > 0) text = text line "\n"
  close(F)
  gsub(/\r/, "", text)
  before = toollines(text, shape)
  if (before == "") return
  if (tool == "MultiEdit") { print "ask"; return }
  if (tool == "Write") {
    c = jraw("content")
    if (c == NONE) { print "ask"; return }
    after = toollines(unesc(c), shape)
  } else {
    o = jraw("old_string"); nw = jraw("new_string")
    if (o == NONE || nw == NONE) { print "ask"; return }
    o = unesc(o); nw = unesc(nw); gsub(/\r/, "", o); gsub(/\r/, "", nw)
    if (o == "" || !index(text, o)) { print "ask"; return }
    all = (J ~ /"replace_all"[ \t\r\n]*:[ \t\r\n]*true/)
    res = ""; rest = text
    do {
      p = index(rest, o)
      if (!p) break
      res = res substr(rest, 1, p - 1) nw; rest = substr(rest, p + length(o))
    } while (all)
    after = toollines(res rest, shape)
  }
  if (before != after) print "ask"
}

# The lines of TEXT that hold lint, format, type or test settings, one per
# line, blank lines dropped; JSON lines lose trailing commas so that adding a
# neighbouring key does not count as a change.
function toollines(text, shape,   n, L, i, line, out, keep, top, ind, key, cur, hdr) {
  gsub(/\r/, "", text)
  n = split(text, L, "\n"); out = ""; keep = 0; top = -1; cur = ""
  for (i = 1; i <= n; i++) {
    line = L[i]
    if (line ~ /^[ \t]*$/) continue
    if (shape == "pyproject" || shape == "setupcfg" || shape == "cargo") {
      if (line ~ /^[ \t]*\[/) {
        hdr = line; sub(/^[ \t]*\[\[?[ \t]*/, "", hdr)
        if (shape == "pyproject") keep = (hdr ~ /^tool\.(ruff|black|isort|pytest|mypy|pylint|coverage|pyright|flake8|tox|pydocstyle|bandit)/)
        else if (shape == "setupcfg") keep = (hdr ~ /^(flake8|tool:pytest|mypy|isort|pycodestyle|pydocstyle|coverage:|pylint)/)
        else keep = (hdr ~ /^(lints|workspace\.lints)/)
      }
      if (keep) out = out line "\n"
    } else if (shape == "pkg") {
      match(line, /^[ \t]*/); ind = RLENGTH
      if (top < 0 && line ~ /^[ \t]*"/) top = ind
      if (ind == top && line ~ /^[ \t]*"/) {
        key = line; sub(/^[ \t]*"/, "", key); sub(/".*/, "", key); cur = key
      } else if (ind < top) cur = ""
      if (cur ~ /^(eslintConfig|prettier|stylelint|jest|ava|mocha|nyc|c8|lint-staged|husky|vitest)$/) out = out norm(line) "\n"
      else if (cur == "scripts" && ind > top && line ~ /^[ \t]*"(test|lint|format|typecheck)(:[^"]*)?"[ \t]*:/) out = out norm(line) "\n"
    } else if (shape == "ts") {
      if (line ~ /"(strict[A-Za-z]*|noImplicit[A-Za-z]*|noUnused[A-Za-z]*|noUnchecked[A-Za-z]*|noFallthroughCasesInSwitch|noPropertyAccessFromIndexSignature|exactOptionalPropertyTypes|useUnknownInCatchVariables|alwaysStrict|skipLibCheck|checkJs|allowUnreachableCode|allowUnusedLabels)"[ \t]*:/)
        out = out norm(line) "\n"
    }
  }
  return out
}

# Drop a JSON line's trailing comma, so adding a neighbouring key (which adds a
# comma to this line) does not count as a change to this line.
function norm(l) { sub(/[ \t]*,?[ \t]*$/, "", l); return l }
