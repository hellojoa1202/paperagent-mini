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

1. `build_report_prompt()`를 짧고 안정적인 한국어 보고서가 나오도록 개선
2. 중국어·번역 지시문·중복 문장·빈 섹션 검사 강화
3. 구현하지 않은 기능을 구현했다고 쓰는 문제 방지
4. prototype 선택 여부에 따라 관련 문구를 자연스럽게 처리
5. 서로 다른 보고서 3개 이상으로 검사 결과 기록

## 완료 기준

- 한국어와 필요한 영문 기술 용어만 출력함
- 같은 문장 또는 섹션이 반복되지 않음
- 필수 섹션 누락을 검사함
- 기본 산출물은 `research_report.md`, prototype 선택 시에만 `prototype.py`가 생성됨

## 통합 계약

조아가 통합할 대상은 `build_report_prompt`, `ReportCheck`, `check_report`입니다.
`rewrite_final_synthesis`는 기존 ProfessorAgent prompt로 옮깁니다. UI와 파일 개수는 변경하지 않습니다.
