# PaperAgent Mini

연구 주제를 입력하면 arXiv 논문 검색부터 요약 검증, 문헌 비교, prototype 작성,
최종 보고서 생성까지 실행하는 multi-agent 프로젝트입니다.

## 실행 예시

<!-- PaperAgent 실행 화면 이미지 한 장을 여기에 추가 -->

## 전체 구조

```text
[Research Topic]
       |
       v
+----------------------+
| 1. 논문 수집         |  arXiv 검색, Abstract/PDF 추출
+----------+-----------+
           v
+----------------------+
| 2. 요약 생성·검증    |  PaperReader <-> Reviewer
+----------+-----------+
           v
+----------------------+
| 3. 문헌 종합·검토    |  Postdoc, Critic, ResearchGap
+----------+-----------+
           v
+----------------------+
| 4. 구현 설계·코드화  |  Method, Planner, Writer, Reviewer
+----------+-----------+
           v
+----------------------+
| 5. 최종 보고서       |  Professor Agent
+----------+-----------+
           v
        outputs/
```

CLI와 Claude Desktop MCP는 같은 pipeline을 호출합니다.

```text
CLI ------------+
                +-- run_pipeline() -- Agent pipeline -- outputs/
Claude Desktop -+
```

## Pipeline 구성

단계별 Agent 역할과 검증 흐름은 [Pipeline 상세 설명](./docs/PIPELINE.md)에서 확인할 수 있습니다.

### 1. 논문 수집

```text
Research topic
  -> arXiv 검색
  -> rate-limit 재시도
  -> Abstract 또는 PDF 본문 추출
```

고정된 예시 논문을 사용하지 않으며 실제 arXiv 검색 결과만 처리합니다.

### 2. 요약 생성과 검증

```text
PaperReaderAgent
  -> Problem / Key idea / Method / Experiments / Limitations 요약
  -> ReviewerAgent가 정확성·구체성·완결성 평가
  -> 기준 점수 미달 시 피드백을 반영해 재작성
```

각 논문의 핵심 내용은 한국어 불렛으로 작성하고, 모델명과 방법명 같은 주요 기술 용어는
원문의 영문 표기를 유지합니다.

### 3. 문헌 종합과 연구 관점 평가

```text
검증된 논문 요약
  -> PostdocAgent: 연구 흐름과 논문 비교
  -> CriticAgent: 약한 근거와 누락 검토
  -> ResearchGapAgent: 공통 연구 공백과 후속 실험 제안
```

필요하면 Experiment, Novelty, Impact Reviewer를 추가로 실행할 수 있습니다.

### 4. prototype 생성과 검사

```text
MethodExtractionAgent
  -> PrototypePlannerAgent
  -> PrototypeWriterAgent
  -> PrototypeReviewerAgent
  -> prototype.py
```

prototype은 NumPy와 mock data를 사용하며 다음 구조를 포함합니다.

- mock data 생성
- baseline 구현
- 논문의 제안 방법 구현
- baseline과 제안 방법 비교
- 최소 두 개의 계산 지표 출력
- 문법, import, shape, 실행 결과 검사

검사에 실패하면 오류 내용을 바탕으로 자동 수정합니다. 반복 수정 후에도 실패하면
초안을 저장하고 `점검 필요` 상태로 표시합니다.

### 5. 최종 보고서

`ProfessorAgent`가 앞 단계의 결과를 하나의 `research_report.md`로 정리합니다.

```text
논문별 요약
요약 품질 평가
문헌 비교와 비판
후속 실험
구현 계획과 prototype 안내
최종 종합
```

## 생성 파일

```text
outputs/
├── research_report.md    # 항상 생성
└── prototype.py          # prototype 옵션을 켠 경우 생성
```

중간 Agent별 파일은 만들지 않고 보고서 하나로 합칩니다.

## 시작하기

### 설치

Python 3.11 이상을 권장합니다.

```bash
git clone https://github.com/hellojoa1202/paperagent-mini.git
cd paperagent-mini
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
copy .env.example .env
```

### 모델 설정

`.env`에서 사용할 provider 하나만 활성화합니다. Ollama는 API 키 없이 사용할 수 있습니다.

| Provider | `LLM_PROVIDER` | 필요한 값 |
|---|---|---|
| Ollama | `ollama` | `LLM_MODEL`, `OLLAMA_URL` |
| Anthropic | `anthropic` | `LLM_MODEL`, `ANTHROPIC_API_KEY` |
| OpenAI | `openai` | `LLM_MODEL`, `OPENAI_API_KEY` |
| xAI | `xai` | `LLM_MODEL`, `XAI_BASE_URL`, `XAI_API_KEY` |
| Groq | `groq` | `LLM_MODEL`, `GROQ_API_KEY` |
| LM Studio | `lmstudio` | `LLM_MODEL`, `LM_STUDIO_BASE_URL` |

API 키와 서버 주소를 입력하는 위치는 `.env.example`의 주석에서 확인할 수 있습니다.
실제 키가 들어 있는 `.env`는 Git에 올리지 않습니다.

### CLI 실행

빠른 Abstract 기반 실행:

```bash
python -m paperagent run "LLM agents for scientific discovery" \
  --max-papers 2 --no-prototype --abstract-only --quick-review
```

전체 pipeline 실행:

```bash
python -m paperagent run "multi-agent research assistants" --max-papers 3
```

## Claude Desktop MCP 연결

가상환경의 Python과 `mcp_paperagent_server.py`의 절대경로를 Claude Desktop 설정에 등록합니다.

macOS/Linux:

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

Windows:

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

설정 파일 위치:

| 운영체제 | 경로 |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | Claude Desktop의 Developer/MCP 설정에서 확인 |

설정 후 Claude Desktop을 완전히 종료했다가 다시 실행합니다.

```text
paperagent-mini 실행해줘.
```
