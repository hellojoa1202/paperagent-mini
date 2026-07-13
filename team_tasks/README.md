# 3rd Team Tasks

## GY

- PaperReader 요약 prompt 개선
- Reviewer 평가 prompt와 rubric 개선
- Reviewer feedback을 반영한 재작성 전·후 점수 비교
- 논문 3개로 요약 성능 확인
- 결과와 테스트 작성

상세 내용: [`GY/README.md`](./GY/README.md)

## SH

- 생성된 `prototype.py` 문법 오류 검사
- runtime error와 timeout 검사
- 무거운 dependency 사용 여부 검사
- `PrototypeReviewerAgent`가 오류를 전달하고 코드를 한 번 수정하도록 구현
- 정상·오류 코드로 테스트

상세 내용: [`SH/README.md`](./SH/README.md)

## JM

- `ResearchGapAgent` 추가
- 문헌에서 공통 한계와 research gap 추출
- 가설, baseline, metric, ablation, risk가 포함된 후속 실험 제안
- 필수 항목 누락과 중복 제안 검사
- 서로 다른 주제 3개로 테스트

상세 내용: [`JM/README.md`](./JM/README.md)

## JY

- 최종 보고서 prompt 정리
- 한자·중국어·일본어 검사
- 중복 문장과 빈 섹션 검사
- Paper Link와 필수 섹션 검사
- 불필요한 생성 파일과 prototype 관련 문구 검사
- 정상·오류 보고서로 테스트

상세 내용: [`JY/README.md`](./JY/README.md)
