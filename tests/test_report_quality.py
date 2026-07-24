from __future__ import annotations

from paperagent.report_quality import check_report


def test_clean_report_passes_selected_sections() -> None:
    report = """
# Report

## Paper Summaries
내용

## Literature Review
검토 내용
""".strip()

    result = check_report(
        report,
        required_sections=("Paper Summaries", "Literature Review"),
    )

    assert result.passed


def test_checker_finds_unwanted_cjk_and_broken_link() -> None:
    report = """
## Paper Summaries
中文

## Literature Review
[2401.00001](https://example.com)
""".strip()

    result = check_report(
        report,
        required_sections=("Paper Summaries", "Literature Review"),
    )

    assert result.cjk_count == 2
    assert result.broken_links


def test_checker_rejects_image_and_emoji_content() -> None:
    rocket = "\U0001F680"
    result = check_report(
        f"# Report\n\n![plot](plot.png)\n\n{rocket} 결과",
        required_sections=("Report",),
    )

    assert result.visual_noise
    assert not result.passed
