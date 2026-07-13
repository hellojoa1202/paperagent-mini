# PaperAgent Mini

Agent Laboratory의 연구 자동화 구조를 참고하여 만든 multi-agent 논문 조사 프로젝트입니다.
사용자가 연구 주제를 입력하면 논문 검색부터 요약 검증, 문헌 종합, 연구 아이디어 평가,
구현 계획 및 prototype 코드 작성까지 하나의 pipeline으로 실행합니다.

## 전체 구조

```text
[Research Topic]
       │
       ▼
┌──────────────────────┐
│ 1. 논문 수집         │  arXiv 검색 → Abstract/PDF 추출
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 2. 요약 생성·평가    │  PaperReader ⇄ Reviewer
│                      │  기준 점수 미달 시 피드백 기반 재작성
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 3. 문헌 종합·검토    │  Postdoc → Critic
│                      │  ├─ Experiment Reviewer
│                      │  ├─ Novelty Reviewer
│                      │  └─ Impact Reviewer
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 4. 구현 설계·코드화  │  Method Extractor → Planner → Writer
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 5. 최종 보고         │  Professor Agent
└──────────┬───────────┘
           ▼
     [outputs/ 산출물]
```

CLI와 Claude Desktop MCP는 동일한 pipeline을 호출하는 서로 다른 실행 인터페이스입니다.

```text
CLI ─────────────┐
                 ├── run_pipeline(...) ── Agent pipeline ── outputs/
Claude Desktop ─ MCP
```

## 3rd 스터디 역할별 작업 폴더

현재 전체 프로젝트는 루트에서 실행하고, 네 명의 후속 과제는 [`team_tasks/`](./team_tasks/)에서
각자 독립적으로 실험합니다. 팀원은 `3rd`를 기준으로 자기 브랜치와 이니셜 폴더만 수정합니다.

| 담당 | 작업 폴더 | 목표 |
|---|---|---|
| GY | [`team_tasks/GY`](./team_tasks/GY/) | 요약·Reviewer reflection 성능 개선 |
| SH | [`team_tasks/SH`](./team_tasks/SH/) | prototype 검증과 실패 시 수정 |
| JM | [`team_tasks/JM`](./team_tasks/JM/) | ResearchGapAgent 구현 및 pipeline 통합 |
| JY | [`team_tasks/JY`](./team_tasks/JY/) | Postdoc·Critic·Professor prompt와 보고서 개선 |

UI와 MCP 연결은 완료 범위이므로 팀 과제에서 수정하지 않습니다. 상세 실행법과 완료 기준은 각 폴더의
README에 있습니다.

## Pipeline 구성

### 1. 논문 수집

사용자의 연구 주제를 arXiv 검색어로 변환하고 관련 논문을 가져옵니다.

```text
Research topic
   └─ search_arxiv()
       ├─ arXiv API 실검색
       ├─ rate-limit 발생 시 제한된 횟수만큼 재시도
       └─ read_arxiv_pdf()
           ├─ PDF 다운로드
           ├─ 텍스트 추출
           └─ 분석 후 임시 PDF 삭제
```

검색 실패를 감추기 위한 고정 fallback 논문은 사용하지 않습니다. 빠른 확인이 필요한 경우에는
PDF 전체 대신 arXiv abstract만 사용하도록 선택할 수 있습니다.

### 2. 논문 요약 생성과 품질 개선

논문을 한 번 요약하고 끝내지 않고, 작성 Agent와 평가 Agent가 피드백을 주고받습니다.

```text
Abstract/PDF text
       │
       ▼
PaperReaderAgent
       │  Problem / Key idea / Method / Experiments / Limitations
       ▼
ReviewerAgent
       │  정확성·구체성·완결성·명료성을 1~10점으로 평가
       │
       ├─ score >= MIN_REVIEW_SCORE ──────────────┐
       │                                          ▼
       └─ score < MIN_REVIEW_SCORE          최종 요약 채택
              │
              └─ 구체적 feedback
                       │
                       └─ PaperReaderAgent 재작성
                          (최대 MAX_REVISION_ROUNDS회)
```

