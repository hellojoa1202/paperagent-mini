# JY — Agent 프롬프트 및 최종 보고서 개선

## 맡은 부분

여러 논문을 종합하고 검토한 뒤 최종 `research_report.md`로 정리하는 프롬프트 부분을 맡습니다.

## 해주면 되는 일

- `PostdocAgent`가 여러 논문의 흐름과 차이점을 깔끔하게 정리하도록 prompt를 수정해 주세요.
- `CriticAgent`가 근거가 약하거나 빠진 내용을 구체적으로 알려주도록 prompt를 수정해 주세요.
- `ProfessorAgent`가 최종 보고서를 짧은 불릿 중심으로 작성하도록 prompt를 수정해 주세요.
- 보고서에 중국어, 반복 문장, 빈 항목, 잘못된 Paper Link가 없는지 확인해 주세요.
- 몇 가지 보고서로 실행해 보고 결과를 이 README 아래에 간단히 적어주세요.

## 현재 폴더 파일

- `report_quality.py`: 세 Agent의 prompt와 보고서 검사 방식 예시
- `run_report_check.py`: 보고서를 검사하거나 각 prompt를 실행해 보는 파일
- `sample_report.md`: 바로 검사해 볼 수 있는 보고서 예시
- `test_report_quality.py`: 간단한 테스트 예시
- `.env.example`: JY가 사용하던 `qwen2.5:7b` 또는 OpenAI 설정 예시

현재 코드는 시작하기 위한 참고용입니다. 필요한 부분은 자유롭게 수정해도 됩니다.

## 시작 방법

```bash
git checkout -b 3rd-JY
cp team_tasks/JY/.env.example team_tasks/JY/.env
python team_tasks/JY/run_report_check.py team_tasks/JY/sample_report.md
```

작업이 끝나면 `3rd-JY` 브랜치에 push하고 조아에게 알려주세요.

## 작업 내용

### 1. 세 Agent prompt 개선 (`src/paperagent/agents.py`)

- **PostdocAgent** — 여러 논문의 공통 흐름과 차이점이 한눈에 보이도록 `Paper comparison`
  표를 포함한 불릿 중심 literature review를 쓰도록 수정. 주장마다 근거 논문을
  `(arXiv ID)`로 표기하게 함.
- **CriticAgent** — 막연한 비판 대신 `문제 위치 / 이유 / 수정 제안` 세 줄 형식으로
  근거가 약하거나 빠진 내용을 구체적으로 지적하도록 수정.
- **ProfessorAgent** — 최종 보고서를 긴 줄글이 아니라 짧은 불릿 중심으로 쓰도록 수정.
- 세 Agent 모두 출력에 `_remove_unwanted_cjk()`를 적용해 실수로 섞인 한자/일본어
  조각을 제거하고, prompt에 "항목을 비워두지 않기 / 없는 수치를 만들지 않기" 규칙을 추가.

### 2. 보고서 자동 검사 강화 (`report_quality.py`)

`check_report()`에 두 가지 검사를 추가했습니다. 기존(중국어·반복 문장·누락 섹션·길이 초과)에 더해:

- **빈 항목(`empty_sections`)** — 제목만 있고 내용이 없는 섹션 탐지. 하위 제목(더 깊은
  `###`)이 있는 컨테이너 섹션은 오탐하지 않도록 레벨을 고려.
- **잘못된 Paper Link(`broken_links`)** — 빈 링크, arXiv 링크의 표시 id와 URL id 불일치,
  arXiv id처럼 보이지만 arXiv 주소가 아닌 링크를 탐지.

## 실행 및 검증 결과

`qwen2.5:7b`(ollama) 없이도 확인할 수 있도록 LLM 호출이 없는 결정론적 검사기를
정상 보고서와 문제 보고서에 실행했습니다.

### 정상 보고서 (`sample_report.md`)

```bash
$ python team_tasks/JY/run_report_check.py team_tasks/JY/sample_report.md
{
  "missing_sections": [], "cjk_count": 0, "duplicate_lines": [],
  "empty_sections": [], "broken_links": [], "too_long": false,
  "passed": true
}
```

### 문제 보고서 (`sample_report_bad.md`)

일부러 중국어·반복 문장·빈 항목·잘못된 링크를 넣은 보고서입니다. 네 가지 문제를 모두 잡아냅니다.

```bash
$ python team_tasks/JY/run_report_check.py team_tasks/JY/sample_report_bad.md
{
  "missing_sections": [],
  "cjk_count": 2,
  "duplicate_lines": ["- 여러 논문의 공통 흐름을 정리한 충분히 긴 문장입니다 반복 검사용."],
  "empty_sections": ["4. Critical Review"],
  "broken_links": [
    "[2401.99999](https://arxiv.org/abs/2401.11111) — 표시 id와 링크 id 불일치",
    "[2401.55555](https://example.com/not-arxiv) — arXiv 링크가 아님"
  ],
  "too_long": false,
  "passed": false
}
```

### 테스트

```bash
$ pytest team_tasks/JY/test_report_quality.py
7 passed
```

- 검사 항목별 테스트(중국어/반복/빈 항목/잘못된 링크/정상 통과)와 세 prompt의 역할
  분리 테스트를 포함해 7개 모두 통과합니다.
- 이 환경에는 `pytest`가 없어 각 `test_*` 함수를 직접 호출해 통과를 확인했습니다.
