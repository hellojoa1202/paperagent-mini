# JM — ResearchGapAgent & Pipeline Integration

기존 과제에서 전체 multi-agent 구조와 전문 Reviewer들을 확장했으므로, 이번에는 실제 다음 행동을
만드는 `ResearchGapAgent` 하나를 추가하고 실제 workflow에 연결합니다. Reviewer를 더 늘리는 것이
아니라 검토된 문헌을 작고 검증 가능한 후속 실험으로 바꾸는 역할입니다.

## 실행

```bash
git checkout -b 3rd-JM
cp team_tasks/JM/.env.example team_tasks/JM/.env
python team_tasks/JM/run_research_gap.py team_tasks/JM/sample_literature.md --topic "efficient transformer"
python team_tasks/JM/run_research_gap.py team_tasks/JM/sample_literature.md --topic "efficient transformer" --report team_tasks/JY/sample_report.md
python -m pytest team_tasks/JM/test_research_gap_agent.py
```

## 할 일

1. `ResearchGapAgent.propose()` prompt 개선
2. 가설, baseline, metric, ablation, risk, 근거 논문 형식 고정
3. 1~2주 안에 가능한 토이 실험을 우선하도록 조정
4. 필수 필드 누락 검사
5. 동일한 제안 반복 검사
6. Critic 다음, Prototype 이전에 실행되도록 pipeline 단계 설계
7. 체크포인트에 `research_gap` 단계를 저장하고 재실행 시 복원
8. 결과를 `research_report.md`의 `Next Experiments` 섹션에 병합
9. Agent 단위 테스트와 report 병합 테스트 작성
10. 서로 다른 주제 3개로 실험

새 Agent는 `ResearchGapAgent` 하나만 구현합니다. 여러 Agent의 토론, 자동 ranking, 외부 논문 추가
검색은 범위에서 제외합니다.

## 완료 기준

- 요청한 개수만큼 구조화된 제안을 생성함
- 모든 제안에 근거 논문이 있음
- baseline과 metric이 빠지지 않음
- 같은 아이디어를 표현만 바꿔 반복하지 않음
- 중단 후 재실행해도 완료된 ResearchGap 결과를 다시 생성하지 않음
- 별도 Markdown 산출물을 늘리지 않고 기존 보고서에 포함함

## 통합 계약

조아가 통합할 대상은 `ResearchGapAgent`, `run_research_gap_stage`, `append_next_experiments`,
`validate_gap_output`입니다. 최종 pipeline에서는 Critic 이후, Prototype 계획 이전에 들어갑니다.
