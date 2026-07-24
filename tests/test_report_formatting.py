from paperagent.report_formatting import (
    clean_agent_markdown,
    find_visual_noise,
    normalize_technical_terms,
    remove_visual_noise,
)


def test_remove_visual_noise_removes_emoji_and_markdown_images() -> None:
    check_mark = "\u2705"
    rocket = "\U0001F680"
    text = (
        f"## 결과 {check_mark}\n"
        "![chart](chart.png)\n"
        '<img src="other.png" alt="other">\n'
        f"- 실행 완료 {rocket}"
    )

    cleaned = remove_visual_noise(text)

    assert check_mark not in cleaned
    assert rocket not in cleaned
    assert "chart.png" not in cleaned
    assert "other.png" not in cleaned
    assert "- 실행 완료" in cleaned


def test_clean_agent_markdown_nests_headings_and_drops_chatty_preamble() -> None:
    text = "물론입니다. 아래는 결과입니다.\n# 방법\n## 입력\n- mock data"

    cleaned = clean_agent_markdown(text)

    assert "물론입니다" not in cleaned
    assert "### 방법" in cleaned
    assert "#### 입력" in cleaned


def test_clean_agent_markdown_removes_html_images_and_code_dump() -> None:
    check_mark = "\u2705"
    text = f"""
# {check_mark} 구현
<img src="result.png">
```python
print("전체 코드는 별도 파일에 저장")
```
- 핵심 흐름만 설명
""".strip()

    cleaned = clean_agent_markdown(text)

    assert check_mark not in cleaned
    assert "result.png" not in cleaned
    assert "print(" not in cleaned
    assert "### 구현" in cleaned
    assert "- 핵심 흐름만 설명" in cleaned
    assert not find_visual_noise(cleaned)


def test_normalize_technical_terms_keeps_recognizable_english_spellings() -> None:
    text = (
        "안모니 검증, 트랜스포머 어텐션, 임베딩 레이턴시, "
        "Faddeev-Popov 정체, 가우스 조정, 마스터 워드 식"
    )

    normalized = normalize_technical_terms(text)

    assert "안모니" not in normalized
    assert "anomaly" in normalized
    assert "Transformer attention" in normalized
    assert "embedding latency" in normalized
    assert "Faddeev-Popov ghost" in normalized
    assert "gauge fixing" in normalized
    assert "Master Ward Identity" in normalized
