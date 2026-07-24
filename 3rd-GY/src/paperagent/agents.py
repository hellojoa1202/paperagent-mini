"""Small multi-agent roles inspired by Agent Laboratory."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from paperagent.llm import ask_llm


_CJK_SCRIPT_RE = re.compile(
    r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+[：:]?"
)


def _remove_unwanted_cjk(text: str) -> str:
    """Remove accidental Chinese/Japanese fragments from Korean model output."""
    cleaned_lines = []
    for line in text.splitlines():
        cleaned = _CJK_SCRIPT_RE.sub("", line)
        cleaned = re.sub(r"[ \t]+", " ", cleaned).rstrip(" :：")
        cleaned_lines.append(cleaned)
    return "\n".join(cleaned_lines).strip()


@dataclass(frozen=True)
class PaperSummary:
    paper_id: str
    title: str
    abstract: str
    summary: str
    published: str = ""
    paper_url: str = ""
    venue: str = "Preprint"
    revision_round: int = 0


@dataclass(frozen=True)
class ReviewVerdict:
    """GY 과제의 정량 평가 결과."""

    score: int
    feedback: str
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()


class BaseAgent:
    """Common parent for prompt-only agents."""

    name = "BaseAgent"
    role = "general research assistant"

    def ask(self, user_prompt: str) -> str:
        system_prompt = (
            f"You are {self.name}, a {self.role}. "
            "Work carefully, cite concrete evidence from the provided text, "
            "and write in clear Korean unless code is requested. "
            "Never output Chinese characters, Japanese characters, or translation instructions. "
            "English technical terms and Korean Hangul are allowed."
        )
        return ask_llm(system_prompt, user_prompt)


class PaperReaderAgent(BaseAgent):
    """PhDStudent-like agent for paper reading and per-paper summaries."""

    name = "PaperReaderAgent"
    role = "PhD student agent responsible for literature review"

    def __init__(self, topic: str):
        self.topic = topic

    def summarize_paper(
        self,
        paper: Any,
        full_text: str,
        revision_round: int = 0,
        reviewer_feedback: str = "",
    ) -> PaperSummary:
        if reviewer_feedback:
            feedback_block = (
                "이전 Reviewer가 아래 피드백을 남겼습니다. "
                "각 지적을 하나씩 반드시 반영해 요약을 다시 쓰세요.\n"
                f"{reviewer_feedback}"
            )
        else:
            feedback_block = "이전 피드백 없음. 첫 초안을 작성하세요."

        user_prompt = f"""
Research topic: {self.topic}
Paper title: {paper.title}
Paper abstract: {paper.summary}
Paper text: {full_text}

Reviewer feedback to apply:
{feedback_block}

당신은 위 논문을 읽고 한국어 요약을 작성합니다. 아래 규칙을 반드시 지키세요.

[근거 규칙]
- 제공된 abstract와 paper text에 실제로 적힌 내용만 사용하세요. 추측하거나 일반 상식으로 채우지 마세요.
- 구체적 수치, 데이터셋 이름, 지표(metric) 값, 모델 이름이 원문에 있으면 그대로 인용하세요.
- 원문에 근거가 없는 항목은 비워 두지 말고 "원문에 명시되지 않음"이라고 적으세요.

