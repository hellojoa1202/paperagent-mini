# GY — Summary Quality & Reflection

기존 과제에서 구현한 `PaperReader ↔ Reviewer` 재작성 loop를 정량적으로 개선합니다. 새 Agent는
추가하지 않고 두 Agent의 prompt, 평가 rubric, feedback 품질을 높이는 작업입니다.

## 실행

```bash
git checkout -b 3rd-GY
cp team_tasks/GY/.env.example team_tasks/GY/.env
python team_tasks/GY/run_quality.py team_tasks/GY/sample_case.json
python -m pytest team_tasks/GY/test_summary_quality.py
```

기본은 기존 GY 환경과 같은 Claude Haiku입니다. API를 쓰지 않을 경우 `.env`에서 Ollama 설정으로
바꿉니다. 실제 키는 절대 push하지 않습니다.

## 할 일

1. `build_summary_prompt()` 개선
2. `build_review_prompt()` 개선
3. 정확성, 누락, 구체성, 명료성, hallucination risk 평가 기준 보정
4. 동일 논문에 대해 수정 전·후 점수를 자동 비교
5. 논문 3개로 반복 실험
6. 점수만 올리기 위한 장황한 요약이 되지 않는지 확인
7. 테스트 3개 이상 작성
8. 논문별 `최초 점수 → 수정 점수`를 이 README 하단에 표로 기록

모델 비교, arXiv 검색, UI 수정은 범위에서 제외합니다. 요약과 Reviewer 성능에만 집중합니다.

## 완료 기준

- 평균 점수가 재작성 후 상승하거나, 오르지 않은 사례의 원인이 설명됨
- Reviewer feedback이 원문 근거와 수정 위치를 구체적으로 지시함
- 중국어, 중복 섹션, 근거 없는 수치가 결과에 남지 않음
- 실행 결과 표 3행과 실패 사례 설명 1개가 README에 있음

## 통합 계약

조아가 최종 통합할 대상은 `build_summary_prompt`, `build_review_prompt`, `QualityScore`입니다.
루트 `src/paperagent`와 UI는 수정하지 말고 이 폴더 안에서만 작업합니다.
