# 빈 과실 tail의 명시적 요청/실현 adapter — v1

상태: **순수 순간 연구 계산 로컬 수용; 기관/적분/저장/3D 결합 미수용**.
수용: [56개 새/544개 집중·14개 결과/해시](../research/crop-fruit-startup-rates-implementation.md).
다음은 [새 기관 순간 결합](crop-plant-startup-rates-v1.md)이다.
선행: [시작 정책/독립 대수](../research/crop-fruit-startup-policy.md), 기존
[명시적 배분](crop-fruit-allocation-v1.md)·고정 구획 profile.
정책 ID는 `explicit-entry-empty-sink-deferral-research-v1`이며 새 모델/입력 hash에 묶인다.

## 경계와 두 파일

- `backend/app/crop_fruit_startup.py`: 순간 요청/실현 배분, 시간 적분 없음.
- `backend/tests/test_crop_fruit_startup.py`: 제품이 만들지 않은 독립 참조·거부/불변/수지.
- 기존 `ReferenceFruitCohortParameters`의 정확한 profile과 cG만 사용한다.
  새 품종/초기 계수·농장 입력·원천 채택·API/저장 schema·자동 착과를 추가하지 않는다.

닫힌 provenance block은 `input_id`, `origin`, `values`다.
origin은 기존 synthetic/reference_calculation/reference_observation 연구 구분이다.
values는 기존 배분의 Fq(`fruit_carbohydrate_inflow`, mg_CH2O/m2_floor/s),
S(`fruit_number_inflow`, fruits_equivalent/m2_floor/s),
W1(`fruit_entry_carbohydrate`, mg_CH2O/fruit_equivalent),
50개 w(`fruit_potential_demand`, mg_CH2O/m2_floor/day)와 같다.
모든 값/합은 유한·비음수, bool/누락/추가/잘못된 단위·길이는 hold다.
S>0/W1=0, S×W1>Fq, 양의 곱/합/보존 유량 underflow·overflow는 hold다.

## 수용

1. D2=sum(w2..w50)>0이면 기존 v1 배분을 유지한다.
   D2=0이면 Fa=S×W1, 뒤 배분 0, R=Fq−Fa다. Fq=0/S=0도 지원한다.
2. 결과는 요청 Fq·실현 Fa·유보 R, 50개 C/N 유입, 실제 과실 생장 호흡 cG×Fa,
   buffer 미분의 필수 보정 (1+cG)×R, 두 수지/예산·원 입력/정책/profile hash를 포함한다.
3. [독립 Decimal 사례](../research/artifacts/crop-fruit-startup-policy-reference-20261005.json)와
   실제 이진 부동소수 수지를 대사한다. residual/overflow/양의 underflow를 clip/epsilon으로 숨기지 않는다.
4. 입력 불변·명확한 hold와 기존 배분/구획/결합 회귀를 집중 검증한다.
   사용자 산출물은 요청·실현·유보/호흡/보존 표와 검증 기록이다.

이 adapter는 upstream의 생식기 상태·C/N/RGR/온도 검사 대신이 아니다.
생식기 이전은 현재 계속 hold다. 실제 S/W1/RGR·초기 상태/면적 권리도 별도다.
기존 plant buffer/호흡에 단독 연결하지 않는다. 다음 새 whole-plant 판본은
Fa·buffer 보정·성장 호흡을 동시에 반영하고 보존을 별도로 검증해야 한다.
그 뒤 짧은 적분/불변 저장/같은 UTC 3D 판본 연결을 각각 수용한다.
순수 adapter 완료는 전체 작기·생과 수확·예측/추천이나 G0–G4 수용이 아니다.
