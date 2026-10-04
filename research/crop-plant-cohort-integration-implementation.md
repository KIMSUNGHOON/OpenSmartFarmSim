# 전체 기관·과실 구획의 짧은 적분 — 2026-10-05 KST

상태: **명시적 입력/관리 사건의 로컬 합성 연구 적분 수용**.
[계약](../contracts/crop-plant-cohort-integration-v1.md)과
[실제 참조·출력/검증·자원 증거](artifacts/crop-plant-cohort-integration-reference-20261005.json)를 확인한다.
전체 실제 작기/품종·생과 수확·자원/경제/게시의 수용은 남아 있다.

## CLI와 고정 근거

동일 CLI `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 실제 context
`2026-10-04T18:26:29.821Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
이 세션에서 계약/원식·수치/자원 판단을 수행했으며 재귀 CLI는 없다.
독립 제품 runtime CLI/G1 증거는 이 개발 기록과 구분한다.

기존 [순간 기관 결합](crop-plant-cohort-rates-implementation.md)과 고정
growth/cohort/transport profile, 명시적 착과 정책을 사용한다. 원 식·단위·권리/
raw hash/검토자는 기존 등록부/프로필에 보존하며 실제 품종 계수/초기조건은 채택하지 않았다.
기존 모델/프로필/저장 v1 bytes는 바꾸지 않았다. 새 integrator는
`crop-plant-cohort-rk4-research-v1`이고 code/model/profile/policy/solver를 manifest에 고정한다.

## 구현과 사용자가 확인하는 산출물

`crop_plant_cohort_integration.py`는 buffer/잎/줄기·두 온도와 50개 N/C를 함께
RK4로 전진한다. RGR/S/W1은 명시적인 일정 구간 입력이다. 과실 총량은 항상
구획 합계로 파생한다. 기존 public coupled kernel의 기관·성장 호흡/구획 미분을
호출하며 누적 광 동화·호흡·기관 제거·terminal C/N·entry N을 같은 가중으로 적분한다.
같은 구획의 N/C를 같은 명시 비율로 제거하고 사건의 탄소/개수를 한 번 누적한다.

구간/출력/사건 경계를 넘지 않는다. 경계까지 이전 입력으로 계산한 뒤 새 입력과
사건 후 상태를 대사한다. Tsum은 Fraction의 piecewise constant 정확 적분이다.
모든 trial/마지막 상태의 유한/비음수·C/N 조건과 두 누적 수지를 검사한다.
실패에는 마지막 확인 상태·phase/time/reason과 확인된 과거 sample만 남긴다.
clipping/임의 seed/자동 S/W1/RGR나 미래 sample 채우기는 없다.

사용자는 5분 낮→밤/관리 사례와 1시간 야간 사례의 **11시점**에서 기관/구획
상태·LAI·누적 외부 유량·수지/사건 journal을 확인한다.
이는 새로운 연구 시계열이며 현재 DB/API/3D의 v1 결과를 덮어쓰지 않았다.
terminal CH2O/fruit equivalents는 생과 kg/실제 수확·판매가 아니다.

## 실제 검증·수정·검토

모듈 부재 RED는 실제 exit 2였다. 첫 GREEN은 새 **42개/5.47초**다.
검토 중 원 caller solver를 runtime loop에서 읽는 문제가 발견됐다.
실제 호출자가 값을 바꾸는 실패 시험에서 **계획 30 step과 실제 300 step**의 불일치를
exit 1로 재현했다. 검증된 solver 사본으로 고쳐 같은 manifest/결과의 시험을 통과했다.
solver 수정 뒤 집중은 **487 passed / 7.07초**였다.
이어 양의 최소 subnormal 줄기량에서 유지 호흡이 0으로 소실되는 반례를 exit 1로 재현했다.
해당 양의 유량 underflow를 numeric hold로 보완한 최종 집중은 새 44개/기존 444개,
**488 passed / 6.52초**다. guard 보완 전후 두 사례의 계산 시계열은 동일하다.

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/pytest -q \
  tests/test_crop_plant_cohort_integration.py tests/test_crop_plant_cohort_rates.py \
  tests/test_crop_fruit_cohorts.py tests/test_crop_fruit_allocation.py \
  tests/test_crop_fruit_transport.py tests/test_crop_growth_rates.py \
  tests/test_crop_photosynthesis_domain.py tests/test_crop_growth_integration.py
