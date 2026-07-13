# JY — Postdoc, Critic, Professor Prompt & Report Quality

기존 과제의 Literature Review prompt 작업을 이어서 `PostdocAgent`, `CriticAgent`,
`ProfessorAgent`의 프롬프트와 최종 `research_report.md`의 가독성을 개선합니다. 새 Agent나
workflow는 만들지 않습니다.

## 실행

```bash
git checkout -b 3rd-JY
cp team_tasks/JY/.env.example team_tasks/JY/.env
python team_tasks/JY/run_report_check.py team_tasks/JY/sample_report.md
python team_tasks/JY/run_report_check.py team_tasks/JY/sample_report.md --generate postdoc
python team_tasks/JY/run_report_check.py team_tasks/JY/sample_report.md --generate critic
python team_tasks/JY/run_report_check.py team_tasks/JY/sample_report.md --generate professor
python -m pytest team_tasks/JY/test_report_quality.py
```

`--generate` 없이 실행하면 API 호출 없이 보고서 형식만 검사합니다.

## 할 일

복잡한 Agent나 pipeline을 새로 만들지 않고, 아래 기능을 하나씩 완성합니다.

1. `build_postdoc_prompt()`로 연구 흐름, 논문 비교, 공통 방법, open problem 형식 개선
2. `build_critic_prompt()`로 근거가 약한 주장과 빠진 관점을 구체적으로 지적
3. `build_professor_prompt()`로 구현 내용, 한계, 다음 단계를 짧은 불릿으로 정리
4. 입력에 없는 수치나 구현 내용을 만들지 않도록 세 프롬프트에 공통 제한 추가
5. 한자·중국어·일본어 문자를 찾는 검사
6. 같은 문장, 필수 섹션, 빈 섹션 검사
7. Paper Link와 prototype 관련 문구 검사
8. 세 프롬프트의 결과를 서로 다른 입력으로 비교
9. 정상 보고서와 오류 보고서 테스트 작성

LLM 성능 평가, 새 Agent 작성, workflow 재설계는 하지 않습니다. 대부분 문자열 검색, 정규식,
파일 목록 확인으로 해결할 수 있는 작업입니다. 한 기능씩 구현하고 테스트하면 됩니다.

## 완료 기준

- 한국어와 필요한 영문 기술 용어만 출력함
- 같은 문장 또는 섹션이 반복되지 않음
- 필수 섹션 누락을 검사함
- 기본 산출물은 `research_report.md`, prototype 선택 시에만 `prototype.py`가 생성됨
- 총 6개의 보고서 샘플에 대한 검사 결과가 README에 있음

## 통합 계약

조아가 통합할 대상은 `build_postdoc_prompt`, `build_critic_prompt`, `build_professor_prompt`,
`ReportCheck`, `check_report`입니다. 각각 기존 Agent의 prompt로 옮기며 UI와 파일 개수는 변경하지 않습니다.
