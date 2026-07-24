from team_tasks.JY.report_quality import (
    build_critic_prompt,
    build_postdoc_prompt,
    build_professor_prompt,
    check_report,
)


def test_detects_cjk_and_duplicate_lines() -> None:
    repeated = "이 문장은 중복 검사를 위한 충분히 긴 한국어 샘플 문장입니다."
    result = check_report(f"{repeated}\n{repeated}\n翻译")
    assert result.cjk_count > 0
    assert repeated in result.duplicate_lines


def test_detects_empty_section() -> None:
    text = (
        "## Open problems\n"
        "## Common methods\n"
        "- 여러 논문이 공유하는 방법을 정리한 충분히 긴 문장입니다.\n"
    )
    result = check_report(text)
    assert "Open problems" in result.empty_sections
    assert "Common methods" not in result.empty_sections


def test_container_heading_is_not_empty() -> None:
    text = (
        "## Specialized Reviews\n"
        "### Experiment Review\n"
        "- 실험 설계가 구체적인지 확인한 충분히 긴 검토 문장입니다.\n"
    )
    assert check_report(text).empty_sections == ()


def test_detects_broken_paper_links() -> None:
    text = (
        "- [2401.99999](https://arxiv.org/abs/2401.11111) id가 어긋난 링크 예시입니다.\n"
        "- [2401.55555](https://example.com/paper) arxiv가 아닌 링크 예시입니다.\n"
        "- [정상](https://arxiv.org/abs/2401.55555) 이 링크는 정상입니다.\n"
    )
    broken = check_report(text).broken_links
    assert len(broken) == 2
    assert any("불일치" in item for item in broken)
    assert any("arXiv 링크가 아님" in item for item in broken)


def test_clean_report_passes() -> None:
    text = (
        "## 1. Paper Summaries\n"
        "- [2401.12345](https://arxiv.org/abs/2401.12345) 논문 핵심을 요약한 충분히 긴 문장.\n"
        "## 2. Summary Quality Review\n"
        "- 원문과 요약의 일치 여부를 확인한 충분히 긴 검토 문장입니다.\n"
        "## 3. Literature Review\n"
        "- 여러 논문의 공통 흐름을 정리한 충분히 긴 종합 문장입니다.\n"
        "## 4. Critical Review\n"
        "- 근거가 약한 주장을 구체적으로 지적한 충분히 긴 문장입니다.\n"
        "## 7. Final Synthesis\n"
        "- 현재 구현과 남은 일을 짧게 정리한 충분히 긴 문장입니다.\n"
    )
    result = check_report(text)
    assert result.passed
    assert result.missing_sections == ()


def test_prompt_forbids_fabrication_and_cjk() -> None:
    prompts = (
        build_postdoc_prompt("topic", "source"),
        build_critic_prompt("topic", "source"),
        build_professor_prompt("topic", "source"),
    )
    assert all("한자" in prompt for prompt in prompts)
    assert all("만들지 않기" in prompt for prompt in prompts)


def test_each_agent_prompt_has_its_own_job() -> None:
    assert "Paper comparison" in build_postdoc_prompt("topic", "source")
    assert "문제 위치 / 이유 / 수정 제안" in build_critic_prompt("topic", "source")
    assert "Final Synthesis" in build_professor_prompt("topic", "source")
