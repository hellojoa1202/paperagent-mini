"""Deterministic checks for the consolidated research report."""

from __future__ import annotations

import re
from dataclasses import dataclass

from paperagent.report_formatting import find_visual_noise


REQUIRED_SECTIONS = (
    "Paper Summaries",
    "Summary Quality Review",
    "Literature Review",
    "Critical Review",
    "Final Synthesis",
)
CJK_PATTERN = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]*)\)")
ARXIV_ID_PATTERN = re.compile(r"\d{4}\.\d{4,5}(?:v\d+)?")


@dataclass(frozen=True)
class ReportCheck:
    missing_sections: tuple[str, ...]
    cjk_count: int
    duplicate_lines: tuple[str, ...]
    empty_sections: tuple[str, ...]
    broken_links: tuple[str, ...]
    too_long: bool
    visual_noise: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return not any(
            (
                self.missing_sections,
                self.cjk_count,
                self.duplicate_lines,
                self.empty_sections,
                self.broken_links,
                self.too_long,
                self.visual_noise,
            )
        )


def _find_duplicate_lines(text: str) -> tuple[str, ...]:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    content = [line for line in lines if len(line) >= 20 and not line.startswith("#")]
    seen: set[str] = set()
    duplicates: list[str] = []
    for line in content:
        if line in seen and line not in duplicates:
            duplicates.append(line)
        seen.add(line)
    return tuple(duplicates)


def _find_empty_sections(text: str) -> tuple[str, ...]:
    lines = text.splitlines()
    headings = [
        (index, len(match.group(1)), match.group(2).strip())
        for index, line in enumerate(lines)
        if (match := HEADING_PATTERN.match(line))
    ]
    empty: list[str] = []
    for order, (line_number, level, title) in enumerate(headings):
        next_line = headings[order + 1][0] if order + 1 < len(headings) else len(lines)
        if any(line.strip() for line in lines[line_number + 1 : next_line]):
            continue
        next_level = headings[order + 1][1] if order + 1 < len(headings) else None
        if next_level is None or next_level == level:
            empty.append(title)
    return tuple(empty)


def _find_broken_links(text: str) -> tuple[str, ...]:
    broken: list[str] = []
    for display, url in MARKDOWN_LINK_PATTERN.findall(text):
        display, url = display.strip(), url.strip()
        display_id = ARXIV_ID_PATTERN.search(display)
        if not url:
            broken.append(f"[{display}]() — 링크 주소가 비어 있음")
        elif "arxiv.org/abs/" in url:
            url_id = ARXIV_ID_PATTERN.search(url)
            if not url_id:
                broken.append(f"[{display}]({url}) — arXiv ID가 없는 링크")
            elif display_id and display_id.group() != url_id.group():
                broken.append(f"[{display}]({url}) — 표시 ID와 링크 ID 불일치")
        elif display_id:
            broken.append(f"[{display}]({url}) — arXiv 링크가 아님")
    return tuple(broken)


def check_report(
    text: str,
    *,
    max_chars: int = 24000,
    required_sections: tuple[str, ...] = REQUIRED_SECTIONS,
) -> ReportCheck:
    return ReportCheck(
        missing_sections=tuple(section for section in required_sections if section not in text),
        cjk_count=len(CJK_PATTERN.findall(text)),
        duplicate_lines=_find_duplicate_lines(text),
        empty_sections=_find_empty_sections(text),
        broken_links=_find_broken_links(text),
        too_long=len(text) > max_chars,
        visual_noise=find_visual_noise(text),
    )
