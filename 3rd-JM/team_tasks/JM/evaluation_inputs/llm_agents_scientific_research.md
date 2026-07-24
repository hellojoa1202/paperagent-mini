# Literature Review: LLM Agents for Scientific Research

## Paper 1

- Title: The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery
- arXiv ID: 2408.06292
- Method: The AI Scientist는 idea generation, novelty search, code 작성, experiment 실행, figure 생성, paper 작성, automated review를 하나의 반복 pipeline으로 구성한다.
- Evaluation: Diffusion modeling, transformer language modeling, learning dynamics의 세 machine-learning domain에서 자동 생성 논문과 비용을 평가하고, ICLR review data를 활용해 automated reviewer를 검증한다.
- Main result: 여러 연구 아이디어를 자동으로 실험하고 논문 형태로 작성하며 일부 결과는 자체 automated reviewer의 acceptance threshold를 넘는다.
- Limitation: 연구 범위가 코드로 실행 가능한 machine-learning problem에 집중되어 있다. Idea가 반복 실행 사이에서 유사해질 수 있고 automated reviewer는 figure를 직접 보지 못하며 실제 rebuttal 상호작용도 수행하지 않는다.
- Open question: 생성 Agent와 평가 Agent가 같은 종류의 model bias를 공유할 때 과대평가를 어떻게 방지할지, 외부 재현 실험을 어떻게 포함할지 연구가 필요하다.
- Source: https://arxiv.org/abs/2408.06292

## Paper 2

- Title: Agent Laboratory: Using LLM Agents as Research Assistants
- arXiv ID: 2501.04227
- Method: Agent Laboratory는 literature review, experimentation, report writing 단계를 PhD student, postdoc, professor, ML engineer 등 역할별 LLM Agent 협업으로 수행하고 단계별 human feedback을 허용한다.
- Evaluation: 여러 LLM backend로 생성된 research output을 연구자 설문과 human feedback으로 평가하고, 생성 code의 결과와 연구 비용도 비교한다.
- Main result: 강한 LLM을 사용할수록 결과 품질이 높고 단계별 사람의 개입이 전체 연구 품질을 향상시키며 연구 비용을 줄일 수 있음을 보고한다.
- Limitation: 결과가 backbone LLM 능력과 사람의 단계별 feedback에 크게 의존한다. 평가에 사람의 주관적 판단이 포함되고 완전 자동 환경에서 동일한 품질이 유지되는지는 불확실하다.
- Open question: Agent별 기여도를 분리한 ablation, 반복 실행의 분산, hallucinated citation과 experiment-result mismatch를 자동 검증하는 평가가 필요하다.
- Source: https://arxiv.org/abs/2501.04227

## Paper 3

- Title: AgentRxiv: Towards Collaborative Autonomous Research
- arXiv ID: 2503.18102
- Method: AgentRxiv는 서로 분리된 agent laboratory가 연구 보고서를 shared preprint server에 업로드하고 이전 결과를 검색하여 다음 연구 iteration에서 재사용하게 한다.
- Evaluation: 주로 MATH-500에서 isolated agent, 자기 이전 연구를 사용하는 agent, 여러 laboratory가 공유하는 collaborative setting을 비교하고 다른 benchmark로의 전이도 확인한다.
- Main result: 이전 연구 결과에 접근하거나 여러 agent laboratory가 연구를 공유할 때 isolated baseline보다 높은 성능 향상을 보고한다.
- Limitation: 실험의 중심이 수학 reasoning benchmark와 prompting technique 개선에 맞춰져 있어 실제 과학 분야로의 일반화가 충분히 검증되지 않았다. Agent hallucination과 reward hacking으로 보고된 결과가 실제 experiment와 불일치할 위험이 있다.
- Open question: 공유된 잘못된 연구 결과가 다음 Agent에 누적되는 현상을 막기 위한 provenance, reproduction check, trust score가 필요하다.
- Source: https://arxiv.org/abs/2503.18102

## Cross-paper Notes

- 세 시스템 모두 LLM이 연구 생성과 평가의 핵심 역할을 맡아 hallucination, 평가 편향, 재현성 문제가 공통으로 남는다.
- 공통 비교 후보는 idea novelty, experiment success rate, independently reproduced result rate, citation accuracy, human-review score, cost, repeated-run variance다.
- 후속 실험은 동일한 소규모 연구 과제를 여러 번 실행하고 독립 verifier 유무에 따른 사실 오류와 재현 성공률을 비교하는 방식으로 설계할 수 있다.
