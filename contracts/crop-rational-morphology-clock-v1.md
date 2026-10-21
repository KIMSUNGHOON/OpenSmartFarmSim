# 유리수 출현 시각의 기관 열적 시계 — v1

상태: [385집중 검사/독립8구간 수용](../research/crop-rational-morphology-clock-20261022.md).
[exact-age 길이 point](crop-internode-length-point-v1.md)의 후속 계산 자식이다.
이 시계만으로 기존 v1 새 기관 adapter의 소수 초 hold를 해제하거나 실제 품종을 게시하지 않는다.

`advance_rational_internode_thermal_clock(inputs=...)`는 닫힌 `input_id,state,segments`를 받는다.
state는 `origin=synthetic, age_basis=since_internode_emergence,
temperature_basis=indoor_air_piecewise_constant, internode_id, time_origin_utc,
emerged_elapsed_seconds_exact, at_elapsed_seconds_exact, base_temperature, age_exact`다.
time_origin_utc는 명시 whole-second UTC 원점이다. 출현/현재 시각은 그 원점으로부터 경과 초의
축약된 비음수 유리수 `{numerator,denominator,unit:s}`로 보존한다. 각 정수 문자열은1024자리 이하이다.
현재≥출현이며 같으면 age_exact=0이다. 이 합성 checkpoint의 과거 이력 인증은 별도다.

segments는1–512개 `{start_elapsed_seconds_exact,end_elapsed_seconds_exact,air_temperature}`다.
현재 checkpoint에서 연속/전진해야 하며 기온/기준온도는 명시 finite degC binary64 값이다.
각 구간의 정확 `(Tair−Tbase)×경과초/86400`을 기관 나이에 더한다. 기준 아래 구간은 보류하며 clip하지 않는다.
온도 두 값은 각각 정확 binary64 유리수로 옮긴 뒤 뺀다. 시간 차이도 Fraction에서 먼저 뺀다.
중간 결과의1024자리 상한을 매 구간 확인한다. 양의 작은 나이를 float0으로 바꾸지 않는다.

결과는 model_version=internode-rational-air-thermal-clock-research-v1,
scope=software_research_only/claim_scope=synthetic_crop_math_only/gates=not_assessed,
정규화 입력 SHA와 checkpoint다. 시간 원점과 정확 경과 초·정확 degC_day 나이만 반환한다.
calendar UTC 문자열·근사 출현 시각을 만들지 않는다. 후속 UTC forcing adapter가 표현 가능한 원 시각/원점을 결속한다.
형식/단위/연속성·숫자/용량 실패 때 부분 정상 checkpoint를 게시하지 않는다.

수용: 손으로 정의한 C·초/86400의 독립 유리수,1/3초 출현·큰 시각의 분수 차이·변온/정체·tiny age,
분할 재개/같은 checkpoint, whole-second 기존 시계와 같은 정확 나이, 입력 불변/정규화와 잘못된 시각/단위/용량 보류,
기존351집중 검사·6root/WSL 상한이다. 원 논문은 일별 기온 기반이며 이 subdaily 일정은 명시 연구 확장이다.
실제 품종의 기준온도/출현 정책·측정 정확도는 채택하지 않는다.