[형식 규칙]
- 아래 6개 제목(## ...)을 순서와 철자 그대로 사용하세요.
- 각 항목은 줄글이 아니라 2~4개의 짧은 불릿으로 작성하고, 불릿 하나에는 한 가지 핵심만 한 문장으로 담으세요.
- 한글과 필요한 영문 기술 용어만 사용하세요. 한자, 중국어, 일본어 문자는 절대 쓰지 마세요.

## Problem
- 논문이 해결하려는 문제와 기존 방식의 구체적 한계
## Key idea
- 이 논문만의 핵심 아이디어 (기존과 무엇이 다른지)
## Method
- 방법론, 모델 구조, 알고리즘 (핵심 구성요소를 구체적으로)
## Experiments or evidence
- 데이터셋, 비교 대상(baseline), 주요 결과 수치와 근거
## Limitations
- 저자가 밝힌 한계 또는 약한 가정 (없으면 "원문에 명시되지 않음")
## Why this matters for our project
- 우리 paper agent 프로젝트에 적용할 점
"""
        summary_text = _remove_unwanted_cjk(self.ask(user_prompt))
        return PaperSummary(
            paper_id=paper.get_short_id(),
            title=paper.title,
            abstract=paper.summary,
            summary=summary_text,
            published=getattr(paper, "published", ""),
            paper_url=getattr(
                paper,
                "abs_url",
                f"https://arxiv.org/abs/{paper.get_short_id()}",
            ),
            venue=_paper_venue(paper),
            revision_round=revision_round,
        )


def _paper_venue(paper: Any) -> str:
    """Best-effort conference/journal label from arXiv metadata."""
    metadata = " ".join(
        str(value or "")
        for value in (getattr(paper, "journal_ref", ""), getattr(paper, "comment", ""))
    )
    known = (
        "CoRL", "ICRA", "IROS", "RSS", "NeurIPS", "ICML", "ICLR", "CVPR",
        "ECCV", "ICCV", "AAAI", "IJCAI", "ACL", "EMNLP", "NAACL", "SIGGRAPH",
    )
    for venue in known:
        if re.search(rf"\b{re.escape(venue)}\b", metadata, flags=re.IGNORECASE):
            return venue
    if getattr(paper, "journal_ref", None):
        journal = re.sub(r"\s+", " ", str(paper.journal_ref)).strip()
        return journal[:36] + ("…" if len(journal) > 36 else "")
    return "Preprint"


class ReviewerAgent(BaseAgent):
    """Reviewer-like agent that checks whether a summary matches the paper."""

    name = "ReviewerAgent"
    role = "peer reviewer checking factual consistency and missing details"

    def review_summary(self, summary: PaperSummary, full_text: str) -> ReviewVerdict:
        user_prompt = f"""
Paper title: {summary.title}
Paper abstract: {summary.abstract}
Paper text excerpt: {full_text[:12000]}
Student summary: {summary.summary}

당신은 위 요약을 원문(abstract, paper text)과 대조해 평가하는 엄격한 Reviewer입니다.
오직 제공된 원문만을 근거로 삼고, 원문에 없는 지식으로 판단하지 마세요.

[평가 기준]
- 정확성: 요약의 각 주장이 원문과 일치하는가. 원문에 없는 내용을 지어냈는가(hallucination).
- 구체성: 수치, 데이터셋, 지표, 모델 이름 등 구체적 근거를 담았는가.
- 완결성: Problem/Key idea/Method/Experiments/Limitations 핵심이 빠지지 않았는가.
- 명료성: 불릿이 간결하고 한 불릿에 한 가지 내용만 담겼는가.

[채점 루브릭] (1~10 정수)
- 9~10: 사실 오류 없음 + 핵심 수치·근거 충실 + 누락 없음
- 7~8: 큰 오류 없으나 근거가 얕거나 사소한 누락 있음
- 4~6: 일부 부정확하거나 핵심 항목이 비어 있음
- 1~3: 명백한 사실 오류 또는 원문과 무관한 내용 다수
초안은 보통 5~7점이며 8점 이상은 엄격하게 부여하세요.

[weaknesses / feedback 작성 규칙]
- weaknesses의 각 항목은 "요약의 어느 부분이" "무엇이 틀렸거나 빠졌는지"를 원문 근거와 함께 구체적으로 지목하세요.
  (예: "Method 섹션이 attention 메커니즘만 언급하고 원문의 multi-head 구조를 누락함")
- feedback은 재작성 시 그대로 실행할 수 있는 지시 목록으로 쓰세요. 모호한 총평("더 구체적으로")은 금지합니다.

아래 JSON 하나만 반환하세요.
{{
  "score": 1부터 10 사이의 정수,
  "strengths": ["구체적인 강점"],
  "weaknesses": ["요약의 특정 부분 + 무엇이 틀렸거나 빠졌는지 + 원문 근거"],
  "feedback": "재작성 시 실행할 구체적 지시를 항목별로"
}}
"""
        return parse_review_verdict(self.ask(user_prompt))


class CriticAgent(BaseAgent):
    """GY 과제의 비판적 최종 검토 agent."""

    name = "CriticAgent"
    role = "skeptical senior researcher finding blind spots and weak claims"

    def critique(self, topic: str, literature_review: str) -> str:
        return self.ask(
            f"""
Research topic: {topic}
Literature review: {literature_review}

리뷰를 비판적으로 검토하고 누락된 관점, 숨은 가정, 근거가 약한 주장,
반대 시각과 구체적인 개선안을 한국어 markdown으로 작성하세요.
"""
        )


class PostdocAgent(BaseAgent):
    """Postdoc-like agent that synthesizes multiple summaries."""

    name = "PostdocAgent"
    role = "postdoc mentor synthesizing papers into a research direction"

    def write_literature_review(
        self,
        topic: str,
        summaries: list[PaperSummary],
        reviewer_feedback: str = "",
    ) -> str:
        user_prompt = f"""
Research topic: {topic}

Paper summaries:
{_join_summaries(summaries)}

Reviewer feedback:
{reviewer_feedback or "No reviewer feedback was generated."}

위 자료를 바탕으로 한국어 literature review를 작성하세요.
반드시 포함할 항목:
1. Overall research trend
2. Paper comparison table
3. Common methods
4. Open problems
5. Implementation hints for our mini paper agent
6. Project ideas our team could build next
"""
        return self.ask(user_prompt)


class ProfessorAgent(BaseAgent):
    """Professor-like agent that turns agent outputs into a report."""

    name = "ProfessorAgent"
    role = "professor agent responsible for final report organization"

    def write_project_report(
        self,
        topic: str,
        literature_review: str,
        method_text: str = "",
        implementation_plan: str = "",
        extra_reviews: str = "",
    ) -> str:
        user_prompt = f"""
Research topic: {topic}
Literature review: {literature_review}
Implementable methods: {method_text or "Not generated."}
Implementation plan: {implementation_plan or "Not generated."}
Extra reviewer reports: {extra_reviews or "Not generated."}

발표나 과제 제출에 쓸 수 있는 최종 보고서 초안을 한국어로 작성하세요.
포함할 항목:
- Abstract
- Background
- Agent architecture
- What we implemented
- What remains
- Next milestones
"""
        return self.ask(user_prompt)


class MethodExtractionAgent(BaseAgent):
    """Extract implementable methods, formulas, and algorithms."""

    name = "MethodExtractionAgent"
    role = "ML/SW engineer extracting implementable methods"

    def extract_implementable_method(self, topic: str, summaries: list[PaperSummary]) -> str:
        user_prompt = f"""

Research topic: {topic}
Paper summaries: {_join_summaries(summaries)}

실제 코드로 구현 가능한 알고리즘, 수식, 데이터 흐름, agent 설계를 추출하세요.
가능하면 pseudo-code와 구현 난이도도 함께 정리하세요.
"""
        return self.ask(user_prompt)


class PrototypePlannerAgent(BaseAgent):
    """Convert extracted methods into a concrete prototype plan."""

    name = "PrototypePlannerAgent"
    role = "technical project manager planning a prototype"

    def write_implementation_plan(self, topic: str, method_text: str) -> str:
        user_prompt = f"""

Research topic: {topic}
Extracted method: {method_text}

mock data만으로 실행 가능한 `prototype.py`를 만들기 위한 개발 계획을 작성하세요.
포함할 항목:
1. Requirements & dependencies
2. Core modules
3. Input/Output specifications
4. Step-by-step execution steps
5. Validation scenario
"""
        return self.ask(user_prompt)


class PrototypeWriterAgent(BaseAgent):
    """Write a mock-data prototype and a short execution guide."""

    name = "PrototypeWriterAgent"
    role = "Python developer writing a self-contained prototype"

    def generate_prototype_code(self, topic: str, implementation_plan: str) -> str:
        user_prompt = f"""
Research topic: {topic}
Implementation Plan: {implementation_plan}

위 계획을 바탕으로 동작하는 Python 코드를 작성하세요.
조건:
1. 외부 데이터 없이 mock data를 생성해야 합니다.
2. 표준 라이브러리 위주로 작성하세요.
3. markdown 코드 블록 하나에 Python 코드만 담으세요.
4. 마지막에는 `if __name__ == "__main__":` 실행 블록을 포함하세요.
"""
        return strip_code_fence(self.ask(user_prompt))

    def write_prototype_readme(self, topic: str, implementation_plan: str) -> str:
        user_prompt = f"""

Research topic: {topic}
Implementation Plan: {implementation_plan}

생성된 `prototype.py` 실행 안내 README를 한국어로 작성하세요.
설치, 실행 명령, 예상 출력, 다음 개선점을 포함하세요.
"""
        return self.ask(user_prompt)


class ExperimentReviewerAgent(BaseAgent):
    """Review whether the proposed experiments are convincing."""

    name = "ExperimentReviewerAgent"
    role = "reviewer evaluating experiment design"

    def review(self, topic: str, literature_review: str) -> str:
        return self.ask(_review_prompt(topic, literature_review, "실험 설계, metric, baseline, ablation"))


class NoveltyReviewerAgent(BaseAgent):
    """Review novelty and differentiation from prior work."""

    name = "NoveltyReviewerAgent"
    role = "reviewer evaluating novelty"

    def review(self, topic: str, literature_review: str) -> str:
        return self.ask(_review_prompt(topic, literature_review, "novelty, 차별점, incremental risk"))


class ImpactReviewerAgent(BaseAgent):
    """Review academic and practical impact."""

    name = "ImpactReviewerAgent"
    role = "reviewer evaluating research impact"

    def review(self, topic: str, literature_review: str) -> str:
        return self.ask(_review_prompt(topic, literature_review, "impact, 활용 가능성, 한계"))


def write_paper_summaries(summaries: list[PaperSummary]) -> str:
    lines = ["# 논문 요약 모음집 (Paper Summaries)\n"]
    for index, summary in enumerate(summaries, start=1):
        lines.append(f"## {index}. {summary.title}")
        lines.append(f"- **arXiv ID**: [{summary.paper_id}](https://arxiv.org/abs/{summary.paper_id})")
        if summary.published:
            lines.append(f"- **Published**: {summary.published[:10]}")
        lines.append(f"\n### Abstract\n{summary.abstract}\n")
        lines.append(f"### 요약 내용\n{summary.summary}\n")
        lines.append("---\n")
    return "\n".join(lines)


def write_quick_literature_review(topic: str, summaries: list[PaperSummary]) -> str:
    lines = [
        "# Quick Literature Review\n",
        f"- **Research topic**: {topic}",
        f"- **Paper count**: {len(summaries)}",
        "\n## Paper Comparison\n",
        "| # | Paper | arXiv ID | Key summary |",
        "|---|---|---|---|",
    ]
    for index, summary in enumerate(summaries, start=1):
        short_summary = _first_nonempty_line(summary.summary)
        lines.append(
            f"| {index} | {summary.title.replace('|', '/')} | "
            f"[{summary.paper_id}](https://arxiv.org/abs/{summary.paper_id}) | "
            f"{short_summary.replace('|', '/')} |"
        )
    lines.extend(
        [
            "\n## Note\n",
            "This quick review is generated without an additional synthesis LLM call. "
            "Enable the full literature review option when you want a richer PostdocAgent synthesis.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_single_paper_summary(
    summary: PaperSummary,
    reviewer_feedback: str | None = None,
) -> str:
    lines = [
        f"# {summary.title}\n",
        f"- **arXiv ID**: [{summary.paper_id}](https://arxiv.org/abs/{summary.paper_id})",
        "\n## Abstract",
        summary.abstract,
        "\n## Agent Summary",
        summary.summary,
    ]
    if reviewer_feedback:
        lines.extend(["\n## Reviewer Feedback", reviewer_feedback])
    return "\n".join(lines).strip() + "\n"


def write_reviewer_feedback(feedbacks: list[tuple[PaperSummary, ReviewVerdict]]) -> str:
    lines = ["# Reviewer Feedback\n"]
    for index, (summary, verdict) in enumerate(feedbacks, start=1):
        lines.append(f"## {index}. {summary.title}")
        lines.append(f"- **arXiv ID**: [{summary.paper_id}](https://arxiv.org/abs/{summary.paper_id})")
        lines.append(f"- **Score**: {verdict.score}/10")
        lines.append(f"- **Revision rounds**: {summary.revision_round}")
        lines.append(f"- **Strengths**: {', '.join(verdict.strengths) or 'N/A'}")
        lines.append(f"- **Weaknesses**: {', '.join(verdict.weaknesses) or 'N/A'}")
        lines.append(f"\n### Feedback\n{verdict.feedback}\n")
        lines.append("---\n")
    return "\n".join(lines)


def render_review_verdict(verdict: ReviewVerdict) -> str:
    return (
        f"Score: {verdict.score}/10\n\n"
        f"Strengths: {', '.join(verdict.strengths) or 'N/A'}\n\n"
        f"Weaknesses: {', '.join(verdict.weaknesses) or 'N/A'}\n\n"
        f"Feedback: {verdict.feedback}"
    )


def parse_review_verdict(raw: str) -> ReviewVerdict:
    """JSON fence가 섞인 LLM 응답도 안전하게 보존한다."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    json_text = match.group(1) if match else raw
    if not json_text.lstrip().startswith("{"):
        first, last = json_text.find("{"), json_text.rfind("}")
        if first >= 0 and last > first:
            json_text = json_text[first : last + 1]
    try:
        data = json.loads(json_text)
        score = max(1, min(10, int(data.get("score", 5))))
        return ReviewVerdict(
            score=score,
            feedback=str(data.get("feedback", "")),
            strengths=tuple(map(str, data.get("strengths", []))),
            weaknesses=tuple(map(str, data.get("weaknesses", []))),
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return ReviewVerdict(
            score=5,
            feedback=raw[:1000],
            weaknesses=("Reviewer JSON 파싱 실패: 원문 응답을 feedback에 보존함",),
        )


def strip_code_fence(raw_code: str) -> str:
    text = raw_code.strip()
    if "```python" in text:
        return text.split("```python", 1)[1].split("```", 1)[0].strip()
    if "```" in text:
        return text.split("```", 1)[1].split("```", 1)[0].strip()
    return text


def _join_summaries(summaries: list[PaperSummary]) -> str:
    return "\n\n".join(
        f"## {item.title}\nID: {item.paper_id}\nAbstract: {item.abstract}\n\n{item.summary}"
        for item in summaries
    )


def _first_nonempty_line(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("-*# ").strip()
        if line:
            return line[:180]
    return "Summary generated."


def _review_prompt(topic: str, literature_review: str, review_focus: str) -> str:
    return f"""
Research topic: {topic}
Literature review: {literature_review}

아래 관점으로 peer review를 작성하세요: {review_focus}
형식:
1. Score: 1-5
2. Strengths
3. Weaknesses
4. Concrete suggestions
"""
