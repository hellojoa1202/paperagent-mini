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
CJK_PATTERN = re.compile(r"[぀-ヿ㐀-䶿一-鿿豈-﫿]")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]*)\)")
ARXIV_ID_PATTERN = re.compile(r"\d{4}\.\d{4,5}(?:v\d+)?")
COMMON_PROMPT_RULES = """
- 한국어와 필요한 영문 기술 용어만 사용
- 한자, 중국어, 일본어, 번역 지시문 금지
- 긴 줄글보다 짧은 불릿 사용
- 동일한 문장과 내용을 반복하지 않기
- 제목만 남기고 항목을 비워두지 않기
- 입력에 없는 수치, 성과, 구현 내용을 만들지 않기
""".strip()


@dataclass(frozen=True)
class ReportCheck:
    missing_sections: tuple[str, ...]
    cjk_count: int
    duplicate_lines: tuple[str, ...]
    empty_sections: tuple[str, ...]
    broken_links: tuple[str, ...]
    too_long: bool

    @property
    def passed(self) -> bool:
        return (
            not self.missing_sections
            and not self.cjk_count
            and not self.duplicate_lines
            and not self.empty_sections
            and not self.broken_links
            and not self.too_long
        )


def build_postdoc_prompt(topic: str, paper_summaries: str) -> str:
    return f"""
Research topic: {topic}

검증된 논문 요약:
{paper_summaries}

여러 논문을 하나의 Literature Review로 종합하세요.
공통 흐름과 논문 사이의 차이점이 한눈에 보이도록 정리하는 것이 목표입니다.
주장을 적을 때는 근거가 되는 논문을 `(arXiv ID)`로 함께 표기하세요.
{COMMON_PROMPT_RULES}

포함할 항목:
## Research trend
## Paper comparison
## Common methods
## Open problems
""".strip()


def build_critic_prompt(topic: str, literature_review: str) -> str:
    return f"""
Research topic: {topic}

검토할 Literature Review:
{literature_review}

문헌 리뷰에서 근거가 약한 주장, 과장된 결론, 빠진 관점과 숨은 가정을 찾으세요.
막연하게 비판하지 말고 `문제 위치 / 이유 / 수정 제안`을 짧은 불릿으로 작성하세요.
지적할 문제가 없는 항목은 왜 타당한지 한 줄 근거를 남기세요.
{COMMON_PROMPT_RULES}
""".strip()


def build_professor_prompt(topic: str, source_sections: str) -> str:
    return f"""
Research topic: {topic}

Agent 결과:
{source_sections}

위 결과를 바탕으로 최종 보고서의 `Final Synthesis`만 작성하세요.
읽는 사람이 빠르게 파악하도록 짧은 불릿 중심으로 쓰세요.
{COMMON_PROMPT_RULES}

포함할 항목:
## 핵심 결론
## 현재 구현
## 남은 한계
## 다음 단계
""".strip()


def build_report_prompt(topic: str, source_sections: str) -> str:
    """Backward-compatible alias for the Professor prompt."""
    return build_professor_prompt(topic, source_sections)


def generate_stage(stage: str, topic: str, source_text: str) -> str:
    builders = {
        "postdoc": build_postdoc_prompt,
        "critic": build_critic_prompt,
        "professor": build_professor_prompt,
    }
    if stage not in builders:
        raise ValueError("stage must be one of: postdoc, critic, professor")
    return ask_llm(
        f"You are the PaperAgent {stage} prompt under evaluation. Preserve supplied facts.",
        builders[stage](topic, source_text),
    )


def rewrite_final_synthesis(topic: str, source_sections: str) -> str:
    return generate_stage("professor", topic, source_sections)


def _find_duplicate_lines(text: str) -> tuple[str, ...]:
    normalized_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    content_lines = [line for line in normalized_lines if len(line) >= 20 and not line.startswith("#")]
    seen: set[str] = set()
    duplicates: list[str] = []
    for line in content_lines:
        if line in seen and line not in duplicates:
            duplicates.append(line)
        seen.add(line)
    return tuple(duplicates)


def _find_empty_sections(text: str) -> tuple[str, ...]:
    """A heading is empty when nothing but blanks separate it from the next
    same-level heading (or the end of the file). A deeper sub-heading counts as
    content, so container headings are not flagged."""
    lines = text.splitlines()
    headings = [
        (index, len(match.group(1)), match.group(2).strip())
        for index, line in enumerate(lines)
        if (match := HEADING_PATTERN.match(line))
    ]
    empty: list[str] = []
    for order, (line_no, level, title) in enumerate(headings):
        next_line_no = headings[order + 1][0] if order + 1 < len(headings) else len(lines)
        has_body = any(line.strip() for line in lines[line_no + 1 : next_line_no])
        if has_body:
            continue
        next_level = headings[order + 1][1] if order + 1 < len(headings) else None
        # Same-level sibling or end-of-file means the heading is truly empty;
        # a deeper (or shallower wrapper) next heading is treated as content.
        if next_level is None or next_level == level:
            empty.append(title)
    return tuple(empty)


def _find_broken_links(text: str) -> tuple[str, ...]:
    """Flag empty links and arXiv links whose visible id and URL disagree."""
    broken: list[str] = []
    for display, url in MARKDOWN_LINK_PATTERN.findall(text):
        display, url = display.strip(), url.strip()
        display_id = ARXIV_ID_PATTERN.search(display)
        if not url:
            broken.append(f"[{display}]() — 링크 주소가 비어 있음")
        elif "arxiv.org/abs/" in url:
            url_id = ARXIV_ID_PATTERN.search(url)
            if not url_id:
                broken.append(f"[{display}]({url}) — arXiv id가 없는 링크")
            elif display_id and display_id.group() != url_id.group():
                broken.append(f"[{display}]({url}) — 표시 id와 링크 id 불일치")
        elif display_id:
            broken.append(f"[{display}]({url}) — arXiv 링크가 아님")
    return tuple(broken)


def check_report(text: str, max_chars: int = 24000) -> ReportCheck:
    missing = tuple(section for section in REQUIRED_SECTIONS if section not in text)
    return ReportCheck(
        missing_sections=missing,
        cjk_count=len(CJK_PATTERN.findall(text)),
        duplicate_lines=_find_duplicate_lines(text),
        empty_sections=_find_empty_sections(text),
        broken_links=_find_broken_links(text),
        too_long=len(text) > max_chars,
    )
