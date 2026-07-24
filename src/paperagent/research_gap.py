"""Turn reviewed literature into evidence-backed, testable next experiments."""

from __future__ import annotations

import re
from dataclasses import dataclass

from paperagent.agents import BaseAgent


RESEARCH_GAP_STEP = "research_gap"
NEXT_EXPERIMENTS_HEADING = "## Next Experiments"
MIN_EXPERIMENT_COUNT = 1
MAX_EXPERIMENT_COUNT = 5


def normalize_experiment_count(count: int) -> int:
    return max(MIN_EXPERIMENT_COUNT, min(int(count), MAX_EXPERIMENT_COUNT))


def normalize_reference(reference: str) -> str:
    return re.sub(r"\s+", " ", reference.strip()).casefold()


def extract_literature_references(literature_text: str) -> set[str]:
    """Extract exact paper titles and arXiv IDs supplied to ResearchGapAgent."""
    references: set[str] = set()
    title_pattern = re.compile(
        r"^\s*-\s*(?:Paper\s+)?Title:\s*(.+?)\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    arxiv_pattern = re.compile(
        r"(?<!\d)(?:arXiv(?:\s+ID)?\s*:\s*)?"
        r"(\d{4}\.\d{4,5}(?:v\d+)?)(?!\d)",
        flags=re.IGNORECASE,
    )
    references.update(normalize_reference(title) for title in title_pattern.findall(literature_text))
    references.update(normalize_reference(arxiv_id) for arxiv_id in arxiv_pattern.findall(literature_text))
    return references


def split_references(reference_text: str) -> list[str]:
    return [item.strip() for item in reference_text.split("|") if item.strip()]


def find_unknown_references(
    references: list[str],
    allowed_references: set[str],
) -> list[str]:
    return [
        reference
        for reference in references
        if normalize_reference(reference) not in allowed_references
    ]


@dataclass(frozen=True)
class ResearchGapStageResult:
    text: str
    issues: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.issues


class ResearchGapAgent(BaseAgent):
    name = "ResearchGapAgent"
    role = "postdoc identifying evidence-backed research gaps and feasible experiments"

    def __init__(self, ask_fn=None):
        self.ask_fn = ask_fn or self.ask

    def propose(self, topic: str, literature_text: str, count: int = 3) -> str:
        return self.ask_fn(build_research_gap_prompt(topic, literature_text, count))

    def repair_format(self, previous_text: str, issues: list[str], count: int) -> str:
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        return self.ask_fn(
            f"""
아래는 이전에 생성한 실험 제안입니다.
{previous_text}

다음 형식 문제가 발견되었습니다.
{issues_text}

오류가 있는 필드만 수정하고 실험은 총 {count}개로 유지하세요.
설명이나 코드 블록 없이 수정된 전체 결과만 반환하세요.

### Common Research Gaps

#### Gap G1: 짧은 이름
- Description: 공통적으로 발견된 한계
- Supporting papers: 논문 1 | 논문 2

### Experiment 1: 짧은 이름
- Target gap: G1
- Hypothesis:
- Baseline:
- Metric:
- Ablation:
- Minimum implementation:
- Risk:
- Evidence: 논문 1 | 논문 2
""".strip()
        )


def build_research_gap_prompt(topic: str, literature_text: str, count: int = 3) -> str:
    count = normalize_experiment_count(count)
    return f"""
Research topic: {topic}

검토가 끝난 문헌 자료:
{literature_text}

최소 2편의 논문에서 공통으로 확인되는 한계만 찾으세요.
입력에 없는 사실, 논문, 성능 수치는 만들지 마세요.
공통 한계마다 G1, G2처럼 고유한 ID를 부여하세요.

### Common Research Gaps

#### Gap G1: 짧은 이름
- Description: 공통으로 발견된 한계
- Supporting papers: 입력에 있는 논문 제목 또는 arXiv ID 1 | 논문 제목 또는 arXiv ID 2

공통 한계를 검증할 수 있는 후속 실험 {count}개를 제안하세요.
각 실험은 1~2주 안에 mock data 또는 소규모 공개 데이터로 검증할 수 있어야 합니다.

### Experiment 1: 수행할 실험의 짧은 이름
- Target gap: G1
- Hypothesis:
- Baseline:
- Metric:
- Ablation:
- Minimum implementation:
- Risk:
- Evidence: 입력에 있는 논문 제목 또는 arXiv ID 1 | 논문 제목 또는 arXiv ID 2

모든 실험에 위 필드를 정확히 한 번씩 포함하세요.
Target gap에는 앞에서 정의한 Gap ID만 사용하세요.
Supporting papers와 Evidence는 `|`로 구분하고 서로 다른 논문을 2편 이상 포함하세요.
논문 제목과 arXiv ID는 입력에 적힌 값을 줄이거나 번역하지 말고 그대로 사용하세요.
한글과 필요한 영문 기술 용어만 사용하고 한자, 중국어, 일본어는 쓰지 마세요.
""".strip()


