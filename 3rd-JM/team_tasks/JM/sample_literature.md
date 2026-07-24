# Sample Literature

- Paper A reports strong accuracy but evaluates only one small dataset.
- Paper B reduces inference cost but does not compare memory use.
- Both papers omit ablation studies for their main architectural component.


## Paper A

- Title: Efficient Transformer A
- Main result: 기존 Transformer보다 빠른 추론 속도를 보고했다.
- Evaluation: 하나의 소규모 데이터셋에서만 평가했다.
- Limitation: 대규모 데이터 일반화와 메모리 사용량을 검증하지 않았다.

## Paper B

- Title: Efficient Transformer B
- Main result: 파라미터 수와 연산량을 줄였다.
- Evaluation: 두 개의 소규모 데이터셋에서 비교했다.
- Limitation: 대규모 데이터 평가와 핵심 모듈의 ablation이 없다.

## Paper C

- Title: Memory-Aware Transformer
- Main result: attention 메모리 사용량을 줄였다.
- Evaluation: 메모리는 측정했지만 정확도 비교가 제한적이다.
- Limitation: 모델 크기에 따른 확장성을 확인하지 않았다.