```

[독립 생성기](crop-plant-cohort-integration-reference.py)는 제품 import 없이 기존
60자리 Decimal 기관 원식과 과실 원/별도 배분 식을 계산했다.
0.5/1초와 1/2초의 독립 RK4 refinement를 기록했고 생성 2회는 byte-identical이다.
**1,309개 시계열 수치**의 최대 비영 상대 차이는 **3.0568e−12**, 최대 절대 차이는
**4.6002e−10**이었다. 50단 일정 온도/S=0의 독립 Erlang 해석해 **250개 개수 값**도 대사했다.
이는 부동소수 수식/적분의 대조이며 농장 정확도 기준이 아니다.

야간 120/60/30초 간격의 최종 최대 scalar 오차는 각각
4.4180e−6 / 2.8369e−7 / 1.7760e−8이고 감소 배율은 **15.5733/15.9740**이다.
온도 필터 해석해/정확 온도 합, 시작/중간/끝 관리·같은 N/C 비율/두 수지,
정규화/닫힌 형태·단위/길이/범위·시간/예산, 불변/재현/hash·입력 변경 사본을 확인했다.
초과 제거·음수 trial·빈 sink/entry·양의 유출/관리 제거/기관 유지 호흡 underflow의 보류도 시험했다.

기존 공개 미분을 재사용했고 새 physics coefficient/의존성은 추가하지 않았다.
117개 유한한 상태/누적 성분, 50구획·24시간/128구간·512출력/10,000step의
한정 루프와 입력 사본·manifest/수지 검사를 검토했다.
현재 짧은 연구 범위의 필수 계산 결함은 발견하지 않았다. 전체 hosted/실제 작기는 별도다.

## WSL2 자원 확인과 다음 저장 경계

한 개 `nice -n 10` 과정으로 **합성 24시간·512출력·8,687step**을 실제 완료했다.
시간은 **57.8475초**, peak RSS **42,124 KiB(약 41.1 MiB)**,
compact 결과 JSON **3,639,251 bytes**다. 입력 program·코드/solver·결과/hash·두 최대
잔차를 증거에 저장했다. 원 JSON은 private `/tmp`에 있으며 필요한 조건은 packet에서 재현한다.
서버/DB·Docker·추가 프로세스/의존성은 시작하지 않았다.

이는 기존 **HTTP 전체 응답 30초** 안에서 계산까지 수행하는 방식에 맞지 않는다.
다음 새 research 결과 저장/API는 계산을 요청 처리 밖에서 끝내고 불변 결과를
읽는다. 조회는 재적분하지 않으며 최대 결과 bytes/페이지와 현재 farm/program 권리,
모델/입력/manifest·혼합/변조/철회/재시작/정리와 실제 30초 본문 응답을 검증해야 한다.
기존 v1 저장 계약을 조용히 넓히거나 실제 조회 성능을 이미 통과했다고 주장하지 않는다.

## 남은 수용과 외부 의존성

다음은 새 coupled 결과의 저장 계약/구현 → 조회 API → 같은 시점 표/그래프/3D다.
`crop-fruit-startup-policy`와 `crop-cycle-capacity`는 최종 전체 작기의 필수 경로다.
이번 24시간 수용으로 166일 참조 재현이나 첫날부터 전체 생산을 완료하지 않는다.
실제 UTC/면적·수관/PAR·초기/관리/QC·품종/생과 환산·자원/경제의 근거는 보류다.
국내 독립 자료와 actual forcing/Run은 0개, 열린 G0–G4 관문도 없다.

선행 `784335d`의 앱 이미지/웹/C0/작성 CI는 성공했고 전체 backend는 확인 시점에 진행 중이다.
cohort profile의 실제 [이미지 수용](crop-fruit-cohort-image-inputs-implementation.md)은 완료했지만
이 새 시간 integrator의 hosted 회귀는 아직 시작하지 않았다.
