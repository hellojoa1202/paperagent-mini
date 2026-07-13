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
