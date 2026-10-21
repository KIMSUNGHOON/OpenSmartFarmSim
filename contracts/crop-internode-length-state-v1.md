# 명시 초기 길이와 정규 절간 상태 — 연구 v1

상태: 합성 절간 길이 새43/기존127검사 수용. [초기화 정책 A](../research/crop-internode-length-initialization-20261021.md)와
[정적분](crop-internode-length-change-v1.md)의 후속이다. 실제 관측 보정/품종 승인이 아니다.

## 두 순수 함수

`initialize_internode_length(*, inputs)`의 닫힌 입력은 `input_id`, `clock_state`, `curve`,
`initial_length {value,unit:m}`다. 시계/곡선은 앞선 계약의 명시 합성 입력이다.
기준 길이는 같은 정확 열적 나이의 `F(a)=M/(1+exp[-k(a-tm)])`와 relative1e-12/absolute0으로
대사한다. 불일치는 `INITIAL_LENGTH_HOLD`, 미표현 값은 `NUMERIC_HOLD`다. 자동0/품종 기본값은 없다.
기준 길이는 영수증으로 남기고 **현재 상태는 정규 F(a)**로 만든다. 수치 허용오차가 적분상수로 남지 않는다.

`advance_internode_length(*, inputs)`는 `input_id`, 이전 `state`, `segments`만 받는다.
`state`의 닫힌 필드는 `model_version`, `clock_state`, 정규 `curve`, `curve_sha256`,
정규 `length {value,unit:m}`, 초기 `anchor`다. anchor는 초기 정규 `clock_state`,
`curve_sha256`, `requested_length`, `canonical_length`를 보존한다.
같은 기관/출현·온도 기준, 곡선 SHA, 초기 영수증과 현재 F(a)를 다시 검사한다.
초기 이후의 시계·나이/시각 역행, 길이/곡선 교체와 모르는 필드는 hold다.

두 함수의 envelope는 `model_version=internode-logistic-length-state-research-v1`,
`scope=software_research_only`, `claim_scope=synthetic_crop_math_only`, `gates=not_assessed`,
정규 입력/모델 SHA-256과 새 `state`다. advance에는 원 정적분의 `length_change`와
`length_change_input_sha256`을 포함한다. 정규 끝 길이를 직접 평가하며 작은 구간 증가를 길이에 누적하지 않는다.
같은 끝 나이에 도착한 분할/전체 재개는 같은 최종 상태이고 초기 영수증은 변하지 않는다.
float 길이가 같더라도 정적분의 양의 증가량은 따로 남을 수 있다.

## 검증/수치 경계

F(a)는 정확 나이와 binary64 매개변수의 정확 유리수 차로 지수를 만들고 안정적 logistic/log-domain으로
평가한다. 양의 길이는 normal binary64이고 최대 길이 이하여야 한다. 표현 불가능한 지수/길이는 hold이며
0/최대값으로 clip하지 않는다. 이 경계와 relative1e-12는 소프트웨어 수치 정책이다.

독립 Decimal의 직접 F(a) 값, 명시 초기값과 최대 길이 의미·오차/불일치·곡선 교체/입력 불변,
분할 재개·원 나이/시각/6root와 기존127검사를 대사한다. 공용 clock-state/curve 정규화는
기존 검사를 유지한 채 추출한다. 기존 성공 계약의 계산·서명 필드를 바꾸지 않는다.

이는 인증/영속 저장이 없는 내부 연구 상태다. 초기 영수증도 호출자 제공 객체이며 새로 위조한 모든
필드를 인증하지 못한다. 실제 저장 이력·현재 자료 권리/서명 검사는 후속 저장 계약이 담당한다.
마디 출현/전체 키·실제 품종/유인·저장/3D는 이 한 절간 상태의 수용에 포함하지 않는다.

원 자원/RED·GREEN/지문과16고정밀 대사는 [수용 증거](../research/artifacts/crop-internode-length-state-20261021.json)에 있다.
