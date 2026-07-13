"""A focused new Agent that converts reviewed literature into testable experiments."""

from __future__ import annotations

import re
from dataclasses import dataclass

from paperagent.agents import BaseAgent


RESEARCH_GAP_STEP = "research_gap"
NEXT_EXPERIMENTS_HEADING = "## Next Experiments"


@dataclass(frozen=True)
class ResearchGapStageResult:
    text: str
    issues: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.issues

    def checkpoint_value(self) -> dict[str, str]:
        return {"step": RESEARCH_GAP_STEP, "text": self.text}


class ResearchGapAgent(BaseAgent):
    name = "ResearchGapAgent"
    role = "postdoc identifying evidence-backed research gaps and feasible experiments"

    def propose(self, topic: str, literature_text: str, count: int = 3) -> str:
        return self.ask(build_research_gap_prompt(topic, literature_text, count))


def build_research_gap_prompt(topic: str, literature_text: str, count: int = 3) -> str:
    count = max(1, min(count, 5))
    return f"""
Research topic: {topic}

검토가 끝난 문헌 자료:
{literature_text}

자료에서 공통 한계와 아직 해결되지 않은 문제를 찾아, 우리 스터디가 수행 가능한 후속 실험
{count}개를 제안하세요. 자료에 없는 사실이나 성능 수치는 만들지 마세요.

각 제안은 아래 형식을 정확히 사용하세요.

## Experiment N: 짧은 이름
- Research gap:
- Hypothesis:
- Baseline:
- Metric:
- Ablation:
- Minimum implementation:
- Risk:
- Evidence: 근거가 된 논문 제목 또는 arXiv ID

거대한 학습이나 비싼 데이터 수집이 필요한 제안보다 1~2주 안에 검증 가능한 토이 실험을 우선하세요.
""".strip()


def validate_gap_output(text: str, expected_count: int) -> list[str]:
    issues: list[str] = []
    experiment_count = text.count("## Experiment ")
    if experiment_count != expected_count:
        issues.append(f"실험 개수 불일치: expected={expected_count}, actual={experiment_count}")
    for field in ("Research gap", "Hypothesis", "Baseline", "Metric", "Ablation", "Risk", "Evidence"):
        if text.count(f"- {field}:") < expected_count:
            issues.append(f"필드 누락: {field}")
    return issues


def run_research_gap_stage(topic: str, literature_text: str, count: int = 3) -> ResearchGapStageResult:
    """Standalone contract for the workflow step JM will integrate."""
    text = ResearchGapAgent().propose(topic, literature_text, count)
    return ResearchGapStageResult(text=text, issues=tuple(validate_gap_output(text, count)))


def append_next_experiments(report_text: str, gap_text: str) -> str:
    """Insert or replace one Next Experiments section without creating another file."""
    section = f"{NEXT_EXPERIMENTS_HEADING}\n\n{gap_text.strip()}"
    existing = re.compile(
        rf"{re.escape(NEXT_EXPERIMENTS_HEADING)}\n.*?(?=\n## |\Z)",
        flags=re.DOTALL,
    )
    if existing.search(report_text):
        return existing.sub(section, report_text).rstrip() + "\n"

    insertion_points = ("## 6. Implementation", "## 7. Final Synthesis", "## Final Synthesis")
    for heading in insertion_points:
        marker = f"\n{heading}"
        if marker in report_text:
            return report_text.replace(marker, f"\n{section}\n\n{heading}", 1).rstrip() + "\n"
    return f"{report_text.rstrip()}\n\n{section}\n"
