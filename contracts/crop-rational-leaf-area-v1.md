# 잎의 정확 기온 시계와 면적 상태 결속 — 연구 v1

상태: [34집중/독립8프로그램 수용](../research/crop-rational-leaf-area-20261022.md). [명시 초기 면적](crop-leaf-area-state-v1.md) 뒤의 순수 계산 자식이다.
시계의 정책은 기존 정확 기온 적분과 같은 명시 합성/실내 공기/기준온도 가정이다.
저자 모형·관측의 잎 온도를 실측했다고 주장하지 않는다. 다른 기관/수관의 나이를 잎 나이로 바꾸지 않는다.

## 전용 잎 시계

`backend/app/crop_rational_leaf_area.py`의 leaf clock은 정확히
origin/age_basis/temperature_basis/leaf_id/time_origin_utc/emerged_elapsed_seconds_exact/
at_elapsed_seconds_exact/base_temperature/age_exact를 가진다.
origin=`synthetic`, age_basis=`since_leaf_emergence`, temperature_basis=`indoor_air_piecewise_constant`다.
leaf ID는1–200자 ASCII, UTC 원점은 유효한 whole-second `Z`, 초와 온도일은1024자리 상한의 canonical 기약분수다.
현재 초≥출현 초이고 두 초가 같으면 나이는0이어야 한다. 이전 구간 없는 시작 나이는 명시 가정이며 자동 측정 이력이 아니다.

`advance_leaf_thermal_clock` 입력은 input_id/state/segments다.1–512개 연속 양수 구간에서
`age += (T_air − T_base) * elapsed_seconds / 86400`을 정확 유리수로 누적한다.
각 구간은 start_elapsed_seconds_exact/end_elapsed_seconds_exact/air_temperature다.
부동소수 기온은 원 binary64 값을 정확 유리수로 취급한다. °C 단위·유한성과 현재 구간 연속성을 검사한다.
기준온도 미만은 별도 식이 없으므로 hold이며0으로 clamp하지 않는다. 분수 초를 반올림한 UTC를 만들지 않는다.
기존 기관 clock의 단위/분수 parser만 재사용하고 internode 전진·상태 변환은 호출하지 않는다.
clock 버전은 `leaf-rational-air-thermal-clock-research-v1`이다.

## 면적 상태와 같은 기관 결속

`initialize_rational_leaf_area`는 input_id/clock_state/curve/normalization/initial_area를 요구한다.
전용 잎 clock의 leaf ID/정확 나이를 명시 면적 초기화에 결속하고 원 clock을 별도 clock_anchor로 보관한다.
출력 state의 필드는 model_version/clock_state/area_state/clock_anchor다.
`normalize_rational_leaf_area_state`는 원점/출현/기준온도/leaf ID 불변과 현재/초기 나이·면적 anchor 대응을 검사한다.
현재 초·나이는 초기 이상이며 같은 초에 다른 나이를 허용하지 않는다. 인증/완전한 과거 기온 증거는 후속이다.

`advance_rational_leaf_area`는 input_id/state/segments를 받아 clock을 전진하고 같은 잎 나이로 면적을 전진한다.
원점/정확 출현 초·현재 초·초기 면적 영수증을 보존하고, 원 구간 면적 변화·각 입력 SHA를 돌려준다.
모델 버전은 `leaf-rational-air-area-state-research-v1`, 모든 출력은 기존 연구/합성/관문 미평가 표식이다.

## 수용

제품 모듈 부재 RED 후 독립 Fraction/Decimal 참조의 초기·끝 나이/면적, 분수 출현·변온/flat/명시 시작 나이와
분할 같은 state를 대사한다. 원 internode clock 호출0·leaf ID/나이/anchor 혼합·누락/역구간·단위/기준온도 미만과
512/513 경계·입력 불변을 확인한다. 원7root·자료/동결 화면과 지정 WSL 상한을 유지한다.
실제 기관 측정·leaf/화방/소엽 분류와 명시 목록·관리/탄소 결합, 저장/조회/API/같은 UTC3D는 별도다.
