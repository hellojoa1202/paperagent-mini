"""A focused new Agent that converts reviewed literature into testable experiments."""

from __future__ import annotations

import re
from dataclasses import dataclass

from paperagent.agents import BaseAgent


RESEARCH_GAP_STEP = "research_gap"
NEXT_EXPERIMENTS_HEADING = "## Next Experiments"
MIN_EXPERIMENT_COUNT = 1
MAX_EXPERIMENT_COUNT = 5


def normalize_experiment_count(count: int) -> int:
    return max(
        MIN_EXPERIMENT_COUNT,
        min(int(count), MAX_EXPERIMENT_COUNT),
    )


def normalize_reference(reference: str) -> str:
    """논문 제목과 arXiv ID 대조를 위한 Normalizatoin"""
    return re.sub(r"\s+", " ", reference.strip()).casefold()

def extract_literature_references(literature_text: str) -> set[str]:
    """입력 문헌에서 논문제목, arXiv ID 추출하기"""
    references: set[str] = set()

    title_pattern = re.compile(
        r"^\s*-\s*(?:Paper\s+)?Title:\s*(.+?)\s*$", # '- Title: 논문 이름' 이나 '- Paper Title' 같은거 뽑아오기
        flags=re.IGNORECASE | re.MULTILINE,
    )
    arxiv_pattern = re.compile(
        r"(?<!\d)(?:arXiv(?:\s+ID)?\s*:\s*)?"
        r"(\d{4}\.\d{4,5}(?:v\d+)?)(?!\d)",  # arXiv ID: YYMM.NNNNNvV (2104.12345v1) 이런 식
        flags=re.IGNORECASE,
    )

    for title in title_pattern.findall(literature_text):
        references.add(normalize_reference(title))

    for arxiv_id in arxiv_pattern.findall(literature_text):
        references.add(normalize_reference(arxiv_id))

    return references

def split_references(reference_text: str) -> list[str]:
    """`Paper A | Paper B` 형식의 참고 논문 목록을 분리하기"""
    return [
        reference.strip()
        for reference in reference_text.split("|")
        if reference.strip()
    ]


def find_unknown_references(
    references: list[str],
    allowed_references: set[str],
) -> list[str]:
    """입력 문헌에 존재하지 않는 논문 제목 또는 ID를 반환하기"""
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

    def checkpoint_value(self) -> dict[str, str]:
        return {"step": RESEARCH_GAP_STEP, "text": self.text}


class ResearchGapAgent(BaseAgent):
    def __init__(self, ask_fn=None):
        self.ask_fn = ask_fn or self.ask

    name = "ResearchGapAgent"
    role = "postdoc identifying evidence-backed research gaps and feasible experiments"

    def repair_format(self, previous_text: str, issues: list[str], count: int,) -> str:
        issues_text = "\n".join(f"- {issue}"for issue in issues)
        return self.ask_fn(
            f"""
아래는 이전에 생성한 실험 제안입니다.
{previous_text}

다음 형식 문제가 발견되었습니다.
{issues_text}

연구 내용의 의미는 최대한 유지하세요.
오류 목록에 해당하는 필드만 수정하고, 나머지 내용은 변경하지 마세요.
실험은 총 {count}개여야 합니다.
설명이나 코드 블록을 추가하지 말고 수정된 전체 결과만 반환하세요.
Target gap에는 공통 한계의 짧은 이름이 아니라 G1, G2 형식의 Gap ID만 작성하세요.

각 실험은 아래 필드명을 매우 정확하게 사용해야 합니다.

### Common Research Gaps

#### Gap G1: 짧은 이름
- Description: 공통적으로 발견된 한계
- Supporting papers: 논문 1 | 논문 2

### Experiment N: 짧은 이름
- Target gap: G1
- Hypothesis:
- Baseline:
- Metric:
- Ablation:
- Minimum implementation:
- Risk:
- Evidence: 논문 1 | 논문 2
""".strip())

    def propose(self, topic: str, literature_text: str, count: int = 3) -> str:
        return self.ask_fn(build_research_gap_prompt(topic, literature_text, count))


