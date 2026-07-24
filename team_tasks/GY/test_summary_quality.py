"""Offline tests for GY's summary/review improvements. No network/LLM needed."""

from __future__ import annotations

import json

import paperagent.agents as agents
from paperagent.agents import PaperReaderAgent, ReviewerAgent
from team_tasks.GY import summary_quality


class _PaperShim:
    title = "Attention Is All You Need"
    summary = "We propose the Transformer based solely on attention."

    def get_short_id(self) -> str:
        return "sample"


def test_summary_prompt_enforces_grounding(monkeypatch) -> None:
    captured: dict[str, str] = {}
    monkeypatch.setattr(agents, "ask_llm", lambda system, user: captured.setdefault("p", user) or "- ok")

    PaperReaderAgent("topic").summarize_paper(_PaperShim(), "full text")
    prompt = captured["p"]

    assert "원문에 명시되지 않음" in prompt          # 원문에 없으면 지어내지 말 것
    assert "## Experiments or evidence" in prompt     # 6개 제목 유지
    assert "## Limitations" in prompt


def test_summary_prompt_applies_feedback(monkeypatch) -> None:
    captured: dict[str, str] = {}
    monkeypatch.setattr(agents, "ask_llm", lambda system, user: captured.setdefault("p", user) or "- ok")

    PaperReaderAgent("topic").summarize_paper(
        _PaperShim(), "full text", revision_round=1, reviewer_feedback="Method 섹션 보강"
    )
    prompt = captured["p"]
    assert "Method 섹션 보강" in prompt
    assert "하나씩 반드시 반영" in prompt


def test_review_prompt_has_rubric_and_specificity(monkeypatch) -> None:
    captured: dict[str, str] = {}
    monkeypatch.setattr(
        agents,
        "ask_llm",
        lambda system, user: captured.setdefault("p", user) or '{"score": 6, "feedback": "x"}',
    )
    summary = agents.PaperSummary(
        paper_id="s", title="t", abstract="a", summary="- s"
    )
    ReviewerAgent().review_summary(summary, "full text")
    prompt = captured["p"]
    assert "채점 루브릭" in prompt
    assert "hallucination" in prompt
    assert "weaknesses" in prompt


def _scripted_llm(reviewer_scores):
    """Return an ask_llm stub: reader calls echo a summary, reviewer calls return scripted scores."""
    scores = iter(reviewer_scores)

    def _stub(system: str, user: str) -> str:
        if "ReviewerAgent" in system:
            return json.dumps({"score": next(scores), "feedback": "보강", "strengths": [], "weaknesses": []})
        return "- 요약 불릿"

    return _stub


def test_reflection_adopts_revision_when_it_improves(monkeypatch) -> None:
    monkeypatch.setattr(agents, "ask_llm", _scripted_llm([5, 9]))  # first=5, revised=9
    result = summary_quality.run_reflection("t", "abstract")
    assert result["adopted"] == "revised"
    assert result["best_score"]["score"] == 9
    assert result["improvement"] == 4


def test_reflection_keeps_first_when_revision_regresses(monkeypatch) -> None:
    monkeypatch.setattr(agents, "ask_llm", _scripted_llm([8, 4]))  # revision made it worse
    result = summary_quality.run_reflection("t", "abstract")
    assert result["adopted"] == "first"
    assert result["best_score"]["score"] == 8
