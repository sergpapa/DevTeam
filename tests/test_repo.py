"""The real repo must pass every check, and the real descriptions must route
the prompt table correctly (spec criteria 1-6 and 8).

When a router case fails, the message shows the top three skills and their
scores. Fix the description that lost the prompt. Never delete or reword the
case to make it pass (spec criterion 8).
"""
import os
import re
import time
import unittest

from selfcheck import router
from selfcheck.checks import check_repo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "tests", "router", "cases.tsv")


def load_cases():
    cases = []
    with open(CASES, encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            prompt, expected = line.split("\t")
            cases.append((number, prompt, expected.split("|")))
    return cases


def eval_prompt_openings():
    """First sentence of every eval prompt (evals/*/prompt.md body or case.yaml prompt)."""
    openings = []
    evals = os.path.join(ROOT, "evals")
    for case in sorted(os.listdir(evals)):
        md, yml = os.path.join(evals, case, "prompt.md"), os.path.join(evals, case, "case.yaml")
        if os.path.isfile(md):
            with open(md, encoding="utf-8") as f:
                text = f.read().split("---", 2)[2].strip()
        elif os.path.isfile(yml):
            with open(yml, encoding="utf-8") as f:
                text = re.search(r"^\s*prompt:\s*(.+)$", f.read(), re.M).group(1).strip()
        else:
            continue
        openings.append(re.split(r"(?<=[.?!])\s", text, maxsplit=1)[0])
    return openings


def route_failures(skills, cases):
    failures = []
    for number, prompt, expected in cases:
        ranked = router.rank(prompt, skills)
        name, score = ranked[0]
        if expected == ["none"]:
            ok = score < router.THRESHOLD
        else:
            ok = name in expected and score >= router.THRESHOLD
        if not ok:
            top = ", ".join("%s %.2f" % pair for pair in ranked[:3])
            failures.append("cases.tsv:%d expected %s, got [%s] (threshold %.2f): %s"
                            % (number, "|".join(expected), top, router.THRESHOLD, prompt))
    return failures


class RealRepo(unittest.TestCase):
    def test_every_check_passes(self):
        problems = check_repo(ROOT)
        self.assertEqual([], problems, "\n" + "\n".join(problems))

    def test_case_table_covers_every_skill(self):
        skills = router.load_skills(ROOT)
        counts = dict.fromkeys(list(skills) + ["none"], 0)
        for number, _, expected in load_cases():
            for name in expected:
                self.assertIn(name, counts, "cases.tsv:%d names unknown skill %r" % (number, name))
            if len(expected) == 1:  # an "a|b" row proves neither description on its own
                counts[expected[0]] += 1
        thin = {name: n for name, n in counts.items() if n < (5 if name == "none" else 2)}
        self.assertEqual({}, thin, "need 2 single-skill cases per skill and 5 'none' cases")

    def test_every_eval_prompt_is_a_router_case(self):
        prompts = [p for _, p, _ in load_cases()]
        missing = [opening for opening in eval_prompt_openings()
                   if not any(p.startswith(opening) for p in prompts)]
        self.assertEqual([], missing)

    def test_readme_gives_the_command(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        self.assertTrue("python -m unittest discover -s tests" in readme,
                        "README.md does not give the self-test command")

    def test_every_prompt_routes_to_its_skill(self):
        failures = route_failures(router.load_skills(ROOT), load_cases())
        self.assertEqual([], failures, "\n" + "\n".join(failures))

    def test_whole_run_takes_under_five_seconds(self):
        start = time.perf_counter()
        check_repo(ROOT)
        route_failures(router.load_skills(ROOT), load_cases())
        self.assertLess(time.perf_counter() - start, 5.0)


class LoadSkills(unittest.TestCase):
    def test_reads_name_and_description_of_every_skill_directory(self):
        skills = router.load_skills(ROOT)
        dirs = sorted(d for d in os.listdir(os.path.join(ROOT, "skills"))
                      if os.path.isfile(os.path.join(ROOT, "skills", d, "SKILL.md")))
        self.assertEqual(dirs, sorted(skills))
        self.assertTrue(skills["project"].startswith("Whole-system pipeline"))
        self.assertIn("Use whenever a decision is made", skills["adr"])


if __name__ == "__main__":
    unittest.main()
