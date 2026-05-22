# PaperAgent Mini

2026-1 PROMETHEUS Agent Study toy-project

AgentLaboratory의 literature review 흐름을 참고해서 만든 미니 논문 읽기 agent 프로젝트입니다.

원본 AgentLaboratory 코드는 아래 저장소에서 확인할 수 있습니다.

- https://github.com/SamuelSchmidgall/AgentLaboratory

## 구성

```text
1st_folder/
  paper_reader_agent.py   # 한 파일로 보는 기본 논문 읽기 agent

2nd_folder/
  llm.py                  # LLM 호출
  arxiv_tool.py           # arXiv 검색 / PDF 읽기
  agent.py                # 논문 요약 / 리뷰 작성 agent
  workflow.py             # 전체 실행 흐름
  main.py                 # 실행 진입점
```

## 1st_folder와 2nd_folder의 의미

### 1st_folder

처음 agent 구조를 이해하기 위한 **단일 파일 MVP 버전**입니다.

arXiv 검색, PDF 읽기, LLM 호출, 논문 요약, 최종 literature review 작성 흐름이 `paper_reader_agent.py` 한 파일 안에 들어 있습니다. 스터디 초반에는 이 파일을 위에서 아래로 읽으면서 전체 흐름을 파악하면 됩니다.

### 2nd_folder

1st 버전이 잘 돌아간 뒤 확장하기 위한 **모듈 분리 버전**입니다.

기능을 `llm.py`, `arxiv_tool.py`, `agent.py`, `workflow.py`, `main.py`로 나누어 두었습니다. 이후 논문 비교표 생성, 구현 계획 생성, prototype 코드 생성 같은 기능을 붙일 때는 2nd 구조를 기반으로 확장하면 좋습니다.

## 실행 준비

필요 패키지:

```bash
pip install openai arxiv pypdf
```

Ollama를 사용할 경우:

```bash
ollama pull qwen2.5:7b
```

## 1st_folder 실행

```bash
cd 1st_folder
cp .env.example .env
python paper_reader_agent.py "LLM agents for scientific discovery"
```

결과는 `1st_folder/outputs/final_literature_review.md`에 저장됩니다.

## 참고

이 프로젝트는 AgentLaboratory 원본 전체를 재구현하는 것이 아니라, 그중 문헌 조사 단계의 아이디어를 참고해 논문 검색, PDF 읽기, 요약, 최종 literature review 생성을 작게 구현한 학습용 프로젝트입니다.
