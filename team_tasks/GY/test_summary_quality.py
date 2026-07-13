from team_tasks.GY.summary_quality import QualityScore, build_review_prompt, build_summary_prompt


def test_prompt_contains_source_and_feedback() -> None:
    prompt = build_summary_prompt("title", "abstract", "feedback")
    assert "abstract" in prompt
    assert "feedback" in prompt
    assert "## Limitations" in prompt


def test_quality_total_penalizes_hallucination() -> None:
    low_risk = QualityScore(8, 8, 8, 8, 1, "")
    high_risk = QualityScore(8, 8, 8, 8, 9, "")
    assert low_risk.total > high_risk.total
    assert "hallucination_risk" in build_review_prompt("a", "s")
