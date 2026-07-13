# 3rd Iteration Team Tasks

루트는 조아가 최종 통합할 PaperAgent 전체 프로젝트이고, 아래 폴더는 각 팀원이 자기 담당 기능만
반복 실험할 수 있는 독립 작업 공간입니다. UI와 MCP 서버는 이번 과제 범위가 아닙니다.

| 폴더 | 담당 | 새 Agent |
|---|---|---|
| `GY/` | 논문 요약과 Reviewer reflection 성능 개선 | 없음 |
| `SH/` | prototype 문법·실행 검증과 실패 시 수정 | `PrototypeReviewerAgent` |
| `JM/` | 문헌에서 research gap과 후속 실험 생성 | `ResearchGapAgent` |
| `JY/` | 최종 보고서 프롬프트와 형식 품질 개선 | 없음 |

## 공통 시작 방법

```bash
git clone https://github.com/hellojoa1202/paperagent-mini.git
cd paperagent-mini
git checkout 3rd
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

자기 폴더의 `.env.example`을 `.env`로 복사하고 README의 runner를 실행합니다.

## 브랜치와 제출

서로의 파일을 덮어쓰지 않도록 다음 브랜치를 사용합니다.

```text
3rd-GY
3rd-SH
3rd-JM
3rd-JY
```

자기 이니셜 폴더만 수정하고, 필요한 경우 루트 pipeline 연결 방법을 README의 `통합 계약`에
기록합니다. `src/paperagent`, `mcp_paperagent_server.py`, `ui_mockup`은 직접 수정하지 않습니다.

완료 후 자기 브랜치에 push하고 조아에게 브랜치 이름과 실행 결과를 전달합니다.