Reviewer 응답은 점수, 강점, 약점, 수정 지시를 포함하는 JSON 구조로 요청합니다.
JSON 형식이 깨져도 원문 응답을 버리지 않고 feedback에 보존합니다.

### 3. 여러 논문 종합과 연구 관점 평가

개별 논문 검증이 끝나면 전체 연구 흐름을 정리하고, 서로 다른 평가 관점으로 결과를 검토합니다.

```text
검증된 논문 요약들
       │
       ▼
PostdocAgent
       │  연구 동향 / 논문 비교 / 공통 방법 / 미해결 문제 종합
       ▼
Literature Review
       ├─ CriticAgent
       │    누락된 관점, 숨은 가정, 근거가 약한 주장 검토
       │
       └─ 선택적 병렬 평가
            ├─ ExperimentReviewerAgent : metric, baseline, ablation
            ├─ NoveltyReviewerAgent    : 차별성, 신규성, incremental risk
            └─ ImpactReviewerAgent     : 활용 가능성, 연구 의의, 한계
```

Critic 검토는 문헌 리뷰에 포함됩니다. 세 가지 전문 Reviewer는 필요할 때만 실행하여
추가 API 호출과 실행 시간을 조절할 수 있습니다.

### 4. 구현 계획과 prototype 코드 생성

문헌조사를 실제 개발 작업으로 전환하는 단계입니다. 하나의 Agent가 계획과 코드를 동시에 만들지 않고
방법 추출, 설계, 구현 역할을 순차적으로 분리합니다.

```text
논문 요약 + Literature Review
       │
       ▼
MethodExtractionAgent
       │  알고리즘 / 수식 / 데이터 흐름 / pseudo-code 추출
       ▼
PrototypePlannerAgent
       │  의존성 / 모듈 / 입출력 / 검증 시나리오 설계
       ▼
PrototypeWriterAgent
       ├─ mock data 기반 실행 가능한 Python 코드
       └─ 설치·실행·예상 결과를 담은 안내 문서
```

생성 코드는 외부 데이터가 없어도 구조를 확인할 수 있는 prototype을 목표로 합니다.

### 5. 최종 보고서 구성

`ProfessorAgent`가 앞 단계의 문헌 리뷰, 방법 추출, 구현 계획과 선택 평가 결과를 모아
발표 또는 과제 제출에 사용할 수 있는 하나의 프로젝트 보고서로 재구성합니다.

```text
Literature Review ───────┐
Method Extraction ──────┤
Implementation Plan ────┼─ ProfessorAgent ── Final Project Report
Reviewer Reports ───────┘
```

## 생성 파일

모든 분석 결과를 Agent별 파일로 쪼개지 않고 하나의 보고서로 합칩니다.
코드를 생성하지 않으면 파일은 `research_report.md` 하나뿐입니다.

```text
outputs/
├── research_report.md          # 항상 생성
└── prototype.py                # 코드 생성 옵션을 켠 경우만 생성
```

`research_report.md` 내부 구조:

```text
1. Paper Summaries
2. Summary Quality Review
3. Literature Review
4. Critical Review
5. Specialized Reviews       # 선택
6. Implementation            # prototype 활성화 시
   ├─ Extracted Methods
   ├─ Implementation Plan
   └─ Prototype Guide
7. Final Synthesis            # 최종 보고 활성화 시
```

`prototype.py`는 보고서 안에 넣으면 실행하기 불편하기 때문에 코드 생성 옵션을 켰을 때만
별도 Python 파일로 저장합니다. 설치법과 구현 계획은 다시 파일을 만들지 않고 보고서에 포함합니다.

## 설치와 모델 설정

