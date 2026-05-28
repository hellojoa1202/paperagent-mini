"""Assignment-based agents merged from GY/SH 1st and 2nd folders."""

from __future__ import annotations

from dataclasses import dataclass

import arxiv

from paperagent.llm import ask_llm


@dataclass
class PaperSummary:
    paper_id: str
    title: str
    abstract: str
    summary: str


class PaperReaderAgent:
    """논문 요약과 literature review 작성을 담당하는 현재 구현 agent."""

    def __init__(self, topic: str):
        self.topic = topic

    def summarize_paper(self, paper: arxiv.Result, full_text: str) -> PaperSummary:
        system_prompt = (
            "You are a careful research assistant. "
            "Read papers for a beginner research group and explain them clearly in Korean."
        )
        user_prompt = f"""
Research topic:
{self.topic}

Paper title:
{paper.title}

Paper abstract:
{paper.summary}

Paper text:
{full_text}

아래 항목들을 포함하여 한국어로 명확하고 간결한 요약본을 작성해 주세요:
- Problem (논문이 해결하고자 하는 문제)
- Key idea (핵심 아이디어)
- Method (방법론 및 모델 구조)
- Experiments or evidence (실험 방식 및 결과 증거)
- Limitations (연구 한계점)
- Why this matters for our project (우리 프로젝트에 적용할 수 있는 의의)
"""
        summary = ask_llm(system_prompt, user_prompt)
        return PaperSummary(
            paper_id=paper.get_short_id(),
            title=paper.title,
            abstract=paper.summary,
            summary=summary,
        )

    def write_literature_review(self, summaries: list[PaperSummary]) -> str:
        joined = "\n\n".join(
            f"## {item.title}\nID: {item.paper_id}\n\n{item.summary}" for item in summaries
        )
        system_prompt = (
            "You are a research mentor. "
            "Synthesize papers into a literature review for a student team in Korean."
        )
        user_prompt = f"""
Research topic:
{self.topic}

Paper summaries:
{joined}

위 요약본들을 종합하여 한국어로 작성된 문헌 조사 서평(Literature Review)을 작성해 주세요.
반드시 아래 항목을 포함해야 합니다:
1. Overall research trend (전체적인 연구 동향)
2. Paper comparison table (논문 비교 표 - 마크다운 테이블 형식)
3. Common methods (공통적으로 많이 사용된 방법론)
4. Open problems (미해결 과제 및 한계점)
5. Project ideas our team could build next (우리 팀이 후속으로 개발/구현할 수 있는 프로젝트 아이디어)
"""
        return ask_llm(system_prompt, user_prompt)


class MethodExtractionAgent:
    """SH 1st folder의 구현 가능 방법 추출 흐름을 agent로 분리."""

    def extract_implementable_method(self, topic: str, summaries: list[PaperSummary]) -> str:
        joined = "\n\n".join(
            f"Title: {item.title}\nSummary: {item.summary}" for item in summaries
        )
        system_prompt = (
            "You are an expert ML/SW implementation engineer. "
            "Extract concrete mathematical formulations, pseudo-codes, and core algorithms in Korean."
        )
        user_prompt = f"""
Research topic:
{topic}

Paper summaries:
{joined}

위 논문 요약들 중에서 실제 코드로 구현할 수 있는 구체적인 알고리즘,
수학 공식, 또는 설계 구조를 추출해 주세요.
작성 언어는 한국어로 작성하고, 마크다운 코드 블록이나 수식을 활용하여
엔지니어가 보고 구현 계획을 세울 수 있도록 자세히 설명해 주세요.
"""
        return ask_llm(system_prompt, user_prompt)


class PrototypePlannerAgent:
    """추출된 방법론을 prototype 개발 계획으로 바꾸는 agent."""

    def write_implementation_plan(self, topic: str, method_text: str) -> str:
        system_prompt = (
            "You are a technical project manager. "
            "Create a detailed, step-by-step implementation plan for a software developer in Korean."
        )
        user_prompt = f"""
Research topic:
{topic}

Extracted method:
{method_text}

이 추출된 방법론을 바탕으로, 실제 작동하는 미니 프로토타입 Python 코드(prototype.py)를
구현하기 위한 단계별 개발 계획서를 작성해 주세요.
한국어로 작성해야 하며, 아래 항목들을 구체적으로 채워주세요:
1. Requirements & dependencies (필요 환경 및 패키지)
2. Core modules (구현해야 할 핵심 함수/클래스 정의 및 설계)
3. Input/Output specifications (입출력 데이터 규격)
4. Step-by-step execution steps (구현할 기능 순서 및 검증 시나리오)
"""
        return ask_llm(system_prompt, user_prompt)


class PrototypeWriterAgent:
    """개발 계획을 mock data 기반 prototype.py와 README로 바꾸는 agent."""

    def generate_prototype_code(self, topic: str, implementation_plan: str) -> str:
        system_prompt = (
            "You are an elite Python developer. Write clean, self-contained, working python code "
            "with mock data. Provide ONLY valid executable Python code in code blocks."
        )
        user_prompt = f"""
Research topic:
{topic}

Implementation Plan:
{implementation_plan}

위 개발 계획서에 명시된 핵심 아이디어를 동작하는 Python 코드로 구현해 주세요.
조건:
1. 외부 데이터가 없어도 테스트해볼 수 있도록 소스코드 내부에서 가짜 데이터(Mock data)를 자동 생성해야 합니다.
2. 예외 처리와 직관적인 주석을 포함해 주세요.
3. markdown 코드 블록 형태로 Python 코드만 출력해 주세요.
4. transformers, torch, tensorflow 등 무거운 딥러닝 패키지는 사용하지 마세요.
5. 마지막에는 `if __name__ == '__main__':` 실행 블록을 포함하세요.
"""
        return strip_code_fence(ask_llm(system_prompt, user_prompt))

    def write_prototype_readme(self, topic: str, implementation_plan: str) -> str:
        system_prompt = "You are a developer relations advocate. Write a clean README.md guide in Korean."
        user_prompt = f"""
Research topic:
{topic}

Implementation Plan:
{implementation_plan}

위 계획에 따라 생성된 `prototype.py`를 어떻게 실행하고 검증해야 하는지 알려주는
실행 안내 가이드(README.md)를 한국어로 작성해 주세요.
포함할 항목:
1. 프로토타입 소개
2. 설치 패키지 및 실행 커맨드
3. 실행 시 예상되는 터미널 출력 결과물 설명
"""
        return ask_llm(system_prompt, user_prompt)


def write_paper_summaries(summaries: list[PaperSummary]) -> str:
    lines = ["# 논문 요약 모음집 (Paper Summaries)\n"]
    for index, summary in enumerate(summaries, start=1):
        lines.append(f"## {index}. {summary.title}")
        lines.append(f"- **arXiv ID**: [{summary.paper_id}](https://arxiv.org/abs/{summary.paper_id})")
        lines.append(f"\n### 요약 내용\n{summary.summary}\n")
        lines.append("---\n")
    return "\n".join(lines)


def strip_code_fence(raw_code: str) -> str:
    if "```python" in raw_code:
        return raw_code.split("```python", 1)[1].split("```", 1)[0].strip()
    if "```" in raw_code:
        return raw_code.split("```", 1)[1].split("```", 1)[0].strip()
    return raw_code.strip()
