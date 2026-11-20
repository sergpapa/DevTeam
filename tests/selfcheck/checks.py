"""Per-file and repo-wide checks for the plugin's own files.

Each check returns problem strings that start with the repo-relative path
and say what to change. An empty list means the file passes. Spec:
docs/specs/plugin-self-tests.md.
"""
import os
import re
import subprocess

from .frontmatter import parse
from .mojibake import find

SKILL_SIZE_CAP = 20480
DESCRIPTION_CAP = 1024
NAME_CAP = 64
SKILL_NAME = re.compile(r"[a-z0-9-]+")
TRIGGER = re.compile(r"\b(use (when|whenever|for|before|after)|invoke before)\b", re.IGNORECASE)
BOM = b"\xef\xbb\xbf"
CONTROL = frozenset(chr(c) for c in list(range(32)) + [127] if c not in (9, 10, 13))


def kind_of(relpath):
    """'skill', 'agent', 'style', or None for a file with no frontmatter rules."""
    parts = relpath.split("/")
    if len(parts) == 3 and parts[0] == "skills" and parts[2] == "SKILL.md":
        return "skill"
    if len(parts) == 2 and parts[1].endswith(".md"):
        return {"agents": "agent", "output-styles": "style"}.get(parts[0])
    return None


def check_file(relpath, data):
    """Frontmatter, name, trigger and size rules for one skill, agent or style file."""
    kind = kind_of(relpath)
    problems = []
    if kind == "skill" and len(data) > SKILL_SIZE_CAP:
        problems.append("%s: %d bytes, over the %d-byte cap; move detail into references/"
                        % (relpath, len(data), SKILL_SIZE_CAP))
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        return problems + ["%s: not valid UTF-8 at byte %d; re-save the file as UTF-8" % (relpath, e.start)]
    fields, errors = parse(text)
    if errors:
        return problems + ["%s: %s" % (relpath, e) for e in errors]
    for key in ("name", "description"):
        if key not in fields:
            problems.append("%s: missing required key '%s'" % (relpath, key))
    name, description = fields.get("name"), fields.get("description")
    if kind == "skill":
        problems += _skill_rules(relpath, name, description)
    elif kind == "agent" and name:
        stem = relpath.split("/")[1][:-len(".md")]
        if name != stem:
            problems.append("%s: name '%s' does not match its file name '%s.md'; rename one so they agree"
                            % (relpath, name, stem))
    return problems


def _skill_rules(relpath, name, description):
    problems = []
    directory = relpath.split("/")[1]
    if name:
        if not SKILL_NAME.fullmatch(name):
            problems.append("%s: name '%s' must use only lowercase letters, digits and hyphens"
                            % (relpath, name))
        if len(name) > NAME_CAP:
            problems.append("%s: name is %d characters; the limit is %d" % (relpath, len(name), NAME_CAP))
        if name != directory:
            problems.append("%s: name '%s' does not match its directory '%s'; rename one so they agree"
                            % (relpath, name, directory))
    if description:
        if not TRIGGER.search(description):
            problems.append("%s: description never says when to use the skill; add 'Use when ...' "
                            "(also accepted: Use whenever / for / before / after, Invoke before)" % relpath)
        if len(description) > DESCRIPTION_CAP:
            problems.append("%s: description is %d characters; the limit is %d"
                            % (relpath, len(description), DESCRIPTION_CAP))
    return problems


def check_encoding(relpath, data):
    """UTF-8 without BOM, no double-encoded characters, no control characters.

    A control character other than tab, LF or CR is almost always a typed escape
    (a regex word boundary, say) that got decoded on its way into the file.
    """
    if data.startswith(BOM):
        return ["%s:1: starts with a UTF-8 BOM; remove it" % relpath]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        return ["%s: not valid UTF-8 at byte %d; re-save the file as UTF-8" % (relpath, e.start)]
    problems = ["%s:%d:%d: double-encoded '%s' should be '%s'; redo the edit that wrote it with a UTF-8-safe tool"
                % (relpath, line, column, bad, good) for line, column, bad, good in find(text)]
    for number, line in enumerate(text.split(chr(10)), 1):  # splitlines() would eat VT, FF and FS-RS
        for column, char in enumerate(line, 1):
            if char in CONTROL:
                problems.append("%s:%d:%d: control character U+%04X; a typed escape was probably decoded on "
                                "the way in, so write it as an escape again (or build it with chr())"
                                % (relpath, number, column, ord(char)))
    return problems


def git_files(root):
    """Tracked files plus new files git would add, ignored ones excluded.

    Raises RuntimeError when git cannot list them: an empty list here would
    make the whole run report a pass without checking anything.
    """
    command = ["git", "-C", root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    try:
        out = subprocess.run(command, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        detail = getattr(e, "stderr", b"") or b""
        raise RuntimeError("git could not list the files in %s: %s %s"
                           % (root, e, detail.decode("utf-8", "replace").strip())) from e
    return sorted({p for p in out.decode("utf-8").split("\0") if p})


def check_repo(root):
    """Run every file check over the repo at root. Binary and deleted files are skipped."""
    problems = []
    for relpath in git_files(root):
        path = os.path.join(root, *relpath.split("/"))
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as f:
            data = f.read()
        if b"\0" in data:
            continue
        problems += check_encoding(relpath, data)
        if kind_of(relpath):
            problems += check_file(relpath, data)
    return problems
