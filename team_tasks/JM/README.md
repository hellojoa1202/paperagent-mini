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
2. 각 제안에 가설, baseline, metric, ablation, risk, 근거 논문 포함
3. 1~2주 안에 가능한 토이 실험을 우선하도록 조정
4. 막연하거나 서로 중복되는 제안을 탐지하는 validator 추가
5. qwen3:8b 기준으로 최소 3개 주제 실험

## 완료 기준

- 요청한 개수만큼 구조화된 제안을 생성함
- 모든 제안에 근거 논문이 있음
- baseline과 metric이 빠지지 않음
- 같은 아이디어를 표현만 바꿔 반복하지 않음

## 통합 계약

조아가 통합할 대상은 `ResearchGapAgent`, `build_research_gap_prompt`,
`validate_gap_output`입니다. 최종 pipeline에서는 Critic 이후, Prototype 계획 이전에 들어가며 결과는
별도 파일이 아니라 `research_report.md`의 `Next Experiments` 섹션에 합칩니다.
