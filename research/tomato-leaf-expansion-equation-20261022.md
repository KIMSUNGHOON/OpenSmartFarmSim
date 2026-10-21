# 잎 확장 식·차원 후속 대조 — 2026-10-22

[기존 보류](tomato-leaf-morphology-boundaries-20261022.md)의 정확한 식을 후속 확인했다.
새 실제 계수·기관 관측·저자 코드 채택은0이다.
[본문 §2.1.4/2.3](https://academic.oup.com/insilicoplants/article/7/2/diaf022/8342854)의
logistic 면적/면적에 따른 길이/길이·폭 비율 설명과 HTML의81 MathML을 대조했다.
본문/보충 Table S1은 잎의 완전한 대수식을 제시하지 않아 저자의 고정 구현을 별도 확인했다.

## 구현에서 확인한 수학적 관계

[저자 구현](https://raw.githubusercontent.com/ksmolen2/vtc/ae01e73911103b934663f3b4406451a84cdc06d4/tomatoFSPM_basic_isP/modules_organs.rgg)
L295–304의 면적 변화는 logistic 미분율×열적 나이 차이다.
열적 나이 τ, 시점 τm, 면적 계수 M, 기울기 k로 쓰면
`R(τ)=k M exp[-k(τ−τm)]/(1+exp[-k(τ−τm)])²`다.
원 구현은 cm² 값을 누적 때 m²로 바꾼다.
[갱신 순서](https://raw.githubusercontent.com/ksmolen2/vtc/ae01e73911103b934663f3b4406451a84cdc06d4/tomatoFSPM_basic_isP/updates.rgg)는
나이 뒤 치수 갱신이며 끝점율의 이산 갱신을 정확 적분과 구분한다.

같은 기관 파일 L306–322의 길이 변환은 cm/cm² 수치로 `A_cm²=α L_cm^γ`, 폭은 길이/비율이다.
낮은 rank의 추가 보정이 있어 이 관계만으로 모든 잎의 최종 geometry를 정하지 않는다.
초기화에서 면적의 명시 대입을 확인하지 못했다. 암묵0·출현/기관 분류를 새 정책으로 채택하지 않는다.

**차원 판단:** 지수의 무차원 조건상 k는 `1/degC_day`다.
M을 명시 `m2`로 받는 새 합성 순간율 계약의 결과는 `m2/degC_day`다.
이는 원 Table S1의 `–`가 역온도일 단위였다는 인용이 아니다.
power 식의 수치 정규화를 생략한 SI 계수·실제 Axiany 계수는 확정하지 않는다.

## 출처·권리·판본

논문2025-11-26/수정2025-12-08·CC BY4.0, NPEC2021 실험과 기존 HTML/PDF hash는
[앞 기록](tomato-leaf-morphology-boundaries-20261022.md)을 따른다.
저자 commit `ae01e73911103b934663f3b4406451a84cdc06d4`는2025-12-10이며 출판 실행본과 byte 동일함을 증명하지 않는다.
부모의 bounded HTTPS200/검증 TLS 수신:

| 고정 파일 | retrieval UTC | bytes / raw SHA256 |
| --- | --- | --- |
| 위 modules_organs.rgg | 2026-10-21T22:14:11.703761Z | 24138 / `43fe619e4082dbaeec242ceb8a300b69f95f96fab5c8514775e28bc37c20a62b` |
| 위 updates.rgg | 2026-10-21T22:14:11.920650Z | 1895 / `e7ba0b011456f77341d96f4090f64ca715976299241f469ce6c3e189e97a8265` |

원문은 private0400로 보관했다. 코드/CSV의 사용·표시·재배포 허가는 미확정이며 논문 CC BY를 전이하지 않는다.
코드/계수 복사·실행·자료 승인/재배포0, 개별 관측 시각/가용시각·QC·독립 국내 농장자료는 미확보다.
공개 수학 관계를 독립 구현하는 [순간율 합성 계약](../contracts/crop-leaf-expansion-rate-v1.md)만 분리한다.
초기/누적 면적·길이/geometry·관리·실제 품종/관문은 후속이다.

research skill 조사자의 실제 native context22:09:45.651Z, `gpt-6.1-sol / xhigh`, LF SHA
`bc009a1c9b30090541ece01fb1b573354db9cf9bc4c57ffa288fb0a184e79549`다.
private 후속 보고서 SHA `a067c1a4d882b031c238a2cf51d6b0c626a51e656c21de5358498b25bdd4002c`를 부모가 검토했고,
부모도 고정 원문 두 개와 식·cm 변환을 직접 대조했다. 부모 context는
[같은 실제 native 기록](morphology-execution-live-20261022.md)을 따른다. 재귀 CLI0·독립 승인0이다.
