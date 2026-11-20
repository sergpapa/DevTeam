"""Pins the retro contract in the skill text (docs/specs/retro-that-runs.md).

The behaviour lives in prose, so these tests pin the rule sentences that prose
must keep: where /feature's retro check sits, what it prints when clean, the bar
a lesson must clear, and the order of the cheapest-form ladder. A rule is pinned
as one sentence holding all its parts, so a sentence that mentions the words but
says the opposite does not pass. Wording can still change freely around them.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEGATION = r"(?i)\b(never|not|no|don't|do not|without)\b"


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def sections(text, level=2):
    """[(heading, body)] for each heading of exactly `level`, ignoring fenced code."""
    text = re.sub(r"^```.*?^```", "", text, flags=re.M | re.S)
    matches = list(re.finditer(r"^#{%d}\s+(.+)$" % level, text, re.M))
    ends = [m.start() for m in matches[1:]] + [len(text)]
    return [(m.group(1).strip(), text[m.end():end]) for m, end in zip(matches, ends)]


def section_index(secs, pattern):
    hits = [i for i, (heading, _) in enumerate(secs) if re.search(pattern, heading, re.I)]
    return hits[0] if hits else None


def section(secs, pattern):
    i = section_index(secs, pattern)
    return "" if i is None else secs[i][1]


def sentences(text):
    """Split prose into sentences and list items, so one rule is checked as one unit."""
    parts = re.split(r"(?<=[.!?])[`*]*\s+|\n\s*\n|\n(?=\s*(?:[-*]|\d+\.)\s)", text)
    return [p.strip() for p in parts if p.strip()]


def sentence_with(text, *patterns):
    """First sentence matching every pattern (case-insensitive), or None."""
    for s in sentences(text):
        if all(re.search(p, s, re.I) for p in patterns):
            return s
    return None


def ladder(body):
    """The contiguous numbered list that starts at '1.', one entry per item."""
    start = re.search(r"^1\.\s", body, re.M)
    if not start:
        return []
    block = []
    for line in body[start.start():].splitlines():
        if re.match(r"\d+\.\s", line) or (block and re.match(r"\s+\S", line)):
            block.append(line)
        else:
            break
    return [item.strip() for item in re.split(r"^\d+\.\s+", "\n".join(block), flags=re.M)[1:]]


class Pins(unittest.TestCase):
    def assertRule(self, text, why, *patterns):
        """Some sentence holds every pattern and is not negated."""
        found = sentence_with(text, *patterns)
        self.assertIsNotNone(found, why)
        return found

    def assertPositiveRule(self, text, why, *patterns):
        found = self.assertRule(text, why, *patterns)
        self.assertNotRegex(found, NEGATION, why + " (the rule sentence is negated)")

    def read_or_fail(self, *parts):
        path = os.path.join(ROOT, *parts)
        if not os.path.isfile(path):
            self.fail("missing %s" % os.path.relpath(path, ROOT))
        return read(*parts)


class FeatureEndsWithRetroCheck(Pins):
    """Criterion 1: /feature runs the check after the commit, before the report."""

    def setUp(self):
        self.secs = sections(read("skills", "feature", "SKILL.md"))
        self.body = section(self.secs, r"retro check")
        self.assertTrue(self.body, "skills/feature/SKILL.md has no '## ... Retro check' section")

    def test_section_sits_after_stage_6_and_before_final_report(self):
        stage6 = section_index(self.secs, r"^stage 6")
        retro = section_index(self.secs, r"retro check")
        final = section_index(self.secs, r"final report")
        for name, index in (("Stage 6", stage6), ("Retro check", retro), ("Final report", final)):
            self.assertIsNotNone(index, "skills/feature/SKILL.md has no '## %s' section" % name)
        self.assertLess(stage6, retro, "the retro check must come after the Stage 6 commit")
        self.assertLess(retro, final, "the retro check must come before the final report")

    def test_runs_inline_without_a_subagent(self):
        self.assertRule(self.body, "the check must say it runs in the main session with no subagent",
                        r"main session", r"\bno subagent|without (a |any )?subagent")

    def test_reads_the_slice_record_and_user_corrections(self):
        self.assertRule(self.body, "the check must read the slice record and its findings",
                        r"docs/specs/", r"review|finding", r"refus")
        self.assertPositiveRule(self.body, "the check must read the user's corrections", r"correction")

    def test_counts_recurrence_across_earlier_slices(self):
        self.assertPositiveRule(self.body, "one hit per slice must still add up: the check must search earlier slice records",
                                r"earlier slice|previous slice|other slice", r"docs/specs/|slice record")

    def test_stage_6_no_longer_claims_to_end_the_pipeline(self):
        stage6 = section(self.secs, r"^stage 6")
        self.assertNotRegex(stage6, r"(?i)pipeline ends at a local commit\b",
                            "Stage 6 must not say the pipeline ends there; Stage 7 follows it")

    def test_applies_the_retro_bar(self):
        self.assertPositiveRule(self.body, "the check must hold candidates against /retro's bar",
                                r"(against|apply|applies|hold)[^.]{0,60}durable-lesson bar")

    def test_clean_slice_prints_one_retro_line(self):
        self.assertRule(self.body, "when nothing clears the bar, the whole output must be one 'Retro:' line",
                        r"when nothing", r"one[- ]line|single line", r"whole output|only output|nothing else",
                        r"Retro:")

    def test_hands_lessons_to_retro_at_stage_2(self):
        self.assertPositiveRule(self.body, "lessons must go to /retro starting at Stage 2",
                                r"/retro", r"stage 2")

    def test_nothing_is_applied_before_approval(self):
        self.assertRule(self.body, "nothing may be applied before the user approves it",
                        r"(nothing|no change)[^.]{0,40}appl[^.]{0,60}(before|until|without)[^.]{0,40}approv")

    def test_approved_changes_get_their_own_commit(self):
        self.assertRule(self.body, "approved retro changes must not ride in the slice's commit",
                        r"(own|separate) commit")

    def test_final_report_carries_the_retro_line(self):
        report = section(self.secs, r"final report")
        self.assertPositiveRule(report, "the final report must include the retro line",
                                r"Retro:|retro line")


class RetroBar(Pins):
    """Criterion 2: the durable-lesson bar and its three tests."""

    def setUp(self):
        self.text = read("skills", "retro", "SKILL.md")
        secs = sections(self.text)
        self.bar = section(secs, r"durable-lesson bar")
        self.stage1 = section(secs, r"^stage 1")
        self.assertTrue(self.bar, "skills/retro/SKILL.md has no '## Durable-lesson bar' section")

    def test_occurrence_allows_two_hits_or_one_costly_hit(self):
        found = self.assertRule(self.bar, "the bar must accept 2+ hits, or once if it cost money, data, or a review escape",
                                r"\b(2|two)\b", r"\bonce\b", r"money", r"data", r"review")
        self.assertRegex(found, r"(?i)\b(2|two)\b[^.]{0,40}\bor once\b",
                         "the one-costly-hit clause must be an alternative ('or once'), not a restriction")

    def test_transfer_to_a_different_task(self):
        self.assertPositiveRule(self.bar, "the bar must require that a future session on a different task acts differently",
                                r"(different|another|unrelated) task", r"act differently|behave differently|do differently")

    def test_existing_rule_is_fixed_not_twinned(self):
        self.assertRule(self.bar, "an existing rule that still failed must be fixed or converted, not twinned",
                        r"existing rule|that rule", r"fail", r"\b(fix|fixes|convert|converts)\b",
                        r"instead of (adding )?a twin|rather than (adding )?a twin")

    def test_a_covered_lesson_whose_rule_failed_still_clears_the_bar(self):
        self.assertPositiveRule(self.bar, "a lesson whose existing rule failed must pass the bar, or the fix-that-rule path never runs",
                                r"(existing rule|that rule)[^.]{0,80}(failed|fail)", r"(clears|passes) the bar|still (clears|passes)")
        self.assertNotRegex(self.bar, r"(?i)no existing rule says it",
                            "this wording screens out a lesson whose rule failed")

    def test_habit_only_wording_is_gone(self):
        self.assertNotRegex(self.text, r"(?i)\bhabit is\b", "'a habit is' contradicts the one-costly-hit clause")
        self.assertNotRegex(self.text, r"(?i)keep only the recurring",
                            "Stage 1 must not drop a single costly hit")

    def test_stage_1_keeps_what_clears_the_bar(self):
        self.assertPositiveRule(self.stage1, "Stage 1 must keep what clears the durable-lesson bar",
                                r"keep", r"bar")


class RetroLadder(Pins):
    """Criteria 3 and 4: Stage 2 climbs test, hook, skill, CLAUDE.md in that order."""
    RUNGS = (r"\btest", r"\bhook", r"\bskill", r"claude\.md")

    def setUp(self):
        secs = sections(read("skills", "retro", "SKILL.md"))
        self.stage2 = section(secs, r"^stage 2")
        self.stage3 = section(secs, r"^stage 3")
        self.items = ladder(self.stage2)

    def test_exactly_four_rungs_in_order(self):
        self.assertEqual(4, len(self.items), "Stage 2 must hold one numbered ladder of exactly 4 rungs")
        for position, (rung, item) in enumerate(zip(self.RUNGS, self.items), 1):
            head = item[:120].lower()
            seen = {r: m.start() for r in self.RUNGS for m in [re.search(r, head)] if m}
            self.assertEqual(rung, min(seen, key=seen.get) if seen else None,
                             "rung %d must lead with %s, found: %s" % (position, rung, head))

    def test_hook_rung_covers_lint_and_config_gates(self):
        self.assertGreaterEqual(len(self.items), 2, "Stage 2 has no numbered hook rung")
        self.assertRegex(self.items[1], r"(?i)lint", "the hook rung must include lint rules")
        self.assertRegex(self.items[1], r"(?i)config", "the hook rung must include config gates")

    def test_hook_rung_runs_locally_and_excludes_ci(self):
        self.assertGreaterEqual(len(self.items), 2, "Stage 2 has no numbered hook rung")
        self.assertRegex(self.items[1], r"(?i)\blocal", "the hook rung must run on this machine")
        self.assertRegex(self.items[1], r"(?i)\bCI\b[^.]{0,80}(not|never|bills)|(not|never)[^.]{0,40}\bCI\b",
                         "a CI workflow is not a free rung: it bills on every push")

    def test_stop_at_the_first_rung_that_holds(self):
        self.assertPositiveRule(self.stage2, "the ladder must stop at the first rung that can hold the lesson",
                                r"stop at the first rung")

    def test_upper_rungs_say_why_a_lower_rung_cannot_hold_it(self):
        self.assertRule(self.stage2, "a proposal on rung 3 or 4 must say why a lower rung cannot hold it",
                        r"rung 3 or 4|rungs 3 and 4", r"\bwhy\b", r"lower rung", r"cannot|can't")

    def test_project_facts_sit_outside_the_ladder(self):
        found = self.assertRule(self.stage2, "project facts must go to an ADR or the roadmap, outside the ladder",
                                r"outside the ladder")
        self.assertRegex(self.stage2, r"/adr", "a project decision still goes to an ADR")
        self.assertRegex(self.stage2, r"(?i)roadmap", "project status still goes to the roadmap")
        self.assertNotRegex("\n".join(self.items), r"(?i)/adr|roadmap", "ADR and roadmap are not rungs")
        self.assertTrue(found)

    def test_a_lesson_that_fits_no_rung_is_dropped(self):
        self.assertRule(self.stage2, "a lesson that fits no rung must be dropped",
                        r"fits no rung|no rung fits", r"\bdrop")

    def test_proposals_name_their_rung(self):
        found = self.assertRule(self.stage3, "Stage 3 proposals must name their rung with the target file and change",
                                r"\brung\b", r"target file|exact change")
        self.assertNotRegex(found, r"(?i)\bno rung\b")


class RetroEvalCase(Pins):
    """Criterion 5: the case that rewards a check over a prose rule exists and can pass."""
    CASE = ("evals", "retro-prefers-check-over-prose")

    def test_prompt_is_well_formed_and_never_names_the_skill(self):
        prompt = self.read_or_fail(*self.CASE, "prompt.md")
        parts = prompt.split("---", 2)
        self.assertEqual(3, len(parts), "prompt.md needs --- frontmatter ---")
        front, body = parts[1], parts[2]
        self.assertRegex(front, r"(?m)^description:\s*\S")
        self.assertRegex(front, r"(?m)^allowed_tools:.*\bSkill\b",
                         "without Skill in allowed_tools the skill-fired grader can never pass")
        self.assertNotRegex(body, r"(?i)retro", "an eval prompt must not name the skill")
        self.assertRegex(body, r"(?i)\bagain\b|twice|three times|third time|keeps? happening",
                         "the prompt must describe a mistake that recurred")

    def test_skill_fired_grader_checks_the_retro_skill(self):
        grader = self.read_or_fail(*self.CASE, "graders", "skill-fired.md")
        self.assertRegex(grader, r"(?m)^type: tool_used$")
        self.assertRegex(grader, r"(?m)^tool: Skill$")
        self.assertRegex(grader, r"(?m)^input_match:.*\bretro\b")

    def test_criteria_grader_fails_a_prose_first_fix(self):
        grader = self.read_or_fail(*self.CASE, "graders", "criteria.md")
        self.assertRegex(grader, r"(?m)^type: llm$")
        passes = "\n".join(re.findall(r"(?m)^PASS\b.*$", grader))
        fails = "\n".join(re.findall(r"(?m)^FAIL\b.*$", grader))
        self.assertRegex(passes, r"(?i)first\b[^\n]{0,80}(automated check|test|lint|hook)",
                         "PASS must require the first fix to be an automated check")
        self.assertRegex(passes, r"(?i)names? (its|the) file", "PASS must require the file to be named")
        self.assertRegex(passes, r"(?i)asks? (before|for approval)", "PASS must require asking before applying")
        self.assertRegex(fails, r"(?i)main fix is a prose rule|prose rule is the (main|first) fix",
                         "FAIL must catch a prose-first fix")
        self.assertRegex(fails, r"(?i)prose[^\n]{0,80}without[^\n]{0,60}why",
                         "FAIL must catch a prose rule with no reason a check cannot hold it")


class ReadmeRows(Pins):
    """Criterion 7: the README tells people the check exists."""

    def setUp(self):
        self.rows = {m.group(1): m.group(0) for m in
                     re.finditer(r"^\| `(/[a-z]+)` \|.*$", read("README.md"), re.M)}

    def test_feature_row_lists_the_retro_check(self):
        self.assertRegex(self.rows["/feature"], r"(?i)retro check")

    def test_retro_row_says_feature_runs_it_every_slice(self):
        self.assertRegex(self.rows["/retro"], r"/feature`? runs[^|]{0,60}every slice")


if __name__ == "__main__":
    unittest.main()