def build_research_gap_prompt(topic: str, literature_text: str, count: int = 3) -> str:
    #count = max(1, min(count, 5))
    count = normalize_experiment_count(count)
    return f"""
Research topic: {topic}

검토가 끝난 문헌 자료:
{literature_text}

먼저 입력 문헌에서 공통 한계를 찾으세요.
공통 한계는 최소 2편의 논문에서 확인되는 한계만 사용하세요.
한 논문에만 해당하는 한계는 공통 한계로 사용하면 절대 안됩니다.
자료에 없는 사실이나 성능 수치는 절대로 만들지 마세요.

각 공통 한계는 G1, G2처럼 중복되지 않는 ID를 부여하세요.
공통 한계가 1개뿐이어도 괜찮습니다.

공통 한계는 다음 형식으로 작성하세요.

### Common Research Gaps

#### Gap G1: 짧은 이름
- Description: 공통으로 발견된 한계
- Supporting papers: 논문 제목 또는 arXiv ID 1 | 논문 제목 또는 arXiv ID 2

Supporting papers의 논문들을 반드시 | 기호로 구분해야합니다.
Supporting papers에는 서로 다른 논문들을 최소 2편 이상 포함하세요.

그 다음 공통 한계를 검증할 수 있는 후속 실험 {count}개를 제안하세요.
각 실험의 Target Gap에는 앞에서 정의한 Gap ID 하나만 사용하세요.
존재하지 않는 Gap ID를 만들지 마세요.
하나의 Gap ID를 여러 실험에서 사용해도 괜찮습니다.
실험 개수를 맞추기 위해 한 논문만의 한계를 사용하지 마세요.

각 실험은 아래 형식을 정확히 사용하세요.

### Experiment N: 짧은 이름
- Target gap: G1
- Hypothesis:
- Baseline:
- Metric:
- Ablation:
- Minimum implementation:
- Risk:
- Evidence: 논문 제목 또는 arXiv ID 1 | 논문 제목 또는 arXiv ID 2

Evidence의 논문들을 반드시 | 기호로 구분해야합니다.
Evidence에는 서로 다른 논문을 최소 2편 이상 포함하세요.
Target gap에는 공통 한계의 짧은 이름이 아니라 G1, G2 형식의 Gap ID만 작성하세요.
각 필드 이름 앞에 번호, 문자 또는 다른 기호를 추가하지 마세요.
Experiment 제목에는 Gap ID만 쓰지 말고, 수행할 실험을 설명하는 짧은 이름을 작성하세요.

Supporting papers와 Evidence에는 입력 문헌의 Title 또는 arXiv ID에 실제로 등장하는 값만 원문 그대로 작성하세요.

논문 제목을 줄이거나 번역하거나 철자를 절대로 변경하지 마세요.
입력 문헌에 없는 논문 제목이나 arXiv ID를 새로 만들지 마세요.

거대한 학습이나 비싼 데이터 수집이 필요한 제안보다는, 1~2주 안에 검증 가능한 토이 실험을 우선하세요.
""".strip()

