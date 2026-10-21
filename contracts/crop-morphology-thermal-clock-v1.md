# 절간 출현 이후의 실내 기온 열적 시계 — 연구 v1

상태: [집중105(새56/기존49)검사 수용](../research/crop-morphology-thermal-clock-20261021.md#부모의-구현과-수용).
[원문과 부록의 온도 정의](../research/crop-morphology-thermal-clock-20261021.md)를 따른다.
기존 [절간 신장률](crop-internode-elongation-v1.md)에 줄 열적 나이를 계산하는 독립 순수 함수다.
원문은 일별 기온에서 품종 기준온도를 차감한다. 아래 UTC 상수 구간/재개 정책은 명시적 합성 연구 확장이다.
원문에서 미확인인 하한0 절단·상한·국지 날짜/DST·평균 가중 방식을 추정하지 않는다.

## 입력과 상태

`advance_internode_thermal_clock(*, inputs)`의 닫힌 입력은 `input_id`, `state`, `segments`다.
`input_id`와 `internode_id`는 기존 ASCII 1–200자 식별 형식이다.
`state`는 아래 필드를 모두 명시하며 실제 관측·품종 자료는 받지 않는다.

- `origin=synthetic`, `age_basis=since_internode_emergence`, `temperature_basis=indoor_air_piecewise_constant`.
- `internode_id`, `emerged_at`, `at`: 출현/현재 UTC를 보존한다. 시각은 `YYYY-MM-DDTHH:MM:SSZ` 정수초다.
  `emerged_at<=at`이며 같으면 초기 열적 나이는 명시적으로0이어야 한다.
- `base_temperature`: 정확한 `{value, unit:degC}`의 유한 온도. 기본값은 없다.
- `age_exact`: `numerator`, `denominator`, `unit=degC_day`의 정확한 유리수.
  분자는 비음수/분모는 양수의 정규 십진 정수 문자열, 각각 최대1,024자리이며 기약분수다.0은0/1이다.

`segments`는1–512개의 닫힌 `{start_utc, end_utc, air_temperature}`다.
온도는 유한 `{value, unit:degC}`이며 매 구간 `air_temperature>=base_temperature`를 요구한다.
첫 시작은 state.at, 이후 시작은 직전 끝과 같고 각 끝은 시작보다 늦어야 한다.
누락·겹침·역행·시간대 offset·분수초·윤초는 보류다. 날짜의 실제 유효성/윤년은 검사한다.
구간은 입력으로 선언한 상수 실내 기온이다. 외기·수관 온도나 결측을 자동 변환하지 않는다.

## 계산과 산출물

```text
age_end = age_start + sum((Tair - Tbase) * elapsed_UTC_seconds / 86400)
```

24시간=86,400초는 이 연구의 POSIX UTC 정책이다. 원 연구의 civil-day 관측 시각/가중 방식으로 승인하지 않는다.
온도 숫자는 유한 binary64로 정규화한 뒤 정확한 유리수로 뺄셈/누적한다. 중간 checkpoint에서 float로 잘라 재개하지 않는다.
출현 시각·기준온도·기관 ID를 포함한 checkpoint를 그대로 사용하면 임의 구간 분할/재개 뒤 정확한 최종 나이가 일치해야 한다.
이것은 선언된 상태의 산술 재개이며 인증된 저장/서명·원천 채택·이전 이력 검증은 후속이다.

출력은 원 state의 기관/출현/기준을 유지한 새 `checkpoint`, float `thermal_age {value,unit:degC_day}`,
`model_version=internode-air-thermal-clock-research-v1`, 정규화 입력/모델 SHA-256과 기존 합성/연구/관문 미평가 표식이다.
양의 최종 나이의 float underflow/overflow 또는 checkpoint 한도 초과는 명시 hold다.
기준 미만 온도는0으로 잘라 계산하지 않고 `TEMPERATURE_DOMAIN_HOLD`다.
현재 수관 온도 합, 타품종의4°C, 초기 나이/출현 시각을 기본값으로 넣지 않는다.

## 수용

1. 원문/부록·온도/시간 단위·명시 정책의 차이를 직접 대조한다.
2. 독립 Decimal100자리 참조에서 일/부분일·등온·변온·윤일·기준 동일·분수 초기 나이를 대사한다.
   float 상대 `1e-12`/절대0은 산술 검증 예산이며 농장 정확도의 합격선이 아니다.
3. 짧은 합성 프로그램의 모든 초 단위 분할에서 정확한 checkpoint/float 나이 일치, 입력 불변·재현 hash/기관 출현 기준과
   기존 시계/단위 혼합·잘못된 UTC/간격·정의역·용량/수치 보류를 검증한다.
4. 수용된 절간 신장률49검사를 함께 보존하고 원6서비스/자료·WSL 상한과 소유 정리를 확인한다.

시간에 따른 길이 적분·마디 출현·저장/API/3D·실제 품종 검증은 이 함수의 수용 범위가 아니다.
