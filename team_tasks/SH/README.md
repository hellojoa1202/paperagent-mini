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

## 실행 및 검증 결과

개발 및 검증을 완료한 후, 정상 코드와 오류 코드를 기반으로 검증 및 자동 수정을 실행한 결과입니다.

### 1. 정상 코드 검증 (`sample_prototype.py`)
구문 오류 및 실행 오류가 없는 정상적인 프로토타입 코드를 검증했을 때의 출력 결과입니다.

```bash
$ python -m team_tasks.SH.run_prototype_review team_tasks/SH/sample_prototype.py --execute
review 1: passed=True, error=
saved: team_tasks\SH\outputs\prototype_fixed.py
```
- 결과: 추가적인 LLM 수정 단계 없이 즉시 검증을 통과하여 `prototype_fixed.py`로 저장되었습니다.

### 2. 오류 코드 검증 및 자동 수정
구문 오류가 존재하는 코드를 입력하고, `PrototypeReviewerAgent`가 이를 탐지하여 LLM을 통해 자동 복구(Repair)하는 검증 테스트를 진행했습니다. (테스트 환경에서 Mock Agent를 사용해 복구 흐름 검증)

- 입력 코드 (Syntax Error):
  ```python
  def broken(:
      pass
  ```
- 단위 테스트 실행 결과 (`test_prototype_reviewer.py`):
  ```bash
  $ pytest team_tasks/SH/test_prototype_reviewer.py
  collected 3 items

  team_tasks\SH\test_prototype_reviewer.py ...                             [100%]

  ============================== 3 passed in 0.25s ==============================
  ```
- 결과: 첫 번째 검증(review 1)에서 SyntaxError를 정상적으로 감지하고, `PrototypeReviewerAgent`가 이를 수정한 후 두 번째 검증(review 2)을 무사히 통과하여 복구된 코드가 저장되는 흐름을 확인했습니다.
