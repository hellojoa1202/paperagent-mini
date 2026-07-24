from team_tasks.JM.research_gap_agent import (
    NEXT_EXPERIMENTS_HEADING,
    append_next_experiments,
    build_research_gap_prompt,
    validate_gap_output,
    run_research_gap_stage,
    normalize_experiment_count,
)


def test_prompt_requests_feasible_evidence_backed_work() -> None:
    prompt = build_research_gap_prompt("topic", "literature", 2)
    assert "2개" in prompt
    assert "Evidence" in prompt
    assert "1~2주" in prompt

def test_prompt_uses_normalized_experiment_count() -> None:
    too_many_prompt = build_research_gap_prompt(
        "topic",
        "literature",
        count=10,
    )
    too_few_prompt = build_research_gap_prompt(
        "topic",
        "literature",
        count=0,
    )

    # 최대 5개, 최소 1개로 제한되는지 검사
    assert "후속 실험 5개" in too_many_prompt
    assert "후속 실험 1개" in too_few_prompt

def test_validator_detects_missing_fields() -> None:
    issues = validate_gap_output("### Experiment 1: test\n- Hypothesis: x", 1)
    assert any("Baseline" in issue for issue in issues)


def test_report_contains_only_one_next_experiments_section() -> None:
    report = "# Report\n\n## 7. Final Synthesis\n\nDone.\n"
    merged = append_next_experiments(report, "- Hypothesis: first")
    updated = append_next_experiments(merged, "- Hypothesis: revised")
    assert updated.count(NEXT_EXPERIMENTS_HEADING) == 1
    assert "revised" in updated
    assert "first" not in updated

def test_validator_requires_two_evidence_papers() -> None:
    text = """
### Common Research Gaps

#### Gap G1: test gap
- Description: test description
- Supporting papers: Paper A | Paper B

### Experiment 1: test experiment
- Target gap: G1
- Hypothesis: test hypothesis
- Baseline: test baseline
- Metric: accuracy
- Ablation: remove component
- Minimum implementation: toy implementation
- Risk: test risk
- Evidence: Paper A
""".strip()

    issues = validate_gap_output(text, 1)

    assert any(
        "근거 논문이 2편 미만" in issue
        for issue in issues
    )

def test_validator_rejects_unknown_target_gap() -> None:
    text = """
### Common Research Gaps

#### Gap G1: test gap
- Description: test description
- Supporting papers: Paper A | Paper B

### Experiment 1: test experiment
- Target gap: G2
- Hypothesis: test hypothesis
- Baseline: test baseline
- Metric: accuracy
- Ablation: remove component
- Minimum implementation: toy implementation
- Risk: test risk
- Evidence: Paper A | Paper B
""".strip()

    issues = validate_gap_output(text, 1)

    assert any(
        "정의되지 않은 Gap G2" in issue
        for issue in issues
    )

def test_report_replaces_full_next_experiments_section() -> None:
    report = """
# Report

## Next Experiments

### Common Research Gaps

#### Gap G1: old gap

### Experiment 1: old experiment
- Hypothesis: old hypothesis

## Final Synthesis

Done.
""".strip()

    new_gap_text = """
### Common Research Gaps

#### Gap G1: new gap

### Experiment 1: new experiment
- Hypothesis: new hypothesis
""".strip()

    updated = append_next_experiments(report, new_gap_text)

    assert updated.count(NEXT_EXPERIMENTS_HEADING) == 1
    assert "new hypothesis" in updated
    assert "old hypothesis" not in updated
    assert "## Final Synthesis" in updated

def test_validator_requires_two_supporting_papers() -> None:
    text = """
### Common Research Gaps

#### Gap G1: test gap
- Description: test description
- Supporting papers: Paper A

### Experiment 1: test experiment
- Target gap: G1
- Hypothesis: test hypothesis
- Baseline: test baseline
- Metric: accuracy
- Ablation: remove component
- Minimum implementation: toy implementation
- Risk: test risk
- Evidence: Paper A | Paper B
""".strip()

    issues = validate_gap_output(text, 1)

    assert any(
        "Gap G1의 Supporting papers가 2편 미만" in issue
        for issue in issues
    )

