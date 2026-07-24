# Literature Review: Open-Vocabulary Object Detection

## Paper 1

- Title: Open-vocabulary Object Detection via Vision and Language Knowledge Distillation
- arXiv ID: 2104.13921
- Method: ViLD는 사전학습된 open-vocabulary 이미지 분류 모델을 teacher로 사용하고, category text와 region proposal의 임베딩을 two-stage detector에 distillation한다.
- Evaluation: LVIS에서 rare category를 novel class로 분리해 평가하고, PASCAL VOC, COCO, Objects365로 fine-tuning 없는 전이 성능을 측정한다.
- Main result: 희귀 범주와 새로운 범주에서 supervised detector 및 당시 open-vocabulary baseline보다 높은 성능을 보고한다.
- Limitation: 학습과 추론이 사전학습된 vision-language teacher와 입력 category text에 의존한다. 새로운 범주 평가도 사전에 정한 benchmark label space와 text vocabulary 안에서 수행된다.
- Open question: 실제 환경에서 category list가 불완전하거나 표현이 모호할 때 region-text alignment가 얼마나 안정적인지 추가 검증이 필요하다.
- Source: https://arxiv.org/abs/2104.13921

## Paper 2

- Title: RegionCLIP: Region-based Language-Image Pretraining
- arXiv ID: 2112.09106
- Method: 전체 이미지 수준으로 학습된 CLIP의 domain shift를 줄이기 위해 image region과 template caption을 연결하고 region-level language-image representation을 사전학습한다.
- Evaluation: COCO와 LVIS의 open-vocabulary detection 및 zero-shot detection 설정에서 novel category 성능을 비교한다.
- Main result: region-level pretraining을 통해 COCO와 LVIS의 novel category AP를 기존 방법보다 개선한다.
- Limitation: region과 text의 정렬을 만들기 위해 CLIP 및 template caption 품질에 의존한다. 평가가 COCO와 LVIS 중심이어서 복잡한 실제 장면과 다른 도메인에서의 일반화 근거는 제한적이다.
- Open question: noisy caption, 동의어, 세부 범주 이름이 region representation과 detection 결과에 미치는 영향을 체계적으로 비교할 필요가 있다.
- Source: https://arxiv.org/abs/2112.09106

## Paper 3

- Title: Detecting Twenty-thousand Classes using Image-level Supervision
- arXiv ID: 2201.02605
- Method: Detic은 detection dataset보다 큰 vocabulary를 가진 image classification data로 detector의 classifier를 학습하여 box annotation이 없는 범주까지 vocabulary를 확장한다.
- Evaluation: open-vocabulary LVIS와 long-tail detection benchmark에서 전체 및 novel class AP를 측정하고, ImageNet-21K 범주를 사용한 다른 dataset으로의 전이도 확인한다.
- Main result: image-level supervision만으로 vocabulary를 수만 개 범주까지 확장하고 LVIS의 novel 및 rare category 성능을 개선한다.
- Limitation: 학습 가능한 범주가 image-level label vocabulary와 classifier supervision에 영향을 받는다. 범주 이름을 미리 제공하지 않는 open-ended detection 문제를 직접 해결하지는 않는다.
- Open question: 매우 큰 vocabulary에서 유사 범주 간 혼동, 잘못된 image-level label, 계산량 증가를 함께 평가할 필요가 있다.
- Source: https://arxiv.org/abs/2201.02605

## Cross-paper Notes

- 세 방법 모두 고정된 detection label space를 확장하지만 추론 또는 학습에서 text vocabulary와 사전학습된 표현에 의존한다.
- 공통 비교 후보는 novel/rare category AP, 전체 AP, domain transfer 성능, vocabulary 크기에 따른 추론 비용이다.
- 후속 실험은 동일한 detector backbone과 dataset split에서 category prompt 품질, 동의어, 누락된 category list의 영향을 비교할 수 있다.
