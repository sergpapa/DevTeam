# Slow path of hooks/config-guard.sh (spec: docs/specs/config-guard.md).
#
# Why a separate awk file: the slow path needs a JSON string reader, a table
# of filename globs, per-segment shell rules and a before/after diff of a
# file's tool-config lines. One awk process does all of it, where sed/grep
# pipelines would cost a process per rule on Windows.
#
# Input: the PreToolUse JSON on stdin. Environment:
#   CG_MODE   shell  -> prints "<B|W>\t<what>\t<segment>" for the first match, or nothing
#             shared -> prints "ask" when the call changes CG_FILE's tool-config lines
#   CG_TABLE  lines of "<category> <glob> <glob> ..." (category uses _ for spaces)
#   CG_FILE, CG_SHAPE, CG_TOOL   shared mode only
# Segments stay JSON-escaped so they can be echoed straight back into JSON.

{ J = J $0 "\n" }

END {
  NONE = "\001"
  if (ENVIRON["CG_MODE"] == "shared") shared()
  else if (ENVIRON["CG_MODE"] == "shell") shell()
}

# ---- JSON strings -----------------------------------------------------------

# The still-escaped value of the first "key": "..." in the payload, or NONE.
function jraw(key,   s, out) {
  if (!match(J, "\"" key "\"[ \t\r\n]*:[ \t\r\n]*\"")) return NONE
  s = substr(J, RSTART + RLENGTH); out = ""
  while (match(s, /[\\"]/)) {
    out = out substr(s, 1, RSTART - 1)
    if (substr(s, RSTART, 1) == "\"") return out
    out = out substr(s, RSTART, 2); s = substr(s, RSTART + 2)
  }
  return out s
}

# Decode JSON escapes. \uXXXX is left as written (see the spec's assumptions).
function unesc(s,   out, c) {
  out = ""
  while (match(s, /\\/)) {
    out = out substr(s, 1, RSTART - 1); c = substr(s, RSTART + 1, 1)
    if (c == "n") out = out "\n"
    else if (c == "t") out = out "\t"
    else if (c == "r") out = out "\r"
    else if (c == "b") out = out "\b"
    else if (c == "f") out = out "\f"
    else if (c == "u") out = out "\\u"
    else out = out c
    s = substr(s, RSTART + 2)
  }
  return out s
}

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

function norm(l) { sub(/[ \t]*,?[ \t]*$/, "", l); return l }

# ---- shell commands ----------------------------------------------------------

function shell(   cmd, n, i, lines, k, parts, m, j, seg, s, what, cdseen) {
  cmd = jraw("command")
  if (cmd == NONE || cmd == "") return
  CWD = jraw("cwd")
  load_table()
  # Protect escaped backslashes, join line continuations, then split on
  # escaped newlines and on ; & |.
  gsub(/\\\\/, "\002", cmd)
  gsub(/\\r\\n/, "\\n", cmd)
  gsub(/\002\\n/, " ", cmd)
  gsub(/`\\n/, " ", cmd)
  n = split(cmd, lines, /\\n/); NS = 0
  for (i = 1; i <= n; i++) {
    m = split(lines[i], parts, /[;&|]/)
    for (j = 1; j <= m; j++) {
      seg = parts[j]; gsub(/\002/, "\\\\", seg)
      sub(/^[ \t]+/, "", seg); sub(/[ \t]+$/, "", seg)
      if (seg != "") SEG[++NS] = seg
    }
  }
  for (k = 1; k <= NS; k++) {
    what = bypass(SEG[k])
    if (what != "") { printf "B\t%s\t%s\n", what, SEG[k]; return }
  }
  cdseen = 0
  for (k = 1; k <= NS; k++) {
    what = write_hit(SEG[k], cdseen)
    if (what != "") { printf "W\t%s\t%s\n", what, SEG[k]; return }
    if (tolower(first_word(SEG[k])) ~ /^(cd|pushd|set-location|sl|chdir)$/) cdseen = 1
  }
}

# The bypass a segment performs, as the prompt's "What it does" text, or "".
function bypass(seg,   s, low, n, T, i, j, c, tok, after, at) {
  s = seg
  gsub(/\\"([^\\]|\\[^"])*\\"/, "\"\"", s)    # drop double-quoted text (escaped form)
  gsub(/'[^']*'/, "''", s)                     # drop single-quoted text
  low = tolower(s)
  if (low ~ /(^|[^[:alnum:]_.-])git(\.exe)?([ \t]|$)/) {
    if (s ~ /(^|[ \t])--no-verify([ \t=]|$)/) return "skips the repository's git hooks"
    n = split(s, T, /[ \t]+/); at = 0
    for (i = 1; i <= n; i++) {
      if (!at && T[i] ~ /(^|[\\\/])git(\.exe)?$/) { at = i; continue }
      if (at && !after) {
        if (T[i] == "-C" || T[i] == "-c") { i++; continue }
        if (T[i] ~ /^-/) continue
        after = T[i]; if (after != "commit") break; continue
      }
      if (after == "commit") {
        tok = T[i]
        if (tok == "--") break
        if (tok ~ /^-[^-]/) {
          for (j = 2; j <= length(tok); j++) {
            c = substr(tok, j, 1)
            if (c == "n") return "skips the repository's git hooks"
            if (index("mFcCtSu", c)) break
          }
        }
      }
    }
    if (low ~ /-c[ \t]+core\.hookspath=/) return "points git at a different hooks folder"
    if (low ~ /(^|[ \t])config([ \t]|$)/ && low ~ /core\.hookspath/) {
      if (low ~ /--unset/) return "points git at a different hooks folder"
      if (low !~ /--get/ && low ~ /core\.hookspath[ \t]+[^ \t]/) return "points git at a different hooks folder"
    }
    if (s ~ /(^|[ \t])--no-gpg-sign([ \t]|$)/ || low ~ /-c[ \t]+commit\.gpgsign=(false|0|no|off)([ \t]|$)/) return "skips commit signing"
  }
  if (seg ~ /(^|[^[:alnum:]_])(HUSKY|LEFTHOOK)[ \t]*=[ \t]*(\\?["'])?0([^0-9]|$)/) return "turns off the hook runner"
  if (seg ~ /(^|[ \t])SKIP=[^ \t]*[ \t]+(.*[ \t])?([^ \t]*[\\\/])?git(\.exe)?([ \t]|$)/) return "skips the repository's git hooks"
  return ""
}

function first_word(seg,   T) {
  split(seg, T, /[ \t]+/)
  return T[1]
}

# "changes ..." / "moves or deletes ..." when the segment writes an existing
# guarded file, else "".
function write_hit(seg, cdseen,   s, n, T, i, start, cmd, sub1, tgt, nt, cat, k, mover) {
  s = seg
  gsub(/\\\\/, "\002", s); gsub(/\\[tr]/, " ", s); gsub(/\002/, "\\\\", s)
  gsub(/[0-9]*>+/, " > ", s)
  n = split(s, T, /[ \t]+/)
  for (i = 1; i <= n; i++) { sub(/^(\\"|')/, "", T[i]); sub(/(\\"|')$/, "", T[i]) }
  start = 1
  while (start <= n && (T[start] == "" || T[start] ~ /^[A-Za-z_][A-Za-z0-9_]*=/)) start++
  cmd = tolower(T[start]); sub(/.*[\\\/]/, "", cmd); sub(/\.exe$/, "", cmd)
  nt = 0
  for (i = 1; i < n; i++) if (T[i] == ">") TG[++nt] = T[i + 1]
  if (cmd == "git") {
    for (i = start + 1; i <= n && T[i] ~ /^-/; i++) if (T[i] == "-C" || T[i] == "-c") i++
    sub1 = T[i]
    if (sub1 == "mv" || sub1 == "rm") { for (k = i + 1; k <= n; k++) TG[++nt] = T[k]; mover = 1 }
  } else if (cmd ~ /^(mv|move-item|mi|move|ren|rename|rename-item|rm|del|erase|unlink|remove-item|ri)$/) {
    for (k = start + 1; k <= n; k++) TG[++nt] = T[k]; mover = 1
  } else if (cmd ~ /^(tee|truncate|set-content|add-content|out-file|sc|ac)$/) {
    for (k = start + 1; k <= n; k++) TG[++nt] = T[k]
  } else if (cmd == "sed" || cmd == "perl") {
    for (k = start + 1; k <= n; k++) if (T[k] ~ /^-[A-Za-z]*i/ || T[k] ~ /^--in-place/) break
    if (k <= n) for (k = start + 1; k <= n; k++) TG[++nt] = T[k]
  } else if (cmd ~ /^(cp|install|ln|copy-item|cpi|copy)$/) {
    TG[++nt] = T[n]
    for (k = start + 1; k < n; k++) if (tolower(T[k]) == "-destination") TG[++nt] = T[k + 1]
  } else if (cmd ~ /^(curl|wget|invoke-webrequest|iwr)$/) {
    for (k = start + 1; k <= n; k++) {
      if (T[k] ~ /^--(output|output-document)=/) { tgt = T[k]; sub(/^[^=]*=/, "", tgt); TG[++nt] = tgt }
      else if (k < n && (T[k] == "-o" || T[k] == "--output" || T[k] == "--output-document" || tolower(T[k]) == "-outfile" || (cmd == "wget" && T[k] == "-O"))) TG[++nt] = T[k + 1]
    }
  } else if (cmd == "chmod") {
    for (k = start + 1; k <= n; k++) if (hookpath(T[k])) TG[++nt] = T[k]
  }
  for (k = 1; k <= nt; k++) {
    tgt = TG[k]
    if (tgt == "" || tgt ~ /^-/) continue
    cat = classify(tgt)
    if (cat == "" || cat ~ /^shared/) continue
    if (!cdseen && !exists(tgt)) continue
    return (mover ? "moves or deletes existing " : "changes existing ") cat " config"
  }
  return ""
}

function hookpath(p) { return p ~ /(^|[\\\/])\.husky[\\\/]/ || p ~ /(^|[\\\/])\.git[\\\/]+hooks[\\\/]/ }

function exists(p,   r, line) {
  if (p !~ /^(\/|[A-Za-z]:|\\\\)/ && CWD != NONE && CWD != "") p = CWD "/" p
  r = (getline line < p)
  close(p)
  return r >= 0
}

# ---- the filename table (single source: hooks/config-guard.sh) --------------

function load_table(   rows, n, i, f, m, j, cat, re) {
  n = split(ENVIRON["CG_TABLE"], rows, "\n")
  for (i = 1; i <= n; i++) {
    m = split(rows[i], f, " ")
    if (m < 2) continue
    cat = f[1]; gsub(/_/, " ", cat)
    for (j = 2; j <= m; j++) {
      re = f[j]; gsub(/\./, "[.]", re); gsub(/\*/, ".*", re)
      NG++; GRE[NG] = "^" re "$"; GCAT[NG] = cat
    }
  }
}

function classify(p,   b, i) {
  b = p; sub(/.*[\\\/]/, "", b)
  if (b ~ /\.sample$/) return ""
  for (i = 1; i <= NG; i++) if (b ~ GRE[i]) return GCAT[i]
  if (hookpath(p)) return "git hook"
  return ""
}
