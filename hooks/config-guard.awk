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

# Drop a JSON line's trailing comma, so adding a neighbouring key (which adds a
# comma to this line) does not count as a change to this line.
function norm(l) { sub(/[ \t]*,?[ \t]*$/, "", l); return l }

# ---- shell commands ----------------------------------------------------------

# Shell mode: print "B|W\t<what>\t<segment>" for the first bypass, else the
# first write to an existing guarded file, else nothing. The command is judged
# twice: split with quotes respected (a quoted message never splits it), then
# split ignoring quotes, because an apostrophe in a comment or heredoc body is
# not shell quoting and would otherwise hide every later command.
function shell(   cmd) {
  cmd = jraw("command")
  if (cmd == NONE || cmd == "") return
  CWD = jraw("cwd")
  load_table()
  # Protect escaped backslashes and join line continuations.
  gsub(/\\\\/, "\002", cmd)
  gsub(/\\r\\n/, "\\n", cmd)
  gsub(/\002\\n/, " ", cmd)
  gsub(/`\\n/, " ", cmd)
  split_segments(mask_quoted(cmd))
  if (judge()) return
  split_segments(cmd)
  judge()
}

# Fill SEG[1..NS] by splitting CMD on escaped newlines and ; & |, restoring
# the characters that \002-\006 stand for.
function split_segments(cmd,   n, i, lines, m, j, parts, seg) {
  n = split(cmd, lines, /\\n/); NS = 0
  for (i = 1; i <= n; i++) {
    m = split(lines[i], parts, /[;&|]/)
    for (j = 1; j <= m; j++) {
      seg = parts[j]
      gsub(/\002/, "\\\\", seg); gsub(/\003/, ";", seg); gsub(/\004/, "\\&", seg)
      gsub(/\005/, "|", seg); gsub(/\006/, "\\n", seg)
      sub(/^[ \t]+/, "", seg); sub(/[ \t]+$/, "", seg)
      if (seg != "") SEG[++NS] = seg
    }
  }
}

# Print the first match in SEG (bypasses before writes, leftmost first) and
# return 1, or return 0 when nothing matches.
function judge(   k, j, what, cdseen) {
  for (k = 1; k <= NS; k++) {
    what = bypass(SEG[k])
    if (what == "" && skip_export(SEG[k]))
      for (j = k + 1; j <= NS; j++) if (runs_git(unquote(SEG[j]))) { what = "skips the repository's git hooks"; break }
    if (what != "") { printf "B\t%s\t%s\n", what, SEG[k]; return 1 }
  }
  cdseen = 0
  for (k = 1; k <= NS; k++) {
    what = write_hit(SEG[k], cdseen)
    if (what != "") { printf "W\t%s\t%s\n", what, SEG[k]; return 1 }
    if (tolower(first_word(SEG[k])) ~ /^(cd|pushd|set-location|sl|chdir)$/) cdseen = 1
  }
  return 0
}

# True when the segment exports SKIP (in any position, or bare) for later commands.
function skip_export(seg,   low) {
  low = tolower(unquote(seg))
  if (low ~ /^\$env:skip[ \t]*=/) return 1
  return low ~ /^(export|declare[ \t]+-[a-z]*x[a-z]*)([ \t]|$)/ && low ~ /[ \t]skip([ \t]*=|[ \t]|$)/
}

# The segment with quoted text emptied, except that a quoted path or name of
# git becomes `git` and a quoted 0 right after `=` stays (so `$env:HUSKY = '0'`
# still reads as HUSKY=0).
function unquote(seg,   s) {
  s = seg
  gsub(/\\"([^"]*[\\\/])?[Gg][Ii][Tt](\.[Ee][Xx][Ee])?\\"/, "git", s)
  gsub(/'([^']*[\\\/])?[Gg][Ii][Tt](\.[Ee][Xx][Ee])?'/, "git", s)
  gsub(/=[ \t]*(\\"|')0(\\"|')/, "=0", s)
  gsub(/\\"([^\\]|\\[^"])*\\"/, "\"\"", s)
  gsub(/'[^']*'/, "''", s)
  return s
}

# Replace ; & | and escaped newlines inside quotes with \003-\006, so a quoted
# commit message never splits a command. CMD is JSON-escaped with escaped
# backslashes hidden as \002, so a \" or ' right after \002 is a
# backslash-escaped quote character, not a delimiter.
function mask_quoted(cmd,   out, i, n, c, dq, sq, esc) {
  out = ""; n = length(cmd); dq = sq = 0
  for (i = 1; i <= n; i++) {
    c = substr(cmd, i, 1)
    esc = (i > 1 && substr(cmd, i - 1, 1) == "\002")
    if (!sq && c == "\\" && substr(cmd, i + 1, 1) == "\"") { if (!esc) dq = !dq; out = out "\\\""; i++; continue }
    if (!dq && c == "'") { if (!esc) sq = !sq }
    else if (dq || sq) {
      if (c == ";") c = "\003"
      else if (c == "&") c = "\004"
      else if (c == "|") c = "\005"
      else if (c == "\\" && substr(cmd, i + 1, 1) == "n") { c = "\006"; i++ }
    }
    out = out c
  }
  return out
}

# True when an unquote()d segment runs git (bare or by path).
function runs_git(s) {
  return tolower(s) ~ /(^|[^[:alnum:]_.-])git(\.exe)?([ \t]|$)/
}

# The bypass a segment performs, as the prompt's "What it does" text, or "".
function bypass(seg,   s, low, n, T, i, j, c, tok, after, at) {
  s = unquote(seg)
  low = tolower(s)
  if (runs_git(s)) {
    if (s ~ /(^|[ \t])--no-verify([ \t=]|$)/) return "skips the repository's git hooks"
    n = split(s, T, /[ \t]+/); at = 0
    for (i = 1; i <= n; i++) {
      if (!at && tolower(T[i]) ~ /(^|[\\\/])git(\.exe)?$/) { at = i; continue }
      if (at && !after) {
        if (T[i] ~ /^(-C|-c|--git-dir|--work-tree|--namespace|--config-env|--super-prefix)$/) { i++; continue }
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
      if (low ~ /(^|[ \t])(--unset(-all)?|unset)([ \t]|$)/) return "points git at a different hooks folder"
      if (low !~ /--get/ && low ~ /core\.hookspath[ \t]+[^ \t]/) return "points git at a different hooks folder"
    }
    if (s ~ /(^|[ \t])--no-gpg-sign([ \t]|$)/ || low ~ /-c[ \t]+commit\.gpgsign=(false|0|no|off)([ \t]|$)/) return "skips commit signing"
  }
  # Variable names: any case, because Windows environment names ignore case.
  if (low ~ /(^|[^[:alnum:]_])(husky|lefthook)[ \t]*=[ \t]*(\\?["'])?0([^0-9]|$)/) return "turns off the hook runner"
  if (low ~ /(^|[ \t])skip=[^ \t]*[ \t]+(.*[ \t])?([^ \t]*[\\\/])?git(\.exe)?([ \t]|$)/) return "skips the repository's git hooks"
  return ""
}

# The segment's first whitespace-separated word (the command, for cd detection).
function first_word(seg,   T) {
  split(seg, T, /[ \t]+/)
  return T[1]
}

# "changes ..." / "moves or deletes ..." when the segment writes an existing
# guarded file, else "".
function write_hit(seg, cdseen,   s, m, n, R, T, i, start, cmd, sub1, tgt, nt, cat, k, mover) {
  s = seg
  gsub(/\\\\/, "\002", s); gsub(/\\[tr]/, " ", s); gsub(/\002/, "\\\\", s)
  gsub(/[0-9]*>+/, " > ", s); gsub(/<+/, " < ", s)
  # Redirect targets are write targets; the rest are the command's arguments,
  # so `cp a .eslintrc.json 2>/dev/null` still ends in the real destination.
  m = split(s, R, /[ \t]+/); n = 0; nt = 0
  for (i = 1; i <= m; i++) {
    sub(/^(\\"|')/, "", R[i]); sub(/(\\"|')$/, "", R[i])
    if (R[i] == ">") { if (i < m) { i++; sub(/^(\\"|')/, "", R[i]); sub(/(\\"|')$/, "", R[i]); TG[++nt] = R[i] } }
    else if (R[i] == "<") i++   # an input redirect and its source are not arguments
    else T[++n] = R[i]
  }
  start = 1
  while (start <= n && (T[start] == "" || T[start] ~ /^[A-Za-z_][A-Za-z0-9_]*=/)) start++
  cmd = tolower(T[start]); sub(/.*[\\\/]/, "", cmd); sub(/\.exe$/, "", cmd)
  if (cmd == "git") {
    for (i = start + 1; i <= n && T[i] ~ /^-/; i++) if (T[i] ~ /^(-C|-c|--git-dir|--work-tree|--namespace|--config-env|--super-prefix)$/) i++
    sub1 = T[i]
    if (sub1 == "mv" || sub1 == "rm") { for (k = i + 1; k <= n; k++) TG[++nt] = T[k]; mover = 1 }
  } else if (cmd ~ /^(mv|move-item|mi|move|ren|rename|rename-item|rm|del|erase|unlink|remove-item|ri)$/) {
    for (k = start + 1; k <= n; k++) TG[++nt] = T[k]; mover = 1
  } else if (cmd ~ /^(tee|truncate|set-content|add-content|out-file|sc|ac|clear-content|clc|new-item|ni)$/) {
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

# True for a path inside a .husky folder or .git/hooks (either separator).
function hookpath(p) { return p ~ /(^|[\\\/])\.husky[\\\/]/ || p ~ /(^|[\\\/])\.git[\\\/]+hooks[\\\/]/ }

# True when P can be opened. A relative P is resolved against the payload's
# cwd, which is still JSON-escaped: Windows accepts its doubled backslashes.
# An empty file counts as existing (getline returns 0, not -1).
function exists(p,   r, line) {
  if (p !~ /^(\/|[A-Za-z]:|\\\\)/ && CWD != NONE && CWD != "") p = CWD "/" p
  r = (getline line < p)
  close(p)
  return r >= 0
}

# ---- the filename table (single source: hooks/config-guard.sh) --------------

# Turn CG_TABLE's "<category> <glob>..." rows into anchored regexes (GRE/GCAT).
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

# The category of path P by its exact basename ("shared" for shared files), or "".
function classify(p,   b, i) {
  b = p; sub(/.*[\\\/]/, "", b)
  if (b ~ /\.sample$/) return ""
  for (i = 1; i <= NG; i++) if (b ~ GRE[i]) return GCAT[i]
  if (hookpath(p)) return "git hook"
  return ""
}
