"""Small multi-agent roles inspired by Agent Laboratory."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from paperagent.llm import ask_llm
from paperagent.report_formatting import normalize_technical_terms


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
    return normalize_technical_terms("\n".join(cleaned_lines).strip())


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
    """Structured result from summary quality review."""

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
            "Keep established technical terms in their original English spelling instead of "
            "transliterating them into Korean. Examples include anomaly, Transformer, attention, "
            "token merging, embedding, latency, framework, dataset, baseline, ablation, gauge "
            "fixing, Faddeev-Popov ghost, and Noether current. "
            "English is allowed only for those technical nouns, model names, method names, "
            "datasets, and metrics. All explanations must be written in Korean; never write a "
            "complete explanatory sentence in English. "
            "Do not use emojis, decorative symbols, greetings, chatty preambles, "
            "offers to do more work, or follow-up questions."
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
- 구체적 수치, 데이터셋 이름, 지표 값, 모델 이름이 원문에 있으면 그대로 인용하세요.
- 제공된 자료에 명시적인 한계 문장이 없더라도 평가 환경, 비교 범위, 데이터 범위,
  방법의 가정에서 직접 확인할 수 있는 구체적인 제한점을 작성하세요.
- "원문에 명시되지 않음", "정보 없음" 같은 자리 채우기 문장은 쓰지 마세요.

[형식 규칙]
- 아래 6개 제목(## ...)을 순서와 철자 그대로 사용하세요.
- 각 항목은 줄글이 아니라 2~4개의 짧은 불릿으로 작성하고, 불릿 하나에는 한 가지 핵심만 담으세요.
- 완성형 문장 대신 짧은 명사형 구절을 사용하세요. `~합니다`, `~했다`, `~이다`, `~있다` 같은 문장형 종결은 금지합니다.
- 모델명·방법명·분야 용어는 번역하거나 한글로 음역하지 말고 원문의 영문 표기를 유지하세요.
- 예: `learnable token merging 기반 FLOPs 감소`, `anomaly consistency 검증`, `attention 연산량 감소`
- 영문은 기술 용어에만 사용하세요. 각 불릿에는 반드시 한국어 설명이 포함되어야 하며 영문 문장 전체를 쓰면 안 됩니다.
- 한글과 필요한 영문 기술 용어만 사용하세요. 한자, 중국어, 일본어 문자는 절대 쓰지 마세요.

## Problem
- 논문이 해결하려는 문제와 기존 방식의 구체적 한계
## Key idea
- 이 논문만의 핵심 아이디어와 기존 방식과의 차이
## Method
- 방법론, 모델 구조, 알고리즘의 핵심 구성요소
## Experiments or evidence
- 데이터셋, 비교 대상, 주요 결과 수치와 근거. 수치가 없으면 검증한 환경과 정성적 결과
## Limitations
- 저자가 밝힌 한계 또는 제공된 자료의 평가 범위·방법 가정에서 직접 확인되는 제한점
## Why this matters for our project
- 우리 paper agent 프로젝트에 적용할 점
"""
        summary_text = _remove_unwanted_cjk(self.ask(user_prompt))
        if len(re.findall(r"[가-힣]", summary_text)) < 20:
            summary_text = _remove_unwanted_cjk(
                self.ask(
                    f"""
{user_prompt}

이전 응답이 한국어 요약 형식을 지키지 않았습니다.
아래 이전 응답의 영어 문장을 그대로 반복하지 마세요.
모델명·방법명·dataset·metric 같은 핵심 기술 용어만 영어로 유지하고,
나머지 설명은 모두 한국어 명사형 불릿으로 다시 작성하세요.
각 불릿에는 반드시 한국어가 포함되어야 합니다.

이전 응답:
{summary_text}
"""
                )
            )
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

당신은 위 요약을 원문과 대조해 평가하는 엄격한 Reviewer입니다.
오직 제공된 원문만을 근거로 삼고, 원문에 없는 지식으로 판단하지 마세요.

[평가 기준]
- 정확성: 요약의 각 주장이 원문과 일치하는가. 원문에 없는 내용을 지어냈는가
- 구체성: 수치, 데이터셋, 지표, 모델 이름 등 구체적 근거를 담았는가
- 완결성: Problem, Key idea, Method, Experiments, Limitations 핵심이 구체적으로 채워졌는가
- 명료성: 불릿이 간결하고 한 불릿에 한 가지 내용만 담겼는가
- 언어·형식: 핵심 기술 용어는 영문 원형을 유지하고, 설명은 한국어 명사형 불릿이며 지정된 6개 제목을 지켰는가

