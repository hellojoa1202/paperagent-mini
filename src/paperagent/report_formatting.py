"""Deterministic cleanup for Markdown produced by local LLM agents."""

from __future__ import annotations

import re


_MARKDOWN_IMAGE = re.compile(
    r"!\[[^\]]*]\([^)]*\)|!\[[^\]]*]\[[^\]]*]",
    flags=re.MULTILINE,
)
_HTML_IMAGE = re.compile(
    r"<(?:img|picture|svg)\b[^>]*>.*?</(?:picture|svg)>|<(?:img|svg)\b[^>]*?/?>",
    flags=re.IGNORECASE | re.DOTALL,
)
_EMOJI = re.compile(
    "["
    "\U0001F000-\U0001FAFF"
    "\u2600-\u27BF"
    "\uFE0E-\uFE0F"
    "\u200D"
    "]",
    flags=re.UNICODE,
)
_CHATTY_LINE = re.compile(
    r"^(?:물론입니다|네[,!. ]|아래는|요청하신|다음은|필요\s*시|원하시면|이 안내서를 통해)",
    flags=re.IGNORECASE,
)
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_REDUNDANT_TITLES = {
    "논문 요약 모음집 (paper summaries)",
    "paper summaries",
    "reviewer feedback",
}

_TECHNICAL_TERM_REPLACEMENTS = (
    (re.compile(r"안모니", re.IGNORECASE), "anomaly"),
    (re.compile(r"어텐션", re.IGNORECASE), "attention"),
    (re.compile(r"임베딩", re.IGNORECASE), "embedding"),
    (re.compile(r"레이턴시", re.IGNORECASE), "latency"),
    (re.compile(r"트랜스포머", re.IGNORECASE), "Transformer"),
    (re.compile(r"토큰"), "token"),
    (re.compile(r"데이터셋"), "dataset"),
    (re.compile(r"베이스라인"), "baseline"),
    (re.compile(r"어블레이션"), "ablation"),
    (re.compile(r"파라미터"), "parameter"),
    (
        re.compile(
            r"Fadde(?:ev|이|이ev)?[-–— ]?(?:Popov|포프)\s*정체",
            re.IGNORECASE,
        ),
        "Faddeev-Popov ghost",
    ),
    (re.compile(r"정체\s*작용"), "ghost action"),
    (re.compile(r"가우스\s*조정"), "gauge fixing"),
    (re.compile(r"마스터\s*워드\s*식"), "Master Ward Identity"),
    (re.compile(r"양자\s*전자기\s*작용"), "Yang-Mills action"),
    (re.compile(r"유한\s*재정리"), "finite renormalization"),
)


def normalize_technical_terms(text: str) -> str:
    """Restore standard English spellings for commonly mistranslated terms."""
    normalized = text
    for pattern, replacement in _TECHNICAL_TERM_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def remove_visual_noise(text: str) -> str:
    """Remove images, emoji, and decorative Unicode from Markdown."""
    cleaned = normalize_technical_terms(text)
    cleaned = _MARKDOWN_IMAGE.sub("", cleaned)
    cleaned = _HTML_IMAGE.sub("", cleaned)
    cleaned = _EMOJI.sub("", cleaned)
    cleaned = re.sub(r"[ \t]+$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def clean_agent_markdown(
    text: str,
    *,
    heading_offset: int = 2,
    remove_code_blocks: bool = True,
) -> str:
    """Clean an agent fragment and nest its headings under the report section."""
    cleaned = remove_visual_noise(text)
    lines: list[str] = []
    in_code_block = False

    for line in cleaned.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if not remove_code_blocks:
                lines.append(line)
            continue
        if in_code_block and remove_code_blocks:
            continue
        if in_code_block:
            lines.append(line)
            continue
        if stripped and _CHATTY_LINE.match(stripped):
            continue
        if stripped == "---":
            continue
        if stripped.startswith(">"):
            line = stripped[1:].lstrip()

        heading = _HEADING.match(line)
        if heading:
            title = heading.group(2).strip()
            if re.sub(r"\s+", " ", title).lower() in _REDUNDANT_TITLES:
                continue
            level = min(6, len(heading.group(1)) + max(0, heading_offset))
            line = f"{'#' * level} {title}"
        lines.append(line)

    return remove_visual_noise("\n".join(lines))


def find_visual_noise(text: str) -> tuple[str, ...]:
    """Find image or decorative content that must never reach a report."""
    found: list[str] = []
    found.extend(_MARKDOWN_IMAGE.findall(text))
    found.extend(_HTML_IMAGE.findall(text))
    found.extend(_EMOJI.findall(text))
    return tuple(found)
