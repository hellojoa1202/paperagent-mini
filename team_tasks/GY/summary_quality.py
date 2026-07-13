"""Prompt laboratory for improving PaperReader/Reviewer reflection quality."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from paperagent.agents import strip_code_fence
from paperagent.llm import ask_llm


@dataclass(frozen=True)
class QualityScore:
    accuracy: int
    coverage: int
    specificity: int
    clarity: int
    hallucination_risk: int
    feedback: str

    @property
    def total(self) -> float:
        positive = self.accuracy + self.coverage + self.specificity + self.clarity
        return round((positive + (10 - self.hallucination_risk)) / 5, 2)


def build_summary_prompt(title: str, abstract: str, feedback: str = "") -> str:
    """This is the main prompt GY should tune and compare."""
    return f"""
논문 제목: {title}
원문 초록: {abstract}
이전 Reviewer 피드백: {feedback or "없음"}

원문에 있는 사실만 사용하여 한국어 요약을 작성하세요.
각 섹션은 1~3개의 짧은 불릿으로 작성합니다.

## Problem
## Key idea
## Method
## Experiments or evidence
## Limitations
""".strip()


def build_review_prompt(abstract: str, summary: str) -> str:
    return f"""
원문 초록:
{abstract}

평가할 요약:
{summary}

다음 JSON 형식만 반환하세요. 모든 점수는 1~10입니다.
{{
  "accuracy": 1,
  "coverage": 1,
  "specificity": 1,
  "clarity": 1,
  "hallucination_risk": 1,
  "feedback": "근거가 있는 구체적인 수정 지시"
}}
""".strip()


def generate_summary(title: str, abstract: str, feedback: str = "") -> str:
    return ask_llm(
        "You are PaperReaderAgent. Use Korean and necessary English terms only.",
        build_summary_prompt(title, abstract, feedback),
    )


def score_summary(abstract: str, summary: str) -> QualityScore:
    raw = ask_llm(
        "You are a strict ReviewerAgent. Judge only against the supplied abstract.",
        build_review_prompt(abstract, summary),
    )
    data = json.loads(strip_code_fence(raw))
    return QualityScore(
        accuracy=_score(data, "accuracy"),
        coverage=_score(data, "coverage"),
        specificity=_score(data, "specificity"),
        clarity=_score(data, "clarity"),
        hallucination_risk=_score(data, "hallucination_risk"),
        feedback=str(data.get("feedback", "")).strip(),
    )


def run_reflection(title: str, abstract: str) -> dict[str, object]:
    first = generate_summary(title, abstract)
    before = score_summary(abstract, first)
    revised = generate_summary(title, abstract, before.feedback)
    after = score_summary(abstract, revised)
    return {
        "first_summary": first,
        "first_score": asdict(before) | {"total": before.total},
        "revised_summary": revised,
        "revised_score": asdict(after) | {"total": after.total},
        "improvement": round(after.total - before.total, 2),
    }


def _score(data: dict[str, object], key: str) -> int:
    return max(1, min(10, int(data.get(key, 1))))