def test_stage_uses_injected_llm() -> None:
    calls: list[str] = []

    literature_text = (
        "## Paper A\n"
        "- Title: Paper A\n"
        "\n"
        "## Paper B\n"
        "- Title: Paper B"
    )

    def fake_llm(prompt: str) -> str:
        calls.append(prompt)

        return """
### Common Research Gaps

#### Gap G1: test gap
- Description: test description
- Supporting papers: Paper A | Paper B

### Experiment 1: test experiment
- Target gap: G1
- Hypothesis: test hypothesis
- Baseline: test baseline
- Metric: accuracy
- Ablation: remove component
- Minimum implementation: toy implementation
- Risk: test risk
- Evidence: Paper A | Paper B
""".strip()

    result = run_research_gap_stage(
        topic="test topic",
        literature_text=literature_text,
        count=1,
        ask_fn=fake_llm,
    )

    assert result.passed
    assert len(calls) == 1
    assert "test topic" in calls[0]
    assert literature_text in calls[0]
    assert "Paper A" in calls[0]
    assert "Paper B" in calls[0]

def test_validator_rejects_unknown_evidence_reference() -> None:
    literature = """
## Paper A
- Title: Efficient Transformer A

## Paper B
- Title: Efficient Transformer B
""".strip()

    output = """
### Common Research Gaps

#### Gap G1: missing large-scale evaluation
- Description: large-scale evaluation is missing
- Supporting papers: Efficient Transformer A | Efficient Transformer B

### Experiment 1: large-scale evaluation
- Target gap: G1
- Hypothesis: performance will decrease on larger datasets
- Baseline: original models
- Metric: accuracy
- Ablation: dataset scale
- Minimum implementation: two datasets
- Risk: increased computation
- Evidence: Efficient Transformer A | Efficient, Transformer B
""".strip()

    issues = validate_gap_output(
        output,
        expected_count=1,
        literature_text=literature,
    )

    assert any(
        "Evidence가 입력 문헌에 없습니다: Efficient, Transformer B"
        in issue
        for issue in issues
    )

def test_validator_accepts_references_from_input() -> None:
    literature = """
## Paper A
- Title: Efficient Transformer A

## Paper B
- Title: Efficient Transformer B
""".strip()

    output = """
### Common Research Gaps

#### Gap G1: missing ablation
- Description: both papers omit ablation studies
- Supporting papers: Efficient Transformer A | Efficient Transformer B

### Experiment 1: component ablation
- Target gap: G1
- Hypothesis: the core component improves accuracy
- Baseline: original models
- Metric: accuracy
- Ablation: remove the core component
- Minimum implementation: one dataset and two configurations
- Risk: implementation differences
- Evidence: Efficient Transformer A | Efficient Transformer B
""".strip()

    issues = validate_gap_output(
        output,
        expected_count=1,
        literature_text=literature,
    )

    assert not any(
        "입력 문헌에 없습니다" in issue
        for issue in issues
    )

def test_validator_rejects_empty_experiment_field() -> None:
    literature = """
## Paper A
- Title: Paper A

## Paper B
- Title: Paper B
""".strip()

    output = """
### Common Research Gaps

#### Gap G1: test gap
- Description: common limitation
- Supporting papers: Paper A | Paper B

### Experiment 1: test experiment
- Target gap: G1
- Hypothesis:
- Baseline: baseline model
- Metric: accuracy
- Ablation: remove component
- Minimum implementation: toy experiment
- Risk: implementation error
- Evidence: Paper A | Paper B
""".strip()

    issues = validate_gap_output(
        output,
        expected_count=1,
        literature_text=literature,
    )

    assert any(
        "Experiment 1의 필드가 비어 있습니다: Hypothesis" in issue
        for issue in issues
    )

def test_validator_rejects_missing_experiment_field() -> None:
    literature = """
- Title: Paper A
- Title: Paper B
""".strip()

    output = """
### Common Research Gaps

#### Gap G1: test gap
- Description: common limitation
- Supporting papers: Paper A | Paper B

### Experiment 1: test experiment
- Target gap: G1
- Hypothesis: test hypothesis
- Baseline: baseline model
- Ablation: remove component
- Minimum implementation: toy experiment
- Risk: implementation error
- Evidence: Paper A | Paper B
""".strip()

    issues = validate_gap_output(output, 1, literature)

    assert any(
        "Experiment 1의 필드가 누락되었습니다: Metric" in issue
        for issue in issues
    )

def test_empty_report_gets_next_experiments_heading() -> None:
    gap_text = """
### Common Research Gaps

#### Gap G1: test gap
""".strip()

    report = append_next_experiments(
        "# Research Report\n",
        gap_text,
    )

    assert report.startswith("# Research Report")
    assert report.count(NEXT_EXPERIMENTS_HEADING) == 1
    assert "#### Gap G1: test gap" in report

def test_experiment_count_is_clamped() -> None:
    assert normalize_experiment_count(-3) == 1
    assert normalize_experiment_count(0) == 1
    assert normalize_experiment_count(1) == 1
    assert normalize_experiment_count(3) == 3
    assert normalize_experiment_count(5) == 5
    assert normalize_experiment_count(10) == 5