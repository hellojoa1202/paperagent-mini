## 1. PaperAgent Merged 구현 현황

~260528까지 나온 코드 폴더들 합쳐서 재구성
현재 구현된 범위:

1. arXiv에서 사용자가 입력한 주제 관련 논문 검색
2. PDF 다운로드 및 텍스트 추출
3. `PaperReaderAgent`가 논문별 한국어 요약 생성
4. 논문 요약 모음 `paper_summaries.md` 저장
5. 전체 문헌 리뷰 `final_literature_review.md` 생성
6. `MethodExtractionAgent`가 구현 가능한 방법/수식/알고리즘 추출
7. `PrototypePlannerAgent`가 구현 계획 생성
8. `PrototypeWriterAgent`가 mock data 기반 `prototype.py`와 실행 README 생성

현재 구현된 agent:

- `PaperReaderAgent`
- `MethodExtractionAgent`
- `PrototypePlannerAgent`
- `PrototypeWriterAgent`

아직 구현하지 않은 agent:

- `ReviewerAgent`
- `PostdocAgent`
- `ProfessorAgent`
- `MLEngineerAgent`
- `SWEngineerAgent`
- `ExperimentReviewerAgent`
- `NoveltyReviewerAgent`
- `ImpactReviewerAgent`
- `PaperSolver`
- `MLESolver`
- `AgentRxiv`

생성되는 파일:

- `outputs/paper_summaries.md`
- `outputs/final_literature_review.md`
- `outputs/method_extraction.md`
- `outputs/implementation_plan.md`
- `outputs/prototype.py`
- `outputs/prototype_readme.md`

## 2. 로컬 실행 방법

먼저 Claude Desktop에 `paperagent-merged` MCP 서버를 연결 필요 (자세한 MCP 설정 방법은 노션에 있는 가이드 참고)

기본 설정은 Ollama되어있고 .env에서 각자의 API 혹은 모델로 수정하면 됨 (**일단은 통일하지 않고 각자의 API 혹은 모델을 사용하는 것으로 결정**)

Claude Desktop 실행 방법:

```text
paperagent-merged MCP 실행해줘.
```

그러면 Claude가 순서대로 물어봄

1. 찾아볼 논문 주제
2. 읽을 논문 개수
3. `prototype.py`까지 만들지 여부

답변을 주면 Claude가 그 값을 모아서 `run_paper_literature_review`를 실행합니다.

예시 대화:

```text
사용자: paperagent-merged MCP 실행해줘.
Claude: 어떤 주제로 논문 리뷰를 돌릴까요?
사용자: VLA failure detection
Claude: 논문 몇 개를 읽을까요?
사용자: 3개
Claude: prototype.py까지 만들까요?
사용자: 네
```

한 번에 실행하고 싶으면 이렇게 말해도 됨

```text
paperagent-merged MCP를 사용해서 "multi-agent systems for scientific discovery" 주제로 arXiv 논문 3개를 찾아서 읽고,
논문 요약, 최종 문헌 리뷰, 구현 가능한 방법 추출, 구현 계획, prototype.py까지 만들어줘.
```
CLI로 직접 실행할 수도 있습니당

```bash
python -m paperagent run "여기에_찾아볼_논문_주제" --max-papers 3
```

## 3. 앞으로 구현해야 할 방향

최종 목표는 AgentLaboratory처럼 여러 agent가 역할을 나누어 논문 조사, 평가, 구현 계획, 프로토타입, 보고서 작성을 수행하는 paper agent 시스템입니다.

우선적으로 추가하면 좋은 agent:

1. `ReviewerAgent`
   - 논문 요약이 원문 abstract/PDF 내용과 맞는지 평가하고 피드백을 주는 agent

2. `PostdocAgent`
   - 여러 논문 요약을 더 깊게 비교하고 연구 흐름, 공통 방법론, 빈틈을 정리하는 agent

3. `ProfessorAgent`
   - 최종 보고서, README, paper draft를 정리하는 agent

4. `NoveltyReviewerAgent` / `ImpactReviewerAgent`
   - 기존 논문 대비 novelty, 연구 의의, 활용 가능성을 평가하는 agent

