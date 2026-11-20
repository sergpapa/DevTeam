"""Strict frontmatter parse for skills, agents and output styles.

Why a subset and not a YAML library: Claude Code drops a skill whose
frontmatter its YAML loader rejects, silently. The unquoted colon that killed
/project until 2.0.3 is one such shape. This parser accepts only one-line
`key: value` pairs whose meaning nobody can misread, and names the line and
the fix for anything else. Some shapes it bans are legal YAML (a plain value
starting with `-` or `%`); they are banned because they read as syntax.
"""
import re

KEY = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
INDICATORS = frozenset("-?:,[]{}#&*!|>'\"%@`")
QUOTE_HINT = "wrap the value in double quotes"
TEXT_KEYS = ("name", "description")
# YAML 1.2 core-schema scalars that load as null, a boolean or a number, not text.
NOT_TEXT = re.compile(r"null|Null|NULL|~|true|True|TRUE|false|False|FALSE"
                      r"|[-+]?(\.[0-9]+|[0-9]+(\.[0-9]*)?)([eE][-+]?[0-9]+)?"
                      r"|0o[0-7]+|0x[0-9a-fA-F]+|[-+]?\.(inf|Inf|INF)|\.(nan|NaN|NAN)")


def parse(text):
    """Return (fields, errors). Each error starts with "line N: " or names the fence.

    fields maps key to the unquoted value. Callers should not trust fields when
    errors is non-empty.
    """
    lines = [line[:-1] if line.endswith("\r") else line for line in text.split("\n")]
    if lines[0] != "---":
        hint = " (remove the byte order mark)" if lines[0].startswith("\ufeff") else ""
        return {}, ["line 1: the file must start with a line that is exactly '---'" + hint]
    try:
        close = lines.index("---", 1)
    except ValueError:
        return {}, ["no line that is exactly '---' closes the frontmatter"]

    fields, errors = {}, []
    for number, line in enumerate(lines[1:close], start=2):
        if not line.strip():
            continue
        problem = _line_problem(line, fields)
        if isinstance(problem, str):
            errors.append("line %d: %s" % (number, problem))
        else:
            key, value = problem
            fields[key] = value
    return fields, errors


def _line_problem(line, fields):
    """Return (key, value) for a good line, or a string saying what is wrong."""
    if line[0] in " \t":
        return "indented line; every value must fit on its own 'key: value' line"
    if line.startswith("#"):
        return "comment line; frontmatter takes only 'key: value' lines"
    key, sep, raw = line.partition(": ")
    if not sep:
        if line.endswith(":") and KEY.fullmatch(line[:-1]):
            return "'%s' has an empty value" % line[:-1]
        return "expected 'key: value' (a colon followed by a space)"
    if not KEY.fullmatch(key):
        return "'%s' is not a valid key (letters, digits, '-' and '_', starting with a letter)" % key
    if key in fields:
        return "duplicate key '%s'; keep one" % key
    raw = raw.strip()
    value = _value(raw)
    if isinstance(value, tuple):
        return value[0]
    if key in TEXT_KEYS and raw[:1] not in ("'", '"') and NOT_TEXT.fullmatch(raw):
        return "YAML reads '%s' as null, a boolean or a number, not text; %s" % (raw, QUOTE_HINT)
    if value == "":
        return "'%s' has an empty value" % key
    return key, value


def _value(raw):
    """Unquote a value. Returns the string, or a 1-tuple holding the error."""
    if not raw:
        return ""
    if raw[0] == '"':
        return _double_quoted(raw)
    if raw[0] == "'":
        return _single_quoted(raw)
    if raw[0] in INDICATORS:
        return ("a plain value cannot start with %r; %s" % (raw[0], QUOTE_HINT),)
    if re.search(r":\s", raw) or raw.endswith(":"):
        return ("plain value contains ': ' (or a colon before a tab) or ends with ':', "
                "which YAML reads as a nested key; %s"
                % QUOTE_HINT,)
    if " #" in raw or "\t#" in raw:
        return ("plain value contains ' #', which YAML reads as a comment; %s" % QUOTE_HINT,)
    return raw


def _double_quoted(raw):
    out, i = [], 1
    while i < len(raw):
        c = raw[i]
        if c == "\\":
            nxt = raw[i + 1:i + 2]
            if nxt not in ('"', "\\"):
                return ("unsupported escape '\\%s' in double quotes; only \\\" and \\\\ are allowed" % nxt,)
            out.append(nxt)
            i += 2
            continue
        if c == '"':
            return _closed("".join(out), raw[i + 1:])
        out.append(c)
        i += 1
    return ("double-quoted value is never closed",)


def _single_quoted(raw):
    out, i = [], 1
    while i < len(raw):
        if raw[i] == "'":
            if raw[i + 1:i + 2] == "'":
                out.append("'")
                i += 2
                continue
            return _closed("".join(out), raw[i + 1:])
        out.append(raw[i])
        i += 1
    return ("single-quoted value is never closed",)


def _closed(value, rest):
    if rest.strip():
        return ("text after the closing quote; put the whole value inside the quotes",)
    return value
