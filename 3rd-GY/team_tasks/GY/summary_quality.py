"""요약 개선을 확인하는 스크립트.

prompt는 src/paperagent/agents.py에서 고치고, 여기서는 그 실제 agent를 그대로 불러
요약 → 리뷰 → 재작성이 점수를 올리는지만 본다. (prompt를 여기 또 복사하지 않는다.)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from paperagent.agents import PaperReaderAgent, ReviewerAgent, ReviewVerdict


@dataclass(frozen=True)
class _PaperShim:
    """search_arxiv 결과 대신 title/abstract만으로 실제 agent를 호출하기 위한 최소 객체."""

    title: str
    summary: str  # arXiv 결과의 abstract 필드 이름과 동일하게 맞춘다.

    def get_short_id(self) -> str:
        return "local-sample"


def run_reflection(
    title: str,
    abstract: str,
    topic: str = "paper agent for literature review",
    full_text: str | None = None,
) -> dict[str, object]:
    """첫 요약과 피드백 반영 후 요약의 Reviewer 점수를 비교한다.

    반환값의 ``best_*`` 는 두 요약 중 점수가 높은 쪽을 채택한 결과로,
    src pipeline의 best-of 재작성 로직과 동일한 기준을 사용한다.
    """
    paper = _PaperShim(title=title, summary=abstract)
    text = full_text or abstract

    reader = PaperReaderAgent(topic=topic)
    reviewer = ReviewerAgent()

    first = reader.summarize_paper(paper, text)
    before = reviewer.review_summary(first, text)

    revised = reader.summarize_paper(
        paper, text, revision_round=1, reviewer_feedback=before.feedback
    )
    after = reviewer.review_summary(revised, text)

    best_is_revised = after.score >= before.score
    best_summary = revised if best_is_revised else first
    best_score = after if best_is_revised else before

    return {
        "first_summary": first.summary,
        "first_score": _verdict_dict(before),
        "revised_summary": revised.summary,
        "revised_score": _verdict_dict(after),
        "improvement": after.score - before.score,
        "adopted": "revised" if best_is_revised else "first",
        "best_summary": best_summary.summary,
        "best_score": _verdict_dict(best_score),
    }


def _verdict_dict(verdict: ReviewVerdict) -> dict[str, object]:
    data = asdict(verdict)
    data["strengths"] = list(verdict.strengths)
    data["weaknesses"] = list(verdict.weaknesses)
    return data
