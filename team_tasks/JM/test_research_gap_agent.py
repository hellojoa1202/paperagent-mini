from team_tasks.JM.research_gap_agent import (
    NEXT_EXPERIMENTS_HEADING,
    append_next_experiments,
    build_research_gap_prompt,
    validate_gap_output,
)


def test_prompt_requests_feasible_evidence_backed_work() -> None:
    prompt = build_research_gap_prompt("topic", "literature", 2)
    assert "2개" in prompt
    assert "Evidence" in prompt
    assert "1~2주" in prompt


def test_validator_detects_missing_fields() -> None:
    issues = validate_gap_output("## Experiment 1: test\n- Hypothesis: x", 1)
    assert any("Baseline" in issue for issue in issues)


def test_report_contains_only_one_next_experiments_section() -> None:
    report = "# Report\n\n## 7. Final Synthesis\n\nDone.\n"
    merged = append_next_experiments(report, "- Hypothesis: first")
    updated = append_next_experiments(merged, "- Hypothesis: revised")
    assert updated.count(NEXT_EXPERIMENTS_HEADING) == 1
    assert "revised" in updated
    assert "first" not in updated