[채점 루브릭] (1~10 정수)
- 9~10: 사실 오류가 없고 핵심 근거와 수치가 충실하며 누락이 없음
- 7~8: 큰 오류는 없으나 근거가 얕거나 사소한 누락이 있음
- 4~6: 일부 부정확하거나 핵심 항목이 비어 있음
- 1~3: 명백한 사실 오류 또는 원문과 무관한 내용이 다수 있음
초안은 보통 5~7점이며 8점 이상은 엄격하게 부여하세요.

[weaknesses / feedback 작성 규칙]
- weaknesses에는 "요약의 어느 부분이", "무엇이 틀렸거나 빠졌는지"를 원문 근거와 함께 구체적으로 적으세요.
- feedback은 재작성할 때 그대로 실행할 수 있는 지시 목록으로 작성하세요.
- "더 구체적으로 작성" 같은 모호한 총평은 쓰지 마세요.
- "원문에 명시되지 않음", "정보 없음" 같은 문구로 항목을 채웠다면 통과시키지 말고,
  제공된 자료의 평가 범위나 방법 가정에서 확인되는 구체적인 내용을 쓰도록 지시하세요.
- 영어 문장 위주로 작성됐다면 점수를 6점 이하로 주고 자연스러운 한국어로 다시 쓰도록 지시하세요.
- 영문 기술 용어를 어색하게 한글 음역했거나 불릿을 완성형 문장으로 썼다면
  점수를 6점 이하로 주고 짧은 명사형 불릿으로 재작성하도록 지시하세요.

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
    """Critically review blind spots and weak claims."""

    name = "CriticAgent"
    role = "skeptical senior researcher finding blind spots and weak claims"

    def critique(self, topic: str, literature_review: str) -> str:
        return _remove_unwanted_cjk(
            self.ask(
                f"""
Research topic: {topic}
Literature review:
{literature_review}

위 literature review에서 근거가 약하거나 빠진 내용을 구체적으로 지적하세요.
막연한 비판은 금지하고 각 문제를 아래 세 줄 형식의 짧은 불릿으로 작성하세요.

- 문제 위치: 리뷰의 어떤 주장이나 문장인지
- 이유: 왜 근거가 약하거나 빠졌는지. 숨은 가정, 과장, 반대 사례 포함
- 수정 제안: 무엇을 보완하거나 확인하면 되는지

작성 규칙:
- 한글과 필요한 영문 기술 용어만 사용하고 한자·중국어·일본어 문자와 번역 지시문은 쓰지 마세요.
- 같은 지적을 반복하거나 입력에 없는 내용을 만들지 마세요.
- 지적할 문제가 없는 항목은 왜 타당한지 한 줄로 근거를 남기고 비워두지 마세요.
"""
            )
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

위 논문 요약들을 하나의 한국어 literature review로 종합하세요.
여러 논문의 공통 흐름과 차이점이 한눈에 보이도록 정리하세요.

작성 규칙:
- 긴 줄글 대신 짧은 명사형 불릿을 사용하고, 불릿 하나에는 한 가지 내용만 담으세요.
- `~합니다`, `~했다`, `~이다`, `~있다` 같은 문장형 종결은 사용하지 마세요.
- 주장의 근거가 되는 논문을 `(arXiv ID)`로 함께 표기하세요.
- 논문들의 공통점과 차이점을 반드시 대비하세요.
- 모델명·방법명·분야 용어는 원문의 영문 표기를 유지하세요.
- 영어는 핵심 기술 용어에만 사용하고 나머지 설명은 반드시 한국어로 작성하세요.
- 한글과 필요한 영문 기술 용어만 사용하고 한자·중국어·일본어 문자와 번역 지시문은 쓰지 마세요.
- 같은 내용을 반복하거나 입력에 없는 수치와 성과를 만들지 마세요.
- 제목만 남은 빈 항목을 만들지 마세요.

반드시 포함할 항목:
## Overall research trend
- 전체 연구 흐름을 2~4개 불릿으로 정리
## Paper comparison
| # | Paper (arXiv ID) | 접근 방식 | 차별점 / 한계 |
|---|---|---|---|
## Common methods
- 여러 논문이 공유하는 방법이나 가정
## Open problems
- 아직 해결되지 않은 공통 문제
## Implementation hints for our mini paper agent
- 우리 mini paper agent 프로젝트에 적용할 점
"""
        return _remove_unwanted_cjk(self.ask(user_prompt))


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

발표나 과제 제출에 쓸 수 있는 최종 보고서를 한국어로 작성하세요.
읽는 사람이 빠르게 파악할 수 있도록 긴 줄글 대신 짧은 불릿 중심으로 작성하세요.

작성 규칙:
- 각 항목은 2~4개의 짧은 명사형 불릿으로 작성하고, 불릿 하나에는 한 가지 내용만 담으세요.
- `~합니다`, `~했다`, `~이다`, `~있다` 같은 문장형 종결은 사용하지 마세요.
- 모델명·방법명·분야 용어는 번역하거나 한글로 음역하지 말고 원문의 영문 표기를 유지하세요.
- 영어는 핵심 기술 용어에만 사용하고 나머지 설명은 반드시 한국어로 작성하세요.
- 한글과 필요한 영문 기술 용어만 사용하고 한자·중국어·일본어 문자와 번역 지시문은 쓰지 마세요.
- 같은 문장을 반복하거나 입력에 없는 수치와 성과를 만들지 마세요.
- 제목만 남은 빈 항목을 만들지 마세요.

포함할 항목:
## Abstract
## Background
## Agent architecture
## What we implemented
## What remains
## Next milestones
"""
        return _remove_unwanted_cjk(self.ask(user_prompt))


class MethodExtractionAgent(BaseAgent):
    """Extract implementable methods, formulas, and algorithms."""

    name = "MethodExtractionAgent"
    role = "ML/SW engineer extracting implementable methods"

    def extract_implementable_method(self, topic: str, summaries: list[PaperSummary]) -> str:
        user_prompt = f"""

Research topic: {topic}
Paper summaries: {_join_summaries(summaries)}

실제 코드로 구현 가능한 알고리즘, 수식, 데이터 흐름, agent 설계를 추출하세요.
가장 관련성 높은 방법 하나를 우선 선택하고 선택 이유를 한 문단으로 적으세요.
핵심 계산, 입력·출력, 검증 항목을 짧은 불릿으로 정리하세요.
전체 코드, 설치 안내, 장식용 이모지, 인사말, 후속 질문은 쓰지 마세요.
800단어 이내로 작성하세요.
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
계획 전체에서 Python 표준 라이브러리와 NumPy만 사용하세요.
PyTorch, TensorFlow, torchvision, scikit-learn, matplotlib 등 다른 패키지를 요구하지 마세요.
입력 method가 다른 라이브러리를 전제로 해도 핵심 계산을 NumPy 기반의 작은 toy implementation으로 바꾸세요.
포함할 항목:
1. Requirements & dependencies
2. Mock data specification
3. Baseline method
4. Proposed method
5. Comparison metrics
6. Core modules
7. Input/Output specifications
8. Step-by-step execution steps
9. Validation scenario

각 항목은 짧은 불릿으로 작성하고 전체 Python 코드는 포함하지 마세요.
Extracted method를 그대로 반복하지 말고 구현 결정만 정리하세요.
baseline과 제안 방법을 같은 mock data로 실행하고 최소 2개의 계산된 지표로 비교하도록 설계하세요.
이모지, 장식용 기호, 인사말, 예상 성능 과장, 후속 질문은 쓰지 마세요.
900단어 이내로 작성하세요.
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

위 계획을 구현한 바로 실행 가능한 Python 코드를 작성하세요.
작성 조건:
1. 외부 API 호출이나 로컬 파일 로드 없이 스크립트 내부의 mock data만 사용하세요.
2. 표준 라이브러리와 NumPy만 사용해 가볍게 작성하세요.
   torch, torchvision, TensorFlow, sklearn, matplotlib, tqdm은 import하지 마세요.
3. 함수와 클래스는 `pass` 없이 최소한으로 동작하게 구현하세요.
4. 주석이나 반복문으로 분량을 채우지 말고 90~180줄 정도의 실제 실행 코드로 작성하세요.
5. 설명 없이 markdown의 Python 코드 블록 하나에 전체 코드만 담으세요.
6. `if __name__ == "__main__":` 실행 블록에서 전체 흐름을 시험하고 결과를 출력하세요.
7. 입력·중간 결과·최종 출력 shape를 assert로 검사하고 실제 shape를 출력하세요.
8. 정확도, 속도, 감소율 등의 수치는 코드에서 실제로 계산한 값만 출력하세요.
   "가상 정확도 85%" 같은 고정 성능 수치를 만들지 마세요.
9. 계획에 오류가 있거나 현재 의존성 규칙과 충돌하면 이 작성 조건을 우선하세요.
10. 핵심 계산을 최소 4개의 함수로 나누고 전체 흐름은 반드시
    `run_prototype()` 함수에서 실행하세요.
11. 주제와 계획의 핵심 용어가 함수명·변수명·계산 과정에 드러나야 합니다.
    오류 수정 과정에서도 덧셈, 정렬 같은 무관한 예제로 대체하지 마세요.
12. `make_mock_data()`, baseline 계산, 논문의 제안 방법 계산, 평가 함수에 해당하는
    단계를 분리하고 같은 입력에서 baseline과 제안 방법을 비교하세요.
13. 지표를 최소 2개 직접 계산하고, 입력 shape·중간 shape·baseline 결과·제안 방법
    결과·비교 지표를 JSON 형태로 출력하세요.
"""
        return strip_code_fence(self.ask(user_prompt))

    def write_prototype_readme(self, topic: str, implementation_plan: str) -> str:
        user_prompt = f"""

Research topic: {topic}
Implementation Plan: {implementation_plan}

생성된 `prototype.py` 실행 안내 README를 한국어로 작성하세요.
필요 의존성, 실행 명령, 실제 출력에서 확인할 항목, 다음 개선점을 포함하세요.
전체 코드를 다시 싣거나 Implementation Plan을 반복하지 마세요.
이모지, 장식용 기호, 인사말, 작성자·작성일, 후속 질문은 쓰지 마세요.
400단어 이내의 짧은 불릿으로 작성하세요.
"""
        return self.ask(user_prompt)


class PrototypeReviewerAgent(BaseAgent):
    """Review a generated prototype failure and return repaired code."""

    name = "PrototypeReviewerAgent"
    role = "senior Python engineer repairing a small generated prototype"

    def repair(
        self,
        code: str,
        error: Any,
        *,
        topic: str = "",
        implementation_plan: str = "",
    ) -> str:
        error_message = getattr(error, "error", str(error))
        prompt = f"""
다음 Python 코드는 검증 과정에서 오류가 발생했습니다.

원래 연구 주제:
{topic}

반드시 유지해야 할 구현 계획:
{implementation_plan}

오류 내용:
{error_message}

기존 코드:
```python
{code}
```

오류를 해결하는 데 필요한 최소한의 수정만 하세요.
원래 연구 주제와 구현 계획의 핵심 계산을 보존하고, 덧셈·정렬 등 무관한
예제 코드로 전체를 교체하지 마세요.
기존 코드의 mock data, baseline, 제안 방법, 평가 구조를 삭제하거나 축약하지 마세요.
표준 라이브러리와 NumPy만 사용하고 torch, torchvision, TensorFlow,
sklearn, matplotlib, tqdm은 제거하세요.
외부 데이터와 API 없이 즉시 실행 가능해야 합니다.
실행 코드 기준 90~180줄, 핵심 함수 최소 4개를 유지하고 `run_prototype()`에서
전체 흐름을 실행하세요.
`if __name__ == "__main__":` 블록과 실행 결과 출력, 핵심 shape assert를 포함하세요.
가상·고정 성능 수치를 제거하고 실행 결과에서 직접 계산하세요.
설명 없이 Python 코드 블록 하나에 수정된 전체 코드만 담으세요.
"""
        return strip_code_fence(self.ask(prompt))


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
    lines = []
    for index, summary in enumerate(summaries, start=1):
        lines.append(f"### {index}. {summary.title}")
        lines.append(f"- **arXiv ID**: [{summary.paper_id}](https://arxiv.org/abs/{summary.paper_id})")
        if summary.published:
            lines.append(f"- **Published**: {summary.published[:10]}")
        lines.append(f"\n#### Abstract\n{summary.abstract}\n")
        lines.append(f"#### 요약 내용\n{summary.summary}\n")
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
    lines = []
    for index, (summary, verdict) in enumerate(feedbacks, start=1):
        lines.append(f"### {index}. {summary.title}")
        lines.append(f"- **arXiv ID**: [{summary.paper_id}](https://arxiv.org/abs/{summary.paper_id})")
        lines.append(f"- **Score**: {verdict.score}/10")
        lines.append(f"- **Revision rounds**: {summary.revision_round}")
        lines.append(f"- **Strengths**: {', '.join(verdict.strengths) or 'N/A'}")
        lines.append(f"- **Weaknesses**: {', '.join(verdict.weaknesses) or 'N/A'}")
        lines.append(f"\n#### Feedback\n{verdict.feedback}\n")
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
