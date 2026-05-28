# PaperAgent 향후 구현 방향

이 문서는 현재 `paperagent-merged`가 실제 과제 구현 기준으로 어디까지 되어 있는지와, 앞으로 AgentLaboratory 구조를 참고해 어떤 agent를 추가할지 정리한 문서입니다.

GY의 `3rd_folder`는 현재 통합 대상에서 제외했습니다. 따라서 아래의 "현재 구현"은 GY/SH의 `1st_folder`, `2nd_folder`에 들어 있던 과제 코드만 기준으로 합니다.

## 현재 구현된 agent

| Agent | 현재 역할 | 출처 |
|---|---|---|
| `PaperReaderAgent` | arXiv 논문을 읽고 개별 요약 및 최종 literature review 생성 | GY/SH 1st, 2nd |
| `MethodExtractionAgent` | 논문 요약에서 구현 가능한 방법, 수식, 알고리즘 추출 | SH 1st |
| `PrototypePlannerAgent` | 추출된 방법론을 prototype 구현 계획으로 변환 | SH 1st |
| `PrototypeWriterAgent` | mock data 기반 prototype.py 및 실행 README 생성 | SH 1st |

## 아직 구현되지 않은 agent

| 우선순위 | Agent | 목표 역할 | 담당자가 구현할 핵심 기능 |
|---|---|---|---|
| 1 | `ReviewerAgent` | 논문 요약 품질 평가 | 요약 정확성, 구체성, 누락 내용 평가 및 재작성 피드백 생성 |
| 1 | `PostdocAgent` | 여러 논문 요약의 심화 종합 | 연구 흐름, 공통 방법론, 한계, 후속 아이디어 정리 |
| 1 | `ProfessorAgent` | 최종 보고서/논문 초안 총괄 | abstract, introduction, contribution, conclusion 형태로 정리 |
| 2 | `ExperimentReviewerAgent` | 실험 설계 평가 | metric, baseline, ablation, reproducibility 체크 |
| 2 | `NoveltyReviewerAgent` | novelty 평가 | 기존 논문 대비 차별점과 incremental 여부 평가 |
| 2 | `ImpactReviewerAgent` | 연구 의의 평가 | 활용 가능성, 학술적/실용적 impact, 한계 평가 |
| 2 | `MLEngineerAgent` | 실험 코드 생성/실행 | prototype을 넘어 dataset loader, baseline, metric, runner 생성 |
| 2 | `SWEngineerAgent` | 코드 품질과 패키징 | 생성 코드 정리, 테스트 생성, CLI/API 정리 |
| 3 | `PaperSolver` | paper draft 작성 | literature review와 실험 결과를 논문 형식으로 변환 |
| 3 | `MLESolver` | 실험 코드 반복 개선 | 실행 실패 로그를 읽고 코드 수정/개선 |
| 3 | `AgentRxiv` | 논문 저장/검색 서버 | 읽은 논문, 요약, metadata 저장 및 재검색 |

## 추천 구현 순서

1. `ReviewerAgent`
   - 현재는 LLM이 쓴 요약을 검증하는 단계가 없습니다.
   - 가장 먼저 추가하면 품질 확인과 재작성 루프를 만들 수 있습니다.

2. `PostdocAgent`
   - 현재 `PaperReaderAgent.write_literature_review()`가 종합 리뷰까지 같이 맡고 있습니다.
   - 역할을 분리하면 AgentLaboratory 구조와 더 가까워집니다.

3. `ProfessorAgent`
   - 최종 발표/보고서용 문서를 정리하는 역할입니다.
   - 여러 산출물을 하나의 coherent report로 묶는 데 필요합니다.

4. reviewer 3종 분리
   - `ExperimentReviewerAgent`, `NoveltyReviewerAgent`, `ImpactReviewerAgent`를 추가하면 논문 평가 구조가 더 명확해집니다.

5. `MLEngineerAgent`와 `SWEngineerAgent`
   - SH의 prototype 생성 흐름을 실제 실험 코드 생성/정리 역할로 발전시킵니다.

## 프로젝트 방향성

- 단기 목표: arXiv 검색, 논문 읽기, 요약, 문헌 리뷰, 구현 계획까지 한 번에 도는 MCP tool 완성
- 중기 목표: 현재 하나의 agent가 맡는 일을 여러 역할 agent로 분리
- 장기 목표: Claude에서 MCP tool로 호출하면 논문 조사부터 실험 계획, 프로토타입, 보고서 초안까지 생성하는 paper agent 시스템 구현