5. `SWEngineerAgent` / `MLEngineerAgent`
   - 생성된 prototype 코드를 정리하거나, 실제 실험 코드 구조로 발전시키는 agent

구현할 때 기본 목표:

- `agents.py`에 agent class 추가
- `workflow.py`에 agent 실행 단계 연결
- 결과를 markdown 또는 code 파일로 저장
- 가능하면 MCP tool 실행 결과에도 새 산출물 경로가 보이게 수정

자세한 후보 agent와 프로젝트 방향성은 `AGENT_ROADMAP.md`를 참고하세요.

---------------------

## 4. 과제 설명

### 과제 1. Claude Desktop 설치 및 MCP 연결 확인

각자 Claude Desktop을 설치하고, `paperagent-merged` MCP 서버를 연결해보기

확인할 것:

- Claude Desktop에서 `paperagent-merged` MCP tool이 보이는지
- `paperagent-merged MCP 실행해줘`라고 입력했을 때 Claude가 주제/논문 개수/prototype 여부를 물어보는지
- 답변 후 `run_paper_literature_review` tool이 호출되는지
- 실행 결과 파일이 `outputs/`에 생성되는지

### 과제 2. 각자 모델/API 연결 후 현재 코드 성능 확인

각자 가능한 방식으로 LLM을 연결해서 현재 구현된 agent pipeline을 실행해보기

확인할 것:

- 논문 검색이 정상적으로 되는지
- 논문 요약 품질이 괜찮은지
- 최종 literature review가 쓸 만한지
- `method_extraction.md`, `implementation_plan.md`, `prototype.py`가 실제로 도움이 되는지

### 과제 3. 요약본/실행 흐름 다듬어오기

현재 논문 요약본과 최종 literature review는 prompt가 임의로 작성되어있음 -> 다듬기 필요

해볼 것:

- 현재 나오는 결과 파일들을 보고 이해하기 쉽게 수정 (필요한 요소들은 추가하고, 불필요한 요소들은 삭제)
- 결과 파일 생성 동시에 클로드 대화창에도 저장되었다는 알림과 리뷰 관련 정보 (~~이런 논문들을 찾았고 각각의 논문들 한줄요약?)이 뜨게 수정

확인할 것:

- `paper_summaries.md`가 읽기 쉬운지
- `final_literature_review.md`가 한눈에 비교 가능한지
- Claude Desktop 실행 결과가 사용자가 바로 이해할 수 있는지
- 실행 방법 문서가 팀원이 따라하기 쉬운지

### 과제 4. Agent 추가하기 (~6/24)

현재 구현된 agent 위에 각자 다른 agent를 추가해서 AgentLaboratory와 비슷한 multi-agent 시스템으로 확장

추가 후보 agent:

| Agent | 역할 |
|---|---|
| `ReviewerAgent` | 논문 요약이 원문 abstract/PDF 내용과 맞는지 평가하고 피드백 생성 |
| `PostdocAgent` | 여러 논문 요약을 비교해 연구 흐름, 공통 방법론, 빈틈 정리 |
| `ProfessorAgent` | 최종 보고서, README, paper draft 형태로 결과 정리 |
| `MLEngineerAgent` | 생성된 prototype을 실제 실험 코드 구조로 발전 |
| `SWEngineerAgent` | 생성 코드 정리, 테스트 추가, 실행 구조 개선 |
| `ExperimentReviewerAgent` | 실험 설계, metric, baseline, ablation이 충분한지 평가 |
| `NoveltyReviewerAgent` | 기존 논문 대비 novelty와 차별점 평가 |
| `ImpactReviewerAgent` | 연구 의의, 활용 가능성, 한계, impact 평가 |
| `PaperSolver` | 문헌 리뷰와 결과를 논문 초안 형태로 작성 |
| `MLESolver` | 실험 코드 생성/수정/실행 루프 담당 |
| `AgentRxiv` | 읽은 논문, 요약, metadata를 저장하고 다시 검색 |

각자 구현 후 확인할 것:

- 새 agent가 기존 workflow에 자연스럽게 연결되는지
- 새 agent의 결과물이 파일로 저장되는지
- Claude MCP 실행 결과에서 새 산출물을 확인할 수 있는지