def validate_gap_output(text: str, expected_count: int, literature_text: str | None = None,) -> list[str]:
    issues: list[str] = []

    allowed_references = (extract_literature_references(literature_text) if literature_text is not None else set())
    validate_against_source = literature_text is not None
    if validate_against_source and not allowed_references:
        issues.append("입력 문헌에서 검증 가능한 Title 또는 arXiv ID를 찾지 못했습니다.")

    experiment_count = text.count("### Experiment ")
    if experiment_count != expected_count:
        issues.append(f"실험 개수 불일치: expected={expected_count}, actual={experiment_count}")

    required_fields = ("Target gap", "Hypothesis", "Baseline", "Metric", "Ablation", "Minimum implementation", "Risk", "Evidence",)

    # for field in required_fields:
    #     if text.count(f"- {field}:") < expected_count:
    #         issues.append(f"필드 누락: {field}")

    # Find Defined Gap ID: 정규표현식 Capturing Group으로 ID 찾아서 불러오기
    defined_gap_ids = set(re.findall(r"^#### Gap (G\d+):", text, flags=re.MULTILINE,))
    if not defined_gap_ids:
        issues.append("정의된 공통 Gap ID가 없습니다.")

    gap_blocks = re.finditer(
        r"^#### Gap (G\d+):.*?(?=^#### Gap G\d+:|^### Experiment |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )

    experiment_blocks = re.findall(
        r"^### Experiment \d+:.*?(?=^### Experiment \d+:|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )

    for index, block in enumerate(experiment_blocks, start=1):
        for field in required_fields:
            field_match = re.search(rf"^- {re.escape(field)}:[ \t]*(.*)$", block, flags=re.MULTILINE)
            if field_match is None:
                issues.append(f"Experiment {index}의 필드가 누락되었습니다: {field}")
                continue

            field_value = field_match.group(1).strip()

            if not field_value:
                issues.append(f"Experiment {index}의 필드가 비어 있습니다: {field}")

        target_gap_match = re.search(r"^- Target gap:\s*(G\d+)\s*$", block, flags=re.MULTILINE,)
        if target_gap_match is None:
            issues.append(f"Experiment {index}의 Target gap 형식이 잘못되었습니다.")
        else:
            target_gap_id = target_gap_match.group(1)

            if target_gap_id not in defined_gap_ids:
                issues.append(
                    f"Experiment {index}가 정의되지 않은 Gap "
                    f"{target_gap_id}을 참조합니다."
                )

        evidence_match = re.search(r"^- Evidence:\s*(.+)$", block, flags=re.MULTILINE,)
        if evidence_match is None:
            continue
        references = split_references(evidence_match.group(1))

        unique_references = {normalize_reference(reference) for reference in references}
        # references=[
        #     reference.strip() for reference in evidence_match.group(1).split("|") if reference.strip()
        # ]
        # unique_references={
        #     reference.casefold() for reference in references
        # }

        if len(unique_references) < 2:
            issues.append(f"Experiment {index}의 근거 논문이 2편 미만입니다.")

        if validate_against_source:
            unknown_references = find_unknown_references(references, allowed_references)
            if unknown_references:
                issues.append(f"Experiment {index}의 Evidence가 입력 문헌에 없습니다: "
                              f"{', '.join(unknown_references)}")

    for gap_match in gap_blocks:
        gap_id = gap_match.group(1)
        gap_block = gap_match.group(0)

        description_match = re.search(r"^- Description:[ \t]*(.*)$", gap_block, flags=re.MULTILINE)

        if description_match is None:
            issues.append(f"Gap {gap_id}의 Description 필드가 누락되었습니다.")
        elif not description_match.group(1).strip():
            issues.append(f"Gap {gap_id}의 Description 필드가 비어 있습니다.")


        supporting_papers_match = re.search(
            r"^- Supporting papers:\s*(.+)$",
            gap_block,
            flags=re.MULTILINE,
        )
        if supporting_papers_match is None:
            issues.append(
                f"Gap {gap_id}의 Supporting papers 형식이 잘못되었습니다."
            )
            continue
        supporting_papers = split_references(supporting_papers_match.group(1))
        unique_supporting_papers = {normalize_reference(paper) for paper in supporting_papers}
        #supporting_papers = [paper.strip() for paper in supporting_papers_match.group(1).split("|") if paper.strip()]
        #unique_supporting_papers={paper.casefold() for paper in supporting_papers}
        if len(unique_supporting_papers)<2:
            issues.append(
                f"Gap {gap_id}의 Supporting papers가 2편 미만입니다."
            )
        if validate_against_source:
            unknown_papers = find_unknown_references(supporting_papers, allowed_references)
            if unknown_papers:
                issues.append(f"Gap {gap_id}의 Supporting papers가 입력 문헌에 없습니다: "
                              f"{', '.join(unknown_papers)}")


    return issues


def run_research_gap_stage(topic: str, literature_text: str, count: int = 3, ask_fn=None) -> ResearchGapStageResult:
    """Standalone contract for the workflow step JM will integrate."""
    count = normalize_experiment_count(count
                                       )
    agent = ResearchGapAgent(ask_fn = ask_fn)

    text = agent.propose(topic, literature_text, count)
    issues = validate_gap_output(text, count, literature_text)

    if issues:
        text = agent.repair_format(text, issues, count)

    final_issues = validate_gap_output(text, count, literature_text)
    return ResearchGapStageResult(text=text, issues=tuple(final_issues))


def append_next_experiments(report_text: str, gap_text: str) -> str:
    """Insert or replace one Next Experiments section without creating another file."""
    section = f"{NEXT_EXPERIMENTS_HEADING}\n\n{gap_text.strip()}"
    existing = re.compile(
        rf"{re.escape(NEXT_EXPERIMENTS_HEADING)}\n.*?(?=\n## |\Z)",
        flags=re.DOTALL,
    )
    if existing.search(report_text):
        return existing.sub(section, report_text).rstrip() + "\n"

    insertion_points = ("## 6. Implementation", "## 7. Final Synthesis", "## Final Synthesis")
    for heading in insertion_points:
        marker = f"\n{heading}"
        if marker in report_text:
            return report_text.replace(marker, f"\n{section}\n\n{heading}", 1).rstrip() + "\n"
    return f"{report_text.rstrip()}\n\n{section}\n"
