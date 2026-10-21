# 명시 기관 목록의 전진과 새 절간 합류 — 연구 v1

상태: 합성 목록 새22/기존250검사 수용. [새 절간](crop-shoot-new-internodes-v1.md)과 기존 정규 절간 상태를 결합한다.
`advance_shoot_internode_inventory(*, inputs)`는 `input_id`, `state`, `segments`만 받는다.
state는 `timeline_state`, `inventory_start_sequence`, `internodes`, `emergence_profile`다.
profile은 앞선 명시 합성 `curve`, `initial_length`다. 기존 목록은 **명시한 추적 범위**이며
최초 개수0/품종 기본값을 자동으로 채우지 않는다.

각 기존 항목은 `sequence`, `birth_age_exact`, `length_state`다. 시작 순번은 명시한 음이 아닌
32bit 정수이며 현재 timeline의 다음 순번까지 연속/중복 없이 목록을 제공한다.
기관 ID·곡선/초기 영수증·정규 길이, 같은 현재 UTC/온도 기준, 출현 시각/나이의 순서와
`기관 나이=공통 현재 나이−출현 열적 나이`를 검사한다. 순번/ID 중복·목록 누락은 hold다.
각 clock의 출현 UTC는 공통 원점 이후여야 한다. 과거의 기온/출현 자체는 이 함수가 인증하지 않는다.

기존 기관은 같은 전체 기온 구간으로 전진하고 새 출현은 출현 후 남은 구간으로 계산한다.
합친 뒤 같은 끝 UTC/정확 나이 관계를 다시 대사한다. 기존 나이/초기 영수증은 reset하지 않는다.
전체 추적512기관/UTF-8 JSON2MiB 상한 초과, 소수 초 새 출현·잘못된 초기/단위/상태는 전체 hold다.

출력은 `model_version=shoot-internode-inventory-research-v1`, 합성/연구/미평가 표식,
정규 입력 SHA-256, 새 `state`, 각 기관의 실제 전진/초기 입력 SHA 영수증,
`tracked_axis_length {value,unit:m}`다. 합계는 정규 길이를 fsum한 **추적한 축 길이**이며
목록 이전 기관/뿌리·곡률/유인/내림을 포함하지 않는다. 실제 키나 완전한 식물 목록으로 표시하지 않는다.
유한 합계가 표현 불가능하면 NUMERIC_HOLD이며 clip하지 않는다.
기존 기관의 단계 영수증은 `{sequence,kind:advanced,input_sha256}`,
새 기관은 `{sequence,kind:new,initialization_input_sha256,advancement_input_sha256}`다.
끝 시각 출현의 전진 SHA는 null이다. 초기 영수증 자체는 각 length_state의 anchor에 유지한다.

계산은 순수 함수이며 초기 상태/매개변수는 호출자가 명시한다. 단독 호출의 모든 필드를 새로 만들어
위조하는 것을 인증하지 않는다. 입력/모델/초기 목록·단계 변경의 불변 이력/권리는 후속 저장 계약이 담당한다.
분할 실행 시 호출자는 직전 출력 state를 그대로 재개해야 한다.

독립 Decimal800 직접 곡선/합계와 정확 나이·명시 초기/빈 추적 범위·변온/flat구간·분할 끝 상태,
목록 누락/중복·시계/곡선·overflow/용량/입력 불변, 기존250검사/원6서비스를 대사한다.
불변 저장/같은 UTC3D, leaf/truss·생식기관·실제 품종/독립 농장 검증·G0–G4는 별도다.

[실제 수용/보류 범위](../research/crop-shoot-internode-inventory-20261022.md).
