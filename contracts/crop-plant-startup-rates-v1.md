# 빈 과실 요청 유보의 전체 기관 순간 결합 — v1

상태: **순간 제품 결합의 로컬 수용; 시간 적분 미수용**.
[78개 새/622개 집중·독립 22사례/4,796수치의 수용 기록](../research/crop-plant-startup-rates-implementation.md)을 확인한다.
선행: [startup 순간 계산](../research/crop-fruit-startup-rates-implementation.md),
기존 plant/50구획 순간 계약·고정 profile과 연구 시작 정책.

파일: `backend/app/crop_plant_startup_rates.py`, `backend/tests/test_crop_plant_startup_rates.py`.
기존 v1 모듈 bytes/모델/저장 결과는 수정하지 않는다. 새 모델과 입력/정책/profile hash를 기록한다.
기존 plant/cohort와 같은 닫힌 state·forcing·removals·explicit S/W1/RGR를 받는다.
같은 T24/Tsum·일치하는 profile/단위·50 N/C·C>0⇒N>0를 확인한다.
생식기 이후 17–23°C 연구 범위만 지원한다. pre-onset/자동 착과·실제 품종 계수는 hold다.

## 다음 수용 기준

1. 기존 kernel의 요청 Fq를 startup adapter로 보내 Fa·R를 얻고,
   구획은 Fa만 구조 유입으로 받는다. R을 과실·잎·줄기로 임의 배분하지 않는다.
2. buffer 미분에 adapter의 `(1+cG)×R`를 반영하고 과실 생장 호흡은 cG×Fa로 바꾼다.
   잎/줄기 생장·유지 호흡은 유지하고 과실 유지 호흡은 구획 값으로 단 한 번 반영한다.
3. 양의 tail/균형 진입의 기존 판본 동등성과 빈 초기 배열·첫 명시적 진입·무진입 유보,
   0/작고 큰 값·기관/개수 보존·불일치/수치 hold를 독립 참조와 검사한다.
   buffer만 보정하거나 호흡만 바꾼 반례를 검출한다.
4. 입력 불변/재현·정규화/코드/profile/정책 hash와 필요한 전체 탄소/개수 잔차/예산,
   요청/실현/유보·실제 생장 호흡·연구 가정을 출력한다. 고정 leaf/stem RGR 가정을 표시한다.
5. 집중 새 시험과 기존 작물 회귀를 통과한 뒤 수용한다.
   사용자 산출물은 같은 순간의 기관 유량·요청/유보·호흡/보존 표다.

시간을 진행시키는 코드·불변 저장/GET·3D·자원·생과/경제를 이 작은 단계에 추가하지 않는다.
다음 짧은 적분은 새 모델/프로그램/manifest 판본과 사건·누적·수렴/hold를 계약한 뒤 구현한다.
저장/3D는 그 새 판본의 동일 UTC 원 수치를 각각 검증한다.
순간 결합 완료는 전체 작기·실제 수확이나 G0–G4 수용이 아니다.
