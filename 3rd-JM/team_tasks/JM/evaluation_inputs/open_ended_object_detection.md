# Literature Review: Open-Ended Object Detection

## Paper 1

- Title: Generative Region-Language Pretraining for Open-Ended Object Detection
- arXiv ID: 2403.10191
- Method: GenerateU는 class-agnostic Deformable DETR로 object region을 찾고 language model로 각 region의 이름을 free-form text로 생성한다. Region-language alignment와 pseudo-labeling을 사용해 label diversity를 확장한다.
- Evaluation: LVIS의 zero-shot open-ended detection을 중심으로 평가하고 COCO와 Objects365로 전이 성능을 측정한다. 생성된 이름은 detection AP와 METEOR 및 text-embedding similarity로 평가한다.
- Main result: 추론 시 predefined category list 없이 object를 localization하고 이름을 생성하며, LVIS에서 open-vocabulary 방식과 비교 가능한 성능을 보고한다.
- Limitation: end-to-end 학습에 큰 계산 자원이 필요하며 논문 실험은 16개의 A100 GPU를 사용한다. Free-form object name의 동의어와 표현 차이 때문에 정답 매칭 및 평가가 어렵다.
- Open question: 더 작은 모델과 제한된 GPU에서 성능을 유지할 수 있는지, 생성 이름 평가가 사람의 의미 판단과 얼마나 일치하는지 검증이 필요하다.
- Source: https://arxiv.org/abs/2403.10191

## Paper 2

- Title: Training-Free Open-Ended Object Detection and Segmentation via Attention as Prompts
- arXiv ID: 2410.05963
- Method: VL-SAM은 vision-language model의 attention map을 head aggregation과 regularized attention flow로 결합하고, 여기서 positive 및 negative point prompt를 반복적으로 추출해 SAM에 전달한다.
- Evaluation: LVIS의 long-tail object detection 및 instance segmentation과 CODA의 corner-case detection에서 평가하며 여러 VLM과 SAM 조합의 일반화도 비교한다.
- Main result: 추가 학습 없이 open-ended object detection과 segmentation을 수행하고, 기존 open-ended 방식보다 높은 detection 성능과 instance mask를 제공한다.
- Limitation: VLM attention의 localization 품질과 SAM의 mask 품질에 동시에 의존한다. 여러 foundation model을 연속 실행하므로 inference latency와 memory cost가 실제 배포의 제약이 될 수 있다.
- Open question: 작은 객체, 겹친 객체, attention이 약한 rare object에서 point sampling 오류가 얼마나 누적되는지 정량 분석이 필요하다.
- Source: https://arxiv.org/abs/2410.05963

## Paper 3

- Title: VL-SAM-V2: Open-World Object Detection with General and Specific Query Fusion
- arXiv ID: 2505.18986
- Method: VL-SAM-V2는 open-set detector의 specific query와 VL-SAM이 생성한 open-ended general query를 attention 기반 fusion module로 결합한다. Ranked learnable query와 denoising point training도 사용한다.
- Evaluation: LVIS에서 open-set 및 open-ended zero-shot detection, rare category AP, component ablation, 여러 VLM 및 detector 조합을 비교한다. SAM과 결합한 segmentation과 CODA 사례도 제시한다.
- Main result: GenerateU와 VL-SAM을 포함한 기존 방법보다 open-ended AP와 rare-category AP를 개선하고 open-set과 open-ended mode를 하나의 framework에서 지원한다.
- Limitation: VLM의 hallucination, incorrect response, 느린 inference를 상속하며 segmentation에는 추가 SAM이 필요하다. 여러 module을 연결해 end-to-end 단순성과 효율성이 낮아질 수 있다.
- Open question: hallucinated category를 억제하면서 rare object recall을 유지하는 방법과 query fusion의 계산 비용을 줄이는 방법이 필요하다.
- Source: https://arxiv.org/abs/2505.18986

## Cross-paper Notes

- 세 논문 모두 predefined category 없이 object를 발견하려 하지만 생성 이름의 신뢰성, rare object 성능, 계산 비용 사이의 trade-off가 남는다.
- 공통 비교 후보는 open-ended box AP, AP for rare categories, mask AP, naming similarity, hallucinated category rate, latency, peak memory다.
- 후속 실험은 동일한 LVIS subset에서 GenerateU, VL-SAM, VL-SAM-V2의 category hallucination과 속도를 함께 측정하는 소규모 비교로 구성할 수 있다.
