# PaperAgent Pipeline 상세 설명

PaperAgent는 논문 수집, 요약 검증, 문헌 종합, prototype 구현, 최종 보고서 작성을
순서대로 실행합니다. CLI와 Claude Desktop MCP는 동일한 `run_pipeline()`을 사용합니다.

## 1. 논문 수집

사용자의 연구 주제를 arXiv 검색어로 변환하고 관련 논문을 가져옵니다.

```text
Research topic
   └─ search_arxiv()
       ├─ arXiv API 검색
       ├─ rate-limit 발생 시 제한된 횟수만큼 재시도
       └─ read_arxiv_pdf()
           ├─ PDF 다운로드
           ├─ 텍스트 추출
           └─ 분석 후 임시 PDF 삭제
```

검색 실패를 감추기 위한 고정 논문은 사용하지 않습니다. 빠른 실행이 필요하면 PDF 전체 대신
arXiv Abstract만 사용할 수 있습니다.

## 2. 논문 요약 생성과 품질 개선

`PaperReaderAgent`가 요약을 작성하고 `ReviewerAgent`가 원문과 비교하여 평가합니다.

```text
Abstract/PDF text
       |
       v
PaperReaderAgent
       |  Problem / Key idea / Method / Experiments / Limitations
       v
ReviewerAgent
       |  정확성·구체성·완결성·명료성을 1~10점으로 평가
       |
       ├─ score >= MIN_REVIEW_SCORE  -> 최종 요약 채택
       |
       └─ score < MIN_REVIEW_SCORE
              |
              └─ 구체적인 feedback
                       |
                       └─ PaperReaderAgent 재작성
                          최대 MAX_REVISION_ROUNDS회
```

Reviewer 응답은 점수, 강점, 약점과 수정 지시가 포함된 JSON으로 요청합니다.
JSON 형식이 깨진 경우에도 원문 응답을 버리지 않고 feedback으로 보존합니다.

요약 설명은 한국어 불렛으로 작성합니다. 모델명, 방법명, dataset, metric과 같은 주요 기술 용어는
원문의 영문 표기를 유지합니다.

## 3. 여러 논문 종합과 연구 관점 평가

개별 논문 검증이 끝나면 전체 연구 흐름과 논문 간 차이를 정리합니다.

```text
검증된 논문 요약
       |
       v
PostdocAgent
       |  연구 동향 / 논문 비교 / 공통 방법 / 미해결 문제
       v
Literature Review
       ├─ CriticAgent
       |    누락된 관점, 숨은 가정, 근거가 약한 주장 검토
       |
       ├─ 선택적 평가
       |    ├─ ExperimentReviewerAgent
       |    |    metric, baseline, ablation 검토
       |    ├─ NoveltyReviewerAgent
       |    |    차별성, 신규성과 incremental risk 검토
       |    └─ ImpactReviewerAgent
       |         활용 가능성, 연구 의의와 한계 검토
       |
       └─ ResearchGapAgent
            ├─ 두 편 이상에서 공통으로 확인되는 연구 공백 추출
            ├─ 입력 논문의 제목과 arXiv ID만 근거로 사용
            └─ 소규모 후속 실험 제안
```

세 가지 전문 Reviewer는 선택적으로 실행할 수 있습니다. `ResearchGapAgent`의 결과는 별도 파일을
만들지 않고 `research_report.md`의 `Next Experiments`에 포함합니다. 논문이 한 편이면
공통 연구 공백을 비교할 수 없으므로 해당 단계는 건너뜁니다.

## 4. 구현 계획과 prototype 코드 생성

문헌 조사 결과를 실행 가능한 toy prototype으로 변환합니다. 방법 추출, 설계, 구현과 검사를
서로 다른 Agent가 담당합니다.

```text
논문 요약 + Literature Review
       |
       v
MethodExtractionAgent
       |  알고리즘 / 수식 / 데이터 흐름 / pseudo-code 추출
       v
PrototypePlannerAgent
       |  의존성 / mock data / baseline / 입출력 / 검증 계획
       v
PrototypeWriterAgent
       |  NumPy 기반 실행 코드 생성
       v
PrototypeReviewerAgent
       ├─ Python 문법 검사
       ├─ import와 위험한 함수 호출 검사
       ├─ pass, 고정 성능 수치와 누락된 실행 블록 검사
       ├─ 구현 길이와 연구 주제 관련성 검사
       ├─ 임시 폴더에서 실제 실행
       └─ 실패 원인을 반영하여 코드 수정
```

prototype은 다음 구조를 가집니다.

- 스크립트 내부의 mock data 생성
- 같은 입력에 대한 baseline 구현
- 논문의 제안 방법을 단순화한 NumPy 구현
- baseline과 제안 방법 비교
- 실행 결과에서 최소 두 개의 지표 계산
- 입력, 중간 결과와 출력 shape 검사
- `run_prototype()`과 main 실행 블록

생성 코드는 표준 라이브러리와 NumPy만 사용합니다. PyTorch, TensorFlow, scikit-learn과 외부
데이터 파일은 사용하지 않습니다.

검사에 실패하면 오류 내용을 `PrototypeReviewerAgent`에 전달하여 자동으로 수정합니다.
전체 Prototype 단계는 세 번까지 다시 실행할 수 있습니다. 마지막 실행에서도 통과하지 못하면
문법과 import 안전성을 확인한 초안을 저장하고 `점검 필요` 상태를 표시합니다.

## 5. 최종 보고서 구성

`ProfessorAgent`가 앞 단계에서 생성된 내용을 하나의 보고서로 정리합니다.

```text
논문별 요약 ------------------+
요약 품질 평가 ---------------+
Literature Review ------------+-- ProfessorAgent -- research_report.md
Critical Review --------------+
Next Experiments -------------+
구현 계획과 prototype 안내 ----+
```

`research_report.md`에는 다음 항목이 포함됩니다.

```text
1. Paper Summaries
2. Summary Quality Review
3. Literature Review
4. Critical Review
5. Specialized Reviews        선택 실행
Next Experiments              두 편 이상 조사 시
6. Implementation             prototype 실행 시
7. Final Synthesis
```

저장 전에 누락되거나 비어 있는 절, 중복 문장, 잘못된 arXiv 링크, 이미지와 원치 않는 문자를
규칙 기반으로 검사합니다.

## 생성 결과

```text
outputs/
├── research_report.md
└── prototype.py       prototype 옵션을 켠 경우
```

Agent별 중간 파일은 만들지 않습니다. 문헌 조사와 검토 결과는 `research_report.md`에 합치고,
실행이 필요한 prototype 코드만 별도 Python 파일로 저장합니다.
