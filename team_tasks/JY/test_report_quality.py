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
