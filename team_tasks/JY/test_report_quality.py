from team_tasks.JY.report_quality import build_report_prompt, check_report


def test_detects_cjk_and_duplicate_lines() -> None:
    repeated = "이 문장은 중복 검사를 위한 충분히 긴 한국어 샘플 문장입니다."
    result = check_report(f"{repeated}\n{repeated}\n翻译")
    assert result.cjk_count > 0
    assert repeated in result.duplicate_lines


def test_prompt_forbids_fabrication_and_cjk() -> None:
    prompt = build_report_prompt("topic", "source")
    assert "한자" in prompt
    assert "만들지 않기" in prompt
