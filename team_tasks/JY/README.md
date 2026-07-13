# JY — Report Prompt & Output Quality

기존 과제의 PaperReader와 Literature Review prompt 작업을 이어서 최종 `research_report.md`의
가독성과 안정성을 개선합니다. 새 Agent를 만들지 않고 기존 Professor/report prompt와
deterministic 검사 함수를 개선합니다.

## 실행

```bash
git checkout -b 3rd-JY
cp team_tasks/JY/.env.example team_tasks/JY/.env
python team_tasks/JY/run_report_check.py team_tasks/JY/sample_report.md
python team_tasks/JY/run_report_check.py team_tasks/JY/sample_report.md --rewrite
python -m pytest team_tasks/JY/test_report_quality.py
```

`--rewrite` 없이 실행하면 API 호출 없이 형식만 검사합니다.

## 할 일

복잡한 Agent나 pipeline을 새로 만들지 않고, 아래 기능을 하나씩 완성합니다.

1. `build_report_prompt()`의 문장을 짧고 명확하게 정리
2. 한자·중국어·일본어 문자를 찾는 함수 작성
3. 같은 문장이 반복됐는지 찾는 함수 작성
4. 필수 섹션이 빠졌는지 찾는 함수 작성
5. 제목만 있고 내용이 없는 빈 섹션을 찾는 함수 작성
6. Paper Link가 없거나 URL 형식이 잘못됐는지 찾는 함수 작성
7. `research_report.md` 외에 불필요한 Markdown 파일이 생성됐는지 검사하는 함수 작성
8. prototype 선택이 `아니오`일 때 prototype 관련 문장이 남는지 검사
9. 문제 문장을 자동 삭제하기보다 `문제 목록`으로 먼저 보여주기
10. 정상 보고서 3개와 오류 보고서 3개를 만들어 테스트
11. 검사 전·후 결과를 이 README 하단에 표로 기록

LLM 성능 평가, 새 Agent 작성, workflow 재설계는 하지 않습니다. 대부분 문자열 검색, 정규식,
파일 목록 확인으로 해결할 수 있는 작업입니다. 한 기능씩 구현하고 테스트하면 됩니다.

## 완료 기준

- 한국어와 필요한 영문 기술 용어만 출력함
- 같은 문장 또는 섹션이 반복되지 않음
- 필수 섹션 누락을 검사함
- 기본 산출물은 `research_report.md`, prototype 선택 시에만 `prototype.py`가 생성됨
- 총 6개의 보고서 샘플에 대한 검사 결과가 README에 있음

## 통합 계약

조아가 통합할 대상은 `build_report_prompt`, `ReportCheck`, `check_report`입니다.
`rewrite_final_synthesis`는 기존 ProfessorAgent prompt로 옮깁니다. UI와 파일 개수는 변경하지 않습니다.
