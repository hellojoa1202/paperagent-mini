from __future__ import annotations

from paperagent.agents import PaperSummary
from paperagent.research_gap import (
    NEXT_EXPERIMENTS_HEADING,
    append_next_experiments,
    run_research_gap_stage,
    validate_gap_output,
)
from paperagent.workflow import _build_research_gap_source


SOURCE = """
- Title: Paper A
- arXiv ID: 2401.00001
- Title: Paper B
- arXiv ID: 2401.00002
""".strip()

VALID_OUTPUT = """
### Common Research Gaps

#### Gap G1: 공통 평가 부족
- Description: 두 논문 모두 동일한 평가 기준이 부족함
- Supporting papers: Paper A | Paper B

### Experiment 1: 공통 평가
- Target gap: G1
- Hypothesis: 동일 기준으로 차이가 드러남
- Baseline: 원 논문의 설정
- Metric: 정확도
- Ablation: 구성 요소 제거
- Minimum implementation: 작은 공개 데이터로 비교
- Risk: 데이터 편향
- Evidence: Paper A | Paper B
""".strip()


def test_validate_gap_output_accepts_known_references() -> None:
    assert validate_gap_output(VALID_OUTPUT, 1, SOURCE) == []


def test_stage_repairs_invalid_first_response() -> None:
    responses = iter(("형식이 없는 답변", VALID_OUTPUT))

    result = run_research_gap_stage(
        "topic",
        SOURCE,
        count=1,
        ask_fn=lambda _prompt: next(responses),
    )

    assert result.passed
    assert "Experiment 1" in result.text


def test_append_next_experiments_does_not_create_another_file() -> None:
    report = "# Report\n\n## 7. Final Synthesis\n\n끝\n"
    updated = append_next_experiments(report, VALID_OUTPUT)

    assert NEXT_EXPERIMENTS_HEADING in updated
    assert updated.index(NEXT_EXPERIMENTS_HEADING) < updated.index("## 7. Final Synthesis")


def test_workflow_builds_exact_citable_source() -> None:
    summaries = [
        PaperSummary("2401.00001", "Paper A", "a", "요약 A"),
        PaperSummary("2401.00002", "Paper B", "b", "요약 B"),
    ]

    source = _build_research_gap_source("문헌 종합", summaries)

    assert "- Title: Paper A" in source
    assert "- arXiv ID: 2401.00002" in source