Python 3.11 이상을 권장합니다.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
cp .env.example .env
```

`.env`에서 사용할 provider 하나를 선택합니다. 실제 API 키가 들어 있는 `.env`는 Git에 올리지 않습니다.

| Provider | `LLM_PROVIDER` | 필요한 설정 |
|---|---|---|
| Ollama | `ollama` | `LLM_MODEL`, `OLLAMA_URL` |
| Anthropic | `anthropic` | `LLM_MODEL`, `ANTHROPIC_API_KEY` |
| OpenAI | `openai` | `LLM_MODEL`, `OPENAI_API_KEY` |
| Groq | `groq` | `LLM_MODEL`, `GROQ_API_KEY` |
| LM Studio | `lmstudio` | `LLM_MODEL`, `LM_STUDIO_BASE_URL` |
| EXAONE server | `exaone` | `LLM_MODEL`, `EXAONE_BASE_URL` |

Reviewer 반복 조건도 `.env`에서 변경할 수 있습니다.

```env
MIN_REVIEW_SCORE=7
MAX_REVISION_ROUNDS=2
```

## CLI 실행

빠른 abstract 기반 확인:

```bash
python -m paperagent run "LLM agents for scientific discovery" \
  --max-papers 2 --no-prototype --no-report --abstract-only --quick-review --no-critic
```

전체 pipeline:

```bash
python -m paperagent run "paper agent for literature review" --max-papers 3
```

세 가지 전문 Reviewer까지 실행:

```bash
python -m paperagent run "multi-agent research assistants" --max-papers 3 --extra-reviewers
```

## Claude Desktop MCP 연결

### 1. 프로젝트 준비

먼저 가상환경을 만들고 패키지를 설치한 뒤 `.env` 설정을 완료합니다.

```bash
python -m venv .venv
python -m pip install -e .
```

MCP 설정에는 Python과 서버 파일의 **절대경로**가 필요합니다.

- macOS/Linux 프로젝트 경로 확인: `pwd`
- macOS/Linux Python 경로 확인: `which python`
- Windows PowerShell 프로젝트 경로 확인: `(Get-Location).Path`
- Windows PowerShell Python 경로 확인: `(Get-Command python).Source`

### 2. Claude Desktop 설정 파일 열기

| 운영체제 | 설정 파일 |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | Claude Desktop 배포 방식에 따라 설정 위치가 다르므로 앱의 Developer/MCP 설정에서 확인 |

### 3. MCP 서버 등록

macOS/Linux 예시:

```json
{
  "mcpServers": {
    "paperagent-mini": {
      "command": "/absolute/path/to/paperagent-mini/.venv/bin/python",
      "args": [
        "/absolute/path/to/paperagent-mini/mcp_paperagent_server.py"
      ]
    }
  }
}
```

Windows 예시에서는 JSON의 역슬래시를 두 번 작성해야 합니다.

```json
{
  "mcpServers": {
    "paperagent-mini": {
      "command": "C:\\absolute\\path\\paperagent-mini\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\absolute\\path\\paperagent-mini\\mcp_paperagent_server.py"
      ]
    }
  }
}
```

API 키는 Claude Desktop JSON에 직접 넣지 않고 프로젝트의 `.env`에 저장합니다.

### 4. 연결 확인

Claude Desktop을 완전히 종료한 뒤 다시 시작하고 새 채팅에서 다음과 같이 요청합니다.

```text
paperagent-mini 실행해줘
```

MCP 연결이 정상이라면 채팅 안에 PaperAgent UI가 열립니다. UI에서 주제, 논문 수,
prototype 생성 여부를 선택하면 pipeline이 실행됩니다.

실행이 끝나면 다음 내용을 한 화면에서 확인할 수 있습니다.

- Agent 단계별 진행 상태
- 논문별 간단 요약 표
- `outputs/research_report.md` 저장 경로
- 선택한 경우 `outputs/prototype.py` 생성 여부

UI 표는 보고서에 들어가는 논문별 Agent 요약을 짧게 재구성한 미리보기입니다.
전체 내용은 `research_report.md`에서 확인합니다.

MCP App 실행 중 오류가 발생하면 `outputs/.paperagent_ui_checkpoint.json`에 완료 단계가 임시 저장됩니다.
화면의 `중단 지점부터 다시 실행`을 누르면 같은 주제와 옵션으로 검색·요약·검토 중 마지막으로 저장된
지점부터 재개합니다. 정상 완료되면 체크포인트 파일은 자동으로 삭제됩니다.

### UI를 수정할 때

실행용 단일 HTML은 저장소에 포함되어 있습니다. UI 소스를 수정한 경우에만 다시 빌드합니다.

```bash
cd ui_mockup
npm install
npm run build
```
