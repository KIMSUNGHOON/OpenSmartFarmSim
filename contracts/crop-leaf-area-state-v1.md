# 명시 초기 면적과 한 잎의 정확 나이 상태 — 연구 v1

상태: [41집중 검사/독립16점 수용](../research/crop-leaf-area-state-20261022.md). [순간율](crop-leaf-expansion-rate-v1.md)과
[구간 변화량](crop-leaf-area-change-v1.md) 뒤의 자식이다. 원문의 초기면적 정책은 여전히 미확정이다.

## 명시적 합성 정규화

미분율만으로 적분상수를 정하지 않는다. 이 판본은 호출자가 반드시
`normalization=zero_lower_asymptote_sigmoid_v1`을 선언해야 한다.
그 합성 정책에서 `F(a)=M/(1+exp[-k(a-tm)])`를 canonical 면적으로 정의한다.
이는 a→−∞의 하한이0인 수학적 정규화이며 **출현 나이0의 면적을0으로 두는 정책이 아니다**.
실제 잎/품종의 관측이나 저자 실행본에서 이 정책을 확인했다고 주장하지 않는다.

`backend/app/crop_leaf_area.py`의 point 입력은 정확히 `input_id`, `origin=synthetic`,
`thermal_age_basis=since_leaf_emergence`, 위 `normalization`, `age_exact`, `curve`다.
정확 나이와 곡선은 면적 변화량 계약을 재사용한다. 날짜/현재 탄소 모델·절간 나이로 대신 채우지 않는다.
`calculate_leaf_area_point`는 연구/합성/미평가 표식, 모델/입력/곡선 SHA·정확 나이·`area {value, unit:m2}`를 반환한다.
point 버전은 `leaf-logistic-canonical-area-point-research-v1`이다.

## 명시 초기값과 재개

`initialize_leaf_area`는 위 point 입력과 `leaf_id`, `initial_area`를 모두 요구한다.
초기 면적 quantity는 양수/유한·m2이며 F(a)와 relative1e-12/absolute0 이내로 같아야 한다.
불일치를 자유 offset·자동0·새 계수로 바꾸지 않는다. 출력 상태에는 F(a)를 canonical하게 보관하고,
원 요청 면적/당시 정확 나이·곡선 SHA·leaf ID/F(a)를 별도 anchor 영수증에 보관한다.
이 허용차는 수식의 산술 정책이며 현장 보정 허용오차가 아니다.

`normalize_leaf_area_state`는 현재/anchor의 ID·곡선/정규화·정확 나이 순서와 원 canonical 면적,
초기 면적 일치를 재검증한다. 자체 일관성 검사이며 인증·원 관측/과거 provenance 검증은 아니다.
`advance_leaf_area`는 `input_id`, `state`, `end_age_exact`를 받아 수용된 안정 구간 변화량을 제공하고,
새 현재 면적은 F(a)로 정규화한다. 반복 덧셈으로 split마다 면적이 달라지는 문제를 피한다.
아주 작은 정확 나이 변화에서 두 binary64 면적이 같아도 원 양의 변화량을 endpoint 차감으로 지우지 않는다.

상태 버전은 `leaf-logistic-canonical-area-state-research-v1`이고 상태에는
model_version/origin/thermal_age_basis/normalization/leaf_id/curve/curve_sha256/age_exact/area/anchor만 둔다.
초기/전진 출력은 기존 연구 표식·입력 SHA와 `state`다. 전진에는 원 구간 `area_change`와 그 입력 SHA를 추가한다.
전체 입력/상태의 ID는1–200자 ASCII이며 닫힌 구조·단위를 유지한다. 비유한 exponent·positive0/서브노멀·M초과는 hold다.

## 수용과 후속

제품 부재 RED 후 제품 import 없는 Decimal100자리 원 F(a)의 고정16점/재생성 bytes를 대사한다.
초기/현재/분수 나이·tail·단위·암묵0/미선언 정규화/불일치 거부, anchor/현재 단일 변조,
정확 나이의 분할/재개 동일 state와 독립 구간 변화량을 검사한다. 기존82검사는 같은 source 증거를 유지한다.
보호7root·원 수치/저장3D/자료·WSL 상한을 보존한다.
UTC 잎 시계·출현/관리/명시 목록·불변 서명 저장/계산 없는 조회·같은 UTC3D와 실제 품종/G0–G4는 후속이다.