def validate_gap_output(
    text: str,
    expected_count: int,
    literature_text: str | None = None,
) -> list[str]:
    issues: list[str] = []
    expected_count = normalize_experiment_count(expected_count)
    allowed = extract_literature_references(literature_text or "")
    validate_source = literature_text is not None
    if validate_source and not allowed:
        issues.append("입력 문헌에서 검증 가능한 Title 또는 arXiv ID를 찾지 못했습니다.")

    experiment_blocks = re.findall(
        r"^### Experiment \d+:.*?(?=^### Experiment \d+:|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if len(experiment_blocks) != expected_count:
        issues.append(
            f"실험 개수 불일치: expected={expected_count}, actual={len(experiment_blocks)}"
        )

    defined_gap_ids = set(re.findall(r"^#### Gap (G\d+):", text, flags=re.MULTILINE))
    if not defined_gap_ids:
        issues.append("정의된 공통 Gap ID가 없습니다.")

    required_fields = (
        "Target gap",
        "Hypothesis",
        "Baseline",
        "Metric",
        "Ablation",
        "Minimum implementation",
        "Risk",
        "Evidence",
    )
    for index, block in enumerate(experiment_blocks, start=1):
        for field in required_fields:
            match = re.search(rf"^- {re.escape(field)}:[ \t]*(.*)$", block, re.MULTILINE)
            if match is None:
                issues.append(f"Experiment {index}의 필드가 누락되었습니다: {field}")
            elif not match.group(1).strip():
                issues.append(f"Experiment {index}의 필드가 비어 있습니다: {field}")

        target = re.search(r"^- Target gap:\s*(G\d+)\s*$", block, re.MULTILINE)
        if target is None:
            issues.append(f"Experiment {index}의 Target gap 형식이 잘못되었습니다.")
        elif target.group(1) not in defined_gap_ids:
            issues.append(f"Experiment {index}가 정의되지 않은 Gap {target.group(1)}을 참조합니다.")

        evidence = re.search(r"^- Evidence:\s*(.+)$", block, re.MULTILINE)
        if evidence:
            references = split_references(evidence.group(1))
            if len({normalize_reference(item) for item in references}) < 2:
                issues.append(f"Experiment {index}의 근거 논문이 2편 미만입니다.")
            if validate_source:
                unknown = find_unknown_references(references, allowed)
                if unknown:
                    issues.append(
                        f"Experiment {index}의 Evidence가 입력 문헌에 없습니다: {', '.join(unknown)}"
                    )

    gap_blocks = re.finditer(
        r"^#### Gap (G\d+):.*?(?=^#### Gap G\d+:|^### Experiment |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    for gap_match in gap_blocks:
        gap_id, block = gap_match.group(1), gap_match.group(0)
        description = re.search(r"^- Description:[ \t]*(.*)$", block, re.MULTILINE)
        if description is None:
            issues.append(f"Gap {gap_id}의 Description 필드가 누락되었습니다.")
        elif not description.group(1).strip():
            issues.append(f"Gap {gap_id}의 Description 필드가 비어 있습니다.")

        supporting = re.search(r"^- Supporting papers:\s*(.+)$", block, re.MULTILINE)
        if supporting is None:
            issues.append(f"Gap {gap_id}의 Supporting papers 형식이 잘못되었습니다.")
            continue
        references = split_references(supporting.group(1))
        if len({normalize_reference(item) for item in references}) < 2:
            issues.append(f"Gap {gap_id}의 Supporting papers가 2편 미만입니다.")
        if validate_source:
            unknown = find_unknown_references(references, allowed)
            if unknown:
                issues.append(
                    f"Gap {gap_id}의 Supporting papers가 입력 문헌에 없습니다: {', '.join(unknown)}"
                )
    return issues


def run_research_gap_stage(
    topic: str,
    literature_text: str,
    count: int = 3,
    ask_fn=None,
) -> ResearchGapStageResult:
    count = normalize_experiment_count(count)
    agent = ResearchGapAgent(ask_fn=ask_fn)
    text = agent.propose(topic, literature_text, count)
    issues = validate_gap_output(text, count, literature_text)
    if issues:
        text = agent.repair_format(text, issues, count)
    return ResearchGapStageResult(
        text=text,
        issues=tuple(validate_gap_output(text, count, literature_text)),
    )


def append_next_experiments(report_text: str, gap_text: str) -> str:
    """Insert or replace Next Experiments without creating another output file."""
    section = f"{NEXT_EXPERIMENTS_HEADING}\n\n{gap_text.strip()}"
    existing = re.compile(
        rf"{re.escape(NEXT_EXPERIMENTS_HEADING)}\n.*?(?=\n## |\Z)",
        flags=re.DOTALL,
    )
    if existing.search(report_text):
        return existing.sub(section, report_text).rstrip() + "\n"

    for heading in ("## 6. Implementation", "## 7. Final Synthesis"):
        marker = f"\n{heading}"
        if marker in report_text:
            return report_text.replace(marker, f"\n{section}\n\n{heading}", 1).rstrip() + "\n"
    return f"{report_text.rstrip()}\n\n{section}\n"
