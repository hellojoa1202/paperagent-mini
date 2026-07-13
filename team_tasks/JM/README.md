# JM — ResearchGapAgent 추가

## 맡은 부분

여러 논문을 검토한 결과에서 아직 해결되지 않은 문제를 찾고, 다음에 해볼 실험을 제안하는 부분을
맡습니다.

## 해주면 되는 일

- `ResearchGapAgent`가 논문들의 공통 한계를 찾도록 만들어 주세요.
- 공통 한계를 바탕으로 다음에 해볼 만한 실험을 제안하게 해주세요.
- 실험에는 가설, 비교 방법, 평가 기준, 참고 논문이 포함되게 해주세요.
- 결과가 `research_report.md`의 `Next Experiments` 부분에 들어갈 수 있게 정리해 주세요.
- 몇 가지 주제로 실행해 보고 결과를 이 README 아래에 간단히 적어주세요.

## 현재 폴더 파일

- `research_gap_agent.py`: `ResearchGapAgent`와 보고서 연결 방식 예시
- `run_research_gap.py`: Agent를 실행해 보는 파일
- `sample_literature.md`: 바로 실행해 볼 수 있는 문헌 예시
- `test_research_gap_agent.py`: 간단한 테스트 예시
- `.env.example`: JM이 사용하던 `qwen3:8b` 설정 예시

현재 코드는 시작하기 위한 참고용입니다. 필요한 부분은 자유롭게 수정해도 됩니다.
루트 pipeline에 바로 합치지 말고 우선 이 폴더에서 정상 작동하도록 완성해 주세요.

## 시작 방법

```bash
git checkout -b 3rd-JM
cp team_tasks/JM/.env.example team_tasks/JM/.env
python team_tasks/JM/run_research_gap.py team_tasks/JM/sample_literature.md --topic "efficient transformer"
```

작업이 끝나면 `3rd-JM` 브랜치에 push하고 조아에게 알려주세요.
