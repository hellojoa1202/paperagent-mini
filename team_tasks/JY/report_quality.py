"""Final-report prompt and deterministic quality checks; no new Agent class."""

from __future__ import annotations

import re
from dataclasses import dataclass

from paperagent.llm import ask_llm


REQUIRED_SECTIONS = (
    "Paper Summaries",
    "Summary Quality Review",
    "Literature Review",
    "Critical Review",
    "Final Synthesis",
)
CJK_PATTERN = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


@dataclass(frozen=True)
class ReportCheck:
    missing_sections: tuple[str, ...]
    cjk_count: int
    duplicate_lines: tuple[str, ...]
    too_long: bool

    @property
    def passed(self) -> bool:
        return not self.missing_sections and not self.cjk_count and not self.duplicate_lines and not self.too_long


def build_report_prompt(topic: str, source_sections: str) -> str:
    """This is the main prompt JY should tune."""
    return f"""
Research topic: {topic}

Agent 결과:
{source_sections}

위 결과를 바탕으로 최종 보고서의 `Final Synthesis`만 작성하세요.
- 한국어와 필요한 영문 기술 용어만 사용
- 한자, 중국어, 일본어, 번역 지시문 금지
- 긴 줄글보다 짧은 불릿 사용
- 동일한 문장과 내용을 반복하지 않기
- 입력에 없는 수치나 성과를 만들지 않기
- 구현하지 않은 기능은 구현했다고 쓰지 않기

포함할 항목:
## 핵심 결론
## 현재 구현
## 남은 한계
## 다음 단계
""".strip()


def rewrite_final_synthesis(topic: str, source_sections: str) -> str:
    return ask_llm(
        "You are a Korean technical editor. Preserve facts and improve structure only.",
        build_report_prompt(topic, source_sections),
    )


def check_report(text: str, max_chars: int = 24000) -> ReportCheck:
    normalized_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    content_lines = [line for line in normalized_lines if len(line) >= 20 and not line.startswith("#")]
    seen: set[str] = set()
    duplicates: list[str] = []
    for line in content_lines:
        if line in seen and line not in duplicates:
            duplicates.append(line)
        seen.add(line)
    missing = tuple(section for section in REQUIRED_SECTIONS if section not in text)
    return ReportCheck(
        missing_sections=missing,
        cjk_count=len(CJK_PATTERN.findall(text)),
        duplicate_lines=tuple(duplicates),
        too_long=len(text) > max_chars,
    )
