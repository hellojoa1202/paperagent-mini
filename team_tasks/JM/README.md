# JM — ResearchGapAgent

기존 과제에서 전체 multi-agent 구조와 전문 Reviewer들을 확장했으므로, 이번에는 실제 다음 행동을
만드는 `ResearchGapAgent` 하나를 추가합니다. Reviewer를 더 늘리는 것이 아니라 검토된 문헌을
작고 검증 가능한 후속 실험으로 바꾸는 역할입니다.

## 실행

```bash
git checkout -b 3rd-JM
cp team_tasks/JM/.env.example team_tasks/JM/.env
python team_tasks/JM/run_research_gap.py team_tasks/JM/sample_literature.md --topic "efficient transformer"
python -m pytest team_tasks/JM/test_research_gap_agent.py
```

## 할 일

1. `ResearchGapAgent.propose()` prompt 개선
2. 가설, baseline, metric, ablation, risk, 근거 논문 형식 고정
3. 1~2주 안에 가능한 토이 실험을 우선하도록 조정
4. 필수 필드 누락 검사
5. 동일한 제안 반복 검사
6. 서로 다른 주제 3개로 실험
7. 좋은 제안과 좋지 않은 제안을 각각 1개 골라 이유 작성
8. 결과를 이 README 하단에 표로 기록

새 Agent는 `ResearchGapAgent` 하나만 구현합니다. 여러 Agent의 토론, 자동 ranking, 외부 논문 추가
검색은 범위에서 제외합니다.

## 완료 기준

- 요청한 개수만큼 구조화된 제안을 생성함
- 모든 제안에 근거 논문이 있음
- baseline과 metric이 빠지지 않음
- 같은 아이디어를 표현만 바꿔 반복하지 않음
- 세 주제의 결과와 간단한 품질 평가가 README에 있음

## 통합 계약

조아가 통합할 대상은 `ResearchGapAgent`, `build_research_gap_prompt`,
`validate_gap_output`입니다. 최종 pipeline에서는 Critic 이후, Prototype 계획 이전에 들어가며 결과는
별도 파일이 아니라 `research_report.md`의 `Next Experiments` 섹션에 합칩니다.
