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

1. `build_summary_prompt()`와 `build_review_prompt()` 개선
2. 정확성, 누락, 구체성, 명료성, hallucination risk 평가 기준 보정
3. 최소 3개 논문으로 수정 전·후 점수 비교
4. 점수만 올리기 위한 장황한 요약이 되지 않는지 확인
5. 테스트와 짧은 실험 결과를 이 README 하단에 기록

## 완료 기준

- 평균 점수가 재작성 후 상승하거나, 오르지 않은 사례의 원인이 설명됨
- Reviewer feedback이 원문 근거와 수정 위치를 구체적으로 지시함
- 중국어, 중복 섹션, 근거 없는 수치가 결과에 남지 않음

## 통합 계약

조아가 최종 통합할 대상은 `build_summary_prompt`, `build_review_prompt`, `QualityScore`입니다.
루트 `src/paperagent`와 UI는 수정하지 말고 이 폴더 안에서만 작업합니다.
