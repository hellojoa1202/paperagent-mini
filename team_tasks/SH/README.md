# SH — Prototype 생성 및 검증 개선

## 맡은 부분

논문 내용을 바탕으로 `prototype.py`를 만들고, 생성된 코드가 실행되는지 확인하는 부분을 맡습니다.

## 해주면 되는 일

- 생성되는 `prototype.py`가 너무 복잡하지 않고 바로 실행되도록 prompt를 수정해 주세요.
- 생성된 코드에 문법 오류나 실행 오류가 있는지 확인해 주세요.
- 오류가 있으면 `PrototypeReviewerAgent`가 오류 내용을 전달하고 코드를 한 번 수정하게 해주세요.
- 정상 코드와 오류가 있는 코드로 실행해 보고 결과를 이 README 아래에 간단히 적어주세요.

## 현재 폴더 파일

- `prototype_reviewer.py`: 코드 검사와 `PrototypeReviewerAgent` 예시
- `run_prototype_review.py`: prototype을 검사해 보는 파일
- `sample_prototype.py`: 바로 검사해 볼 수 있는 코드 예시
- `test_prototype_reviewer.py`: 간단한 테스트 예시
- `.env.example`: SH가 사용하던 Ollama, OpenAI, Groq 설정 예시

현재 코드는 시작하기 위한 참고용입니다. 필요한 부분은 자유롭게 수정해도 됩니다.

## 시작 방법

```bash
git checkout -b 3rd-SH
cp team_tasks/SH/.env.example team_tasks/SH/.env
python team_tasks/SH/run_prototype_review.py team_tasks/SH/sample_prototype.py
```

작업이 끝나면 `3rd-SH` 브랜치에 push하고 조아에게 알려주세요.
