# PaperAgent Mini

2026-1 PROMETHEUS Agent Study toy-project

원본 AgentLaboratory 코드
- https://github.com/SamuelSchmidgall/AgentLaboratory
-> 해당 사이트에서 전체 git clone 하고 패키지 다운 필요

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

## 추가 설치 필요

필요 패키지:

```bash
pip install openai arxiv pypdf
```

Ollama를 사용할 경우:

```bash
ollama pull qwen2.5:7b
```

## 참고

이 프로젝트는 AgentLaboratory 원본 전체를 재구현하는 것이 아니라, 그중 문헌 조사 단계의 아이디어를 참고해 논문 검색, PDF 읽기, 요약, 최종 literature review 생성을 작게 구현한 학습용 프로젝트입니다.
