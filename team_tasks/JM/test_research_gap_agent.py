from team_tasks.JM.research_gap_agent import build_research_gap_prompt, validate_gap_output


def test_prompt_requests_feasible_evidence_backed_work() -> None:
    prompt = build_research_gap_prompt("topic", "literature", 2)
    assert "2개" in prompt
    assert "Evidence" in prompt
    assert "1~2주" in prompt


def test_validator_detects_missing_fields() -> None:
    issues = validate_gap_output("## Experiment 1: test\n- Hypothesis: x", 1)
    assert any("Baseline" in issue for issue in issues)
