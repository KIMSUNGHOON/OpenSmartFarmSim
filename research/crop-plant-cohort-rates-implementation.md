# 전체 기관과 과실 구획의 순간 결합 — 2026-10-05 KST

상태: **로컬 합성 순간 계산 수용**. 시간 적분/전체 작기·실제 생산은 미수용이다.
[계약](../contracts/crop-plant-cohort-rates-v1.md)과
[실제 출력/검증 hash](artifacts/crop-plant-cohort-reference-20261005.json)를 확인한다.

## 실제 CLI와 출처/판본

현재 CLI `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 turn_context
`2026-10-04T17:53:25.066Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
이 세션에서 설계·출처 호환/계산 판단을 수행했고 재귀 CLI는 실행하지 않았다.
이는 제품 runtime의 별도 CLI/G1 검증 증거가 아니다.

고정 기존 growth/cohort/transport profile과
[기관 원식 참조](crop-integration-reference.py)/[과실 독립 참조](crop-fruit-cohort-reference.py)를 사용한다.
원식/권리·관측/출판/available/retrieval·raw hash/검토자의 범위는 기존
[원천 등록부](crop-fruit-source-register.json)와 profile에 보존한다.
새 생물 계수나 실제 Axiany 변환을 채택하지 않았다.

새 모델은 `vanthoor-greenlight-explicit-entry-plant-rates-research-v1`이다.
기존 source kernel의 smooth 기관 유입과 별도 명시적 착과 배분을 결합한 연구 판본이다.
원 저자의 자동 착과 전체 모델이나 실제 품종 보정으로 표시하지 않는다.
fruit 성장/유지 호흡·cRgr/Q10·온도 기준/간격·하루 seconds의 대응을 대사했다.
잎/줄기의 fixed RGR은 기존 출처의 연구 가정으로 결과에도 명시한다.

## 사용자 산출물과 구현

`crop_plant_cohort_rates.py`는 공개 기존 계산 함수를 사용한다.
과실 총량은 입력 구획 C의 합계에서 파생하며 별도 총량 입력을 받지 않는다.
두 입력 block의 온도 상태가 다르면 hold한다.
F는 기관 kernel의 결과에서 공급하고 외부 S/W1은 명시 입력으로 받는다.
기관 kernel의 기존 single fruit 미분/유지 호흡은 결합 수지에서 제외하고
구획 값으로 교체한다. buffer의 기존 F+성장 호흡 차감을 그대로 한 번 사용한다.

사용자는 6개 사례의 기관/구획 미분·LAI·유입/호흡·terminal과 개수/전체 탄소
수지를 확인한다. 시간 시계열·새 DB/API/3D, 생과 kg/수확·판매는 이 모듈의 산출물이 아니다.
공개 cohort 수요 함수로 구획을 검증한 뒤 mass를 파생하므로 private parser나
중복 물리식을 추가하지 않았다. 고정 50구획의 추가 수요 평가는 bounded다.

## 실제 검증과 검토

제품 모듈 부재로 실제 RED exit 2를 확인했다. 새 결합 GREEN은 **43개/0.11초**,
기존 모든 작물 집중을 포함한 결과는 **444 passed / 0.99초**다.
한 개의 `nice -n 10` pytest로 실행했고 의존성·DB/서버는 추가하지 않았다.

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/pytest -q \
  tests/test_crop_plant_cohort_rates.py tests/test_crop_fruit_cohorts.py \
  tests/test_crop_fruit_allocation.py tests/test_crop_fruit_transport.py \
  tests/test_crop_growth_rates.py tests/test_crop_photosynthesis_domain.py \
  tests/test_crop_growth_integration.py
```

[독립 생성기](crop-plant-cohort-reference.py)는 제품 코드 없이 고정 독립 Decimal
기관 원식을 재사용하고, 과실 참조의 수요/호흡·개수와 원 이동/별도 배분을 결합했다.
60자리·17/20/23°C·day/night·0/varying RGR·leaf 제거의
**6사례/684개 수치**, 최대 비영 상대 차이 **4.0125e−15**를 실제 출력과 대사했다.
생성 2회는 byte-identical이며 참조 generator/입력 4개 hash를 고정했다.

독립 수치가 잘못된 single fruit 유지 호흡의 채택과 성장 차감 중복을 검출한다.
닫힌 block/단위·ID/연구 origin·온도 불일치/미검토 profile, 독립 fruit mass/F/제거 거부,
빈 sink/진입 예산·N 없이 C/원 photosynthesis 영역·파생 mass overflow·입력 불변/
재현/hash를 확인했다. 정확한 상태 조건은 **C>0인데 N=0이면 hold**다.
기존 kernel의 계산/검사를 재사용했고 새 aggregate도 fsum/명시 수치 예산으로 검사한다.
필수 순간 계산 결함은 발견하지 않았다. 실제 예측 정확도·G0–G4를 검증한 것은 아니다.

## 다음 단계와 외부 의존성

다음은 전체 기관/구획의 시간 입력·RK4·누적 외부 수지·관리 사건이다.
초기 과실 합계는 계속 파생하며 동일 구획의 N/C 제거를 함께 적용한다.
독립 참조/개수 해석해·간격 수렴·사건 경계/실패 hold·동일 manifest/replay를
검증한 뒤 새 저장 판본/같은 결과의 3D로 연결한다.
기존 저장 v1/3D 합성 결과의 claim scope를 소급해서 넓히지 않는다.

빈 초기 tail/자동 S/W1/RGR·생식기 이전은 별도 startup 정책이 필요하다.
실제 Axiany forcing·초기/관리/QC·시간대/면적, 전체 작기 처리 한도·생과 환산/
자원·경제는 남아 있다. 국내 독립 자료는 0건, actual forcing/Run 채택도 0개다.
필수 cohort profile의 실제 hosted 이미지 수용과 이 새 코드의 전체 hosted 회귀는
아직 확인 전이며, 기존 운영 기반의 완료 범위를 확대하지 않았다.
