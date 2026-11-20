"""Lexical stand-in for how a prompt picks a skill: BM25 over the descriptions.

Why: the model routes a prompt to a skill by reading the descriptions, and a
description edit can quietly stop a skill from firing. A model-based check
costs money on every run; this one is free and catches the same class of
drift (a skill losing its words, two skills colliding). It is a proxy: it
cannot read negation ("skip for typos") or intent, so its case table holds
only prompts a word-matcher can fairly be asked to route.
"""
import math
import os
import re
from collections import Counter

from .frontmatter import parse

K1 = 1.2
B = 0.75
STOPWORDS = frozenset("""
a about after again all also am an and any are as at be been before being but by can
could did do does doing for from get gets got had has have having he her here him his how
i if in into is it its just me more my no not now of on once one only or our out over
please should so some such than that the their them then there these they this those
through to too up us very was we were what when where which while who why will with
would you your
""".split())


VOWELS = frozenset("aeiouy")


def _stem(word):
    """Strip one common English suffix and a final 'e', so 'used', 'using' and 'use' meet.

    'ing'/'ed' come off only when a vowel is left ('string' stays) and not
    after an 'e' ('need', 'speed' stay). A doubled final consonant is undone
    on stems over three letters ('committed' meets 'commit', 'added' stays 'add').
    """
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    for suffix in ("ing", "ed"):
        if word.endswith(suffix):
            stem = word[:-len(suffix)]
            if (suffix == "ed" and stem.endswith("e")) or not VOWELS & set(stem):
                break
            if len(stem) > 3 and stem[-1] == stem[-2] and stem[-1] not in "lsz" + "".join(VOWELS):
                stem = stem[:-1]
            return _drop_e(stem)
    if word.endswith("s") and not word.endswith(("ss", "us", "is")) and len(word) > 3:
        word = word[:-1]
    return _drop_e(word)


def _drop_e(word):
    return word[:-1] if len(word) > 2 and word.endswith("e") else word


def tokens(text):
    """Lowercase letter-or-digit runs (any script), stemmed; stopwords and single letters dropped.

    Single letters are dropped because they are mostly debris ("user's" gives
    "s", "ctrl+s" gives "s") and would match each other across unrelated text.
    """
    return [_stem(w) for w in re.findall(r"[^\W_]+", text.lower())
            if len(w) > 1 and w not in STOPWORDS]


def rank(prompt, skills):
    """Score every skill for prompt, best first; ties keep the input order."""
    docs = {name: tokens(name + " " + description) for name, description in skills.items()}
    if not docs:
        return []
    avg_len = sum(len(d) for d in docs.values()) / len(docs) or 1.0
    df = Counter(t for d in docs.values() for t in set(d))
    query = set(tokens(prompt))
    scored = []
    for name, doc in docs.items():
        tf = Counter(doc)
        score = 0.0
        for term in query:
            if tf[term]:
                idf = math.log(1 + (len(docs) - df[term] + 0.5) / (df[term] + 0.5))
                norm = K1 * (1 - B + B * len(doc) / avg_len)
                score += idf * tf[term] * (K1 + 1) / (tf[term] + norm)
        scored.append((name, score))
    return sorted(scored, key=lambda pair: -pair[1])


def load_skills(root):
    """{directory: description} for every skills/<dir>/SKILL.md under root.

    Keyed by directory so two skills that share a name cannot overwrite each
    other (the name check reports the clash). Raises ValueError on frontmatter
    that does not parse: routing on an empty description would blame the
    wrong cause.
    """
    skills = {}
    base = os.path.join(root, "skills")
    for directory in sorted(os.listdir(base)):
        path = os.path.join(base, directory, "SKILL.md")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                fields, errors = parse(f.read())
            if errors:
                raise ValueError("skills/%s/SKILL.md frontmatter does not parse: %s"
                                 % (directory, "; ".join(errors)))
            skills[directory] = fields.get("description", "")
    return skills
