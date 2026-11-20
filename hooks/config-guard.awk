# Slow path of hooks/config-guard.sh (spec: docs/specs/config-guard.md).
# Loaded together with config-guard-shared.awk and config-guard-shell.awk.
#
# Why awk: the slow path needs a JSON string reader, a table
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
