# Modular Paper Reader Agent

This folder is the "second step" version of the mini project.

The same idea from `1st_folder/paper_reader_agent.py` is split into files:

- `llm.py`: LLM API wrapper
- `arxiv_tool.py`: arXiv search and PDF text extraction
- `agent.py`: paper summarization and review-writing prompts
- `workflow.py`: orchestration logic
- `main.py`: command-line entry point

Run:

```bash
export OPENAI_API_KEY="your-key"
python main.py "LLM agents for scientific discovery"
```

Install:

```bash
pip install openai arxiv pypdf
```
