# SH — Prototype Validation & Repair

기존 과제의 `MethodExtraction → Planner → PrototypeWriter` 뒤에 실제 검증 단계를 붙입니다.
이 부분은 생성 코드가 실행되지 않는 문제를 feedback loop로 고치는 것이 목적이므로
`PrototypeReviewerAgent` 하나만 추가합니다.

## 실행

```bash
git checkout -b 3rd-SH
cp team_tasks/SH/.env.example team_tasks/SH/.env
python team_tasks/SH/run_prototype_review.py team_tasks/SH/sample_prototype.py
python team_tasks/SH/run_prototype_review.py team_tasks/SH/sample_prototype.py --execute
python -m pytest team_tasks/SH/test_prototype_reviewer.py
```

`--execute`는 LLM 생성 코드를 실제 실행하므로 개인 PC가 아니라 제한된 실습 환경에서만 사용합니다.

## 할 일

1. syntax, timeout, runtime error, 불필요한 무거운 dependency 검사 강화
2. 실패 원인을 PrototypeReviewerAgent가 짧고 정확하게 Writer에게 전달하도록 prompt 개선
3. 최대 1회 수정만으로 성공률을 높이기
4. 성공률, 평균 수정 횟수, timeout 비율 기록
5. 정상 코드 3개와 오류 코드 3개 이상으로 테스트

## 완료 기준

- 문법 오류를 항상 탐지함
- 실행 검사를 선택했을 때 exit code와 stderr를 보존함
- 실패한 코드가 한 번의 feedback으로 수정되는 예시가 있음
- 무한 수정 loop가 발생하지 않음

## 통합 계약

조아가 통합할 대상은 `PrototypeReviewerAgent`, `PrototypeReview`, `validate_code`,
`review_and_repair`입니다. 루트 pipeline 대신 이 폴더 안에서만 구현하고 통합 위치를 README에 기록합니다.
