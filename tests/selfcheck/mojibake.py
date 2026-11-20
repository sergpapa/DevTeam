"""Find double-encoded UTF-8 (mojibake) in text.

Why: on Windows a UTF-8 character can be re-encoded byte by byte, so an em
dash ends up as three characters that look like line noise. DevTeam 2.0.3
shipped one in README.md. The damage is reversible: encode the run as
Windows-1252 and decode it as UTF-8, which is exactly how this detects it.
"""
import re


def _byte_of():
    """Map each character a Windows-1252 decode can yield to its byte (0x80-0xFF).

    The five bytes 1252 leaves undefined (0x81 0x8D 0x8F 0x90 0x9D) come
    through as their Latin-1 control characters, as Windows editors do.
    """
    table = {}
    for b in range(0x80, 0x100):
        try:
            ch = bytes([b]).decode("cp1252")
        except UnicodeDecodeError:
            ch = chr(b)
        table[ch] = b
    return table


BYTE_OF = _byte_of()
CONTINUATION = "".join(ch for ch, b in BYTE_OF.items() if b <= 0xBF)
# Lead bytes C2-F4 decode to the same characters in 1252 and Latin-1.
RUN = re.compile("[%s-%s][%s]{1,3}" % (chr(0xC2), chr(0xF4), re.escape(CONTINUATION)))
# A two-character run is short, and a letter followed by a curly quote or an
# ellipsis is ordinary German or French (sharp s before a closing quote decodes
# to an NKo letter). So a two-byte run counts only when it decodes to Latin
# (U+0080-U+027F), Greek (U+0370-U+03FF) or Cyrillic (U+0400-U+04FF), the
# scripts that actually get double-encoded in this repo's prose. Known miss
# the other way: a capital A-umlaut right before a closing quote still reads
# as mojibake for U+0113.
TWO_BYTE_TARGETS = ((0x80, 0x27F), (0x370, 0x4FF))


def _needed(lead):
    b = ord(lead)
    return 1 if b <= 0xDF else 2 if b <= 0xEF else 3


def find(text):
    """Return (line, column, bad_run, intended_char) for each run, 1-based, in order."""
    found = []
    for match in RUN.finditer(text):
        run = match.group()
        need = _needed(run[0])
        if len(run) - 1 < need:
            continue
        run = run[:need + 1]
        try:
            intended = bytes(BYTE_OF[ch] for ch in run).decode("utf-8")
        except UnicodeDecodeError:
            continue
        if need == 1 and not any(lo <= ord(intended) <= hi for lo, hi in TWO_BYTE_TARGETS):
            continue
        start = match.start()
        line = text.count("\n", 0, start) + 1
        column = start - text.rfind("\n", 0, start)
        found.append((line, column, run, intended))
    return found
