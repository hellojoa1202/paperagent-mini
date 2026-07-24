# GY — 논문 요약 성능 개선

## 맡은 부분

`PaperReaderAgent`가 논문을 요약하고 `ReviewerAgent`가 그 요약을 평가하는 부분을 맡습니다.

## 해주면 되는 일

- 논문 요약이 더 정확하고 읽기 쉽게 나오도록 prompt를 수정해 주세요.
- Reviewer가 잘못된 내용이나 빠진 내용을 구체적으로 알려주도록 수정해 주세요.
- Reviewer 피드백을 받은 뒤 요약이 실제로 좋아지는지 논문 몇 개로 확인해 주세요.
- 확인한 결과를 이 README 아래에 간단히 적어주세요.

## 현재 폴더 파일

- `summary_quality.py`: 요약 prompt, Reviewer prompt, 재작성 흐름 예시
- `run_quality.py`: 요약 전·후를 실행해 보는 파일
- `sample_case.json`: 바로 실행해 볼 수 있는 논문 예시
- `test_summary_quality.py`: 간단한 테스트 예시
- `.env.example`: GY가 사용하던 Claude 또는 Ollama 설정 예시

현재 코드는 시작하기 위한 참고용입니다. 필요한 부분은 자유롭게 수정해도 됩니다.

## 시작 방법

```bash
git checkout -b 3rd-GY
cp team_tasks/GY/.env.example team_tasks/GY/.env
python team_tasks/GY/run_quality.py team_tasks/GY/sample_case.json
```

작업이 끝나면 `3rd-GY` 브랜치에 push하고 조아에게 알려주세요.

## 확인 결과 (GY)

prompt는 `src/paperagent/agents.py`에서 수정했습니다.

- 요약은 원문에 있는 수치·데이터셋만 쓰고, 없는 항목은 "원문에 명시되지 않음"으로 적도록 했습니다.
- Reviewer는 1~10 채점 기준을 주고, 어느 부분이 왜 틀렸는지 짚는 feedback을 내도록 했습니다.
- 재작성이 오히려 나빠지는 경우가 있어, `workflow.py`가 마지막 draft 대신 점수가 가장 높은 draft를 채택하도록 했습니다.

논문 2편(Attention, BERT)을 Claude로 돌려 확인했습니다.

- BERT 요약이 GLUE 80.5%, SQuAD 93.2/83.1 같은 수치를 원문 그대로 가져왔고, 초록에 없는 한계는 지어내지 않았습니다.
- 두 편 모두 첫 요약 8점에서 재작성 7점으로 조금 떨어졌지만, 점수가 높은 draft를 채택하는 로직 덕분에 8점 요약이 그대로 쓰였습니다.
- 재작성으로 점수가 오르는 경우는 `test_summary_quality.py`에 테스트로 남겨 두었습니다.

```bash
python team_tasks/GY/run_quality.py team_tasks/GY/sample_case.json     # Attention
python team_tasks/GY/run_quality.py team_tasks/GY/sample_case2.json    # BERT
```

API 키는 repo 루트 `.env`에 넣어야 합니다. `get_settings()`가 루트 `.env`를 다시 읽어 그 값을 우선 사용합니다.
