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
TAB = chr(9)


def load_cases():
    """(line number, prompt, expected skills, expected miss) for each row of cases.tsv.

    A third column 'miss' marks a prompt a word matcher is known to misroute.
    """
    cases = []
    with open(CASES, encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            fields = line.split(TAB)
            if len(fields) not in (2, 3) or fields[2:] not in ([], ["miss"]):
                raise ValueError("cases.tsv:%d needs prompt<TAB>expected[<TAB>miss]" % number)
            cases.append((number, fields[0], fields[1].split("|"), fields[2:] == ["miss"]))
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
    """A case routes only if an expected skill strictly outscores every other skill.

    A tie or an all-zero ranking would otherwise pass by alphabetical order.
    An expected-miss row fails the other way: once it routes, promote it.
    """
    failures = []
    for number, prompt, expected, miss in cases:
        ranked = router.rank(prompt, skills)
        best_expected = max(score for name, score in ranked if name in expected)
        best_other = max([score for name, score in ranked if name not in expected] or [0.0])
        routes = best_expected > best_other
        top = ", ".join("%s %.2f" % pair for pair in ranked[:3])
        if miss and routes:
            failures.append("cases.tsv:%d now routes to %s [%s]; promote it by deleting its 'miss' column: %s"
                            % (number, "|".join(expected), top, prompt))
        elif not miss and not routes:
            failures.append("cases.tsv:%d expected %s, got [%s]: %s"
                            % (number, "|".join(expected), top, prompt))
    return failures


class RealRepo(unittest.TestCase):
    def test_every_check_passes(self):
        problems = check_repo(ROOT)
        self.assertEqual([], problems, "\n" + "\n".join(problems))

    def test_case_table_covers_every_skill(self):
        skills = router.load_skills(ROOT)
        counts = dict.fromkeys(skills, 0)
        for number, _, expected, miss in load_cases():
            for name in expected:
                self.assertIn(name, counts, "cases.tsv:%d names unknown skill %r" % (number, name))
            if len(expected) == 1 and not miss:  # "a|b" and miss rows prove nothing on their own
                counts[expected[0]] += 1
        thin = {name: n for name, n in counts.items() if n < 2}
        self.assertEqual({}, thin, "need 2 single-skill cases per skill")

    def test_every_eval_prompt_is_a_router_case(self):
        prompts = [case[1] for case in load_cases()]
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


class RouteFailures(unittest.TestCase):
    """The pass rule itself, on toy skills, so a wrong rule cannot hide behind real data."""
    SKILLS = {"adr": "Record an architecture decision.", "debug": "Find why a bug happens.",
              "retro": "Turn a repeated mistake into a rule."}

    def test_clear_winner_passes(self):
        self.assertEqual([], route_failures(self.SKILLS, [(1, "record this decision", ["adr"], False)]))

    def test_wrong_winner_fails(self):
        self.assertEqual(1, len(route_failures(self.SKILLS, [(1, "record this decision", ["debug"], False)])))

    def test_tie_and_no_match_fail_even_when_alphabetical_order_favours_expected(self):
        tie = {"adr": "alpha", "retro": "alpha"}
        self.assertEqual(1, len(route_failures(tie, [(1, "alpha", ["adr"], False)])))
        self.assertEqual(1, len(route_failures(self.SKILLS, [(1, "zebra", ["adr"], False)])))

    def test_either_of_several_expected_skills_may_win(self):
        self.assertEqual([], route_failures(self.SKILLS, [(1, "record this decision", ["debug", "adr"], False)]))

    def test_expected_miss_that_still_misses_passes(self):
        self.assertEqual([], route_failures(self.SKILLS, [(1, "zebra", ["adr"], True)]))
        self.assertEqual([], route_failures(self.SKILLS, [(1, "record this decision", ["debug"], True)]))

    def test_expected_miss_that_now_routes_fails_and_asks_to_promote(self):
        failures = route_failures(self.SKILLS, [(7, "record this decision", ["adr"], True)])
        self.assertEqual(1, len(failures))
        self.assertIn("cases.tsv:7", failures[0])
        self.assertIn("promote", failures[0])


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
