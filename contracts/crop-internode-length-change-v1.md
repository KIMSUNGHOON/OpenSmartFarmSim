# 같은 열적 시계의 절간 신장량 — 연구 v1

상태: 합성 길이 변화22/기존105검사 수용. [신장률](crop-internode-elongation-v1.md)과
[열적 시계](crop-morphology-thermal-clock-v1.md)를 결합한다.
[초기 길이의 근거/수학적 경계](../research/crop-internode-length-initialization-20261021.md)를 따른다.

원 Eq(4)의 원시함수 `F(a)=M/(1+exp[-k(a-tm)])`에서 구간 신장량은 `F(a1)-F(a0)`다.
미분으로 원 신장률을 얻는다는 것은 이 단계의 수학적 대조이며 새 품종 계수 선정이 아니다.
이 함수는 **길이 변화(m)**만 제공하고 초기/현재 길이·절대 키를 만들지 않는다.
초기0이나 자유 offset을 적용하지 않는다. 실제 절간 길이 연결은 명시 초기값과 곡선의 일치 검증 뒤 별도 수용한다.

## 닫힌 입력/출력

`calculate_internode_length_change(*, inputs)`는 `input_id`, `clock_state`, `segments`, `curve`를 받는다.
첫 세 항목은 수용된 열적 시계의 입력/상태/구간 계약을 그대로 사용한다.
`curve`는 `profile_id`, `origin=synthetic`, `values`다. `values`는 수용된 신장률의
`maximum_length`, `steepness`, `inflection_age` quantity만 명시한다. 기본값/실제 품종 자료는 없다.
원 신장률 커널로 변곡점의 계수/단위·표현 가능 영역을 검사한다.

출력은 `model_version=internode-logistic-length-change-research-v1`, 기존 합성/연구/관문 미평가 표식,
입력 SHA-256·곡선 SHA-256·열적 시계 입력 SHA-256, 같은 기관의 새 열적 `checkpoint`/`thermal_age`,
`length_change {value, unit:m}`다. 조회·저장·서명/과거 이력 인증은 이 순수 함수에 추가하지 않는다.

## 수치 정책과 수용

상수 기온의 경과시간은 열적 나이로 변환한 뒤 적분한다. m/degC_day에 초를 직접 곱하지 않는다.
그 값이 같으면 신장량은0이다. 양의 열적 변화에서 길이 차이가 float 뺄셈으로 지워지는 문제를 피하려고
동등한 식 `M*sigmoid(x1)*sigmoid(-x0)*(1-exp[-k*(a1-a0)])`를 사용한다.
정확한 유리수 나이 차이를 유지하고, 작은 차이는 expm1/log-domain으로 평가한다.
양의 정확한 지수 차이 자체가 float0으로 내려가면 그 차이의 분자/분모 로그로 평가한다.
이 영역에서 `log(1-exp(-d))≈log(d)`의 차이는 binary64 정밀도보다 작다.
비유한 지수·양의 신장량 underflow/서브노멀·최대 길이 초과/비유한 출력은 명시 hold다.
이는 지원하는 수치 영역이며 생물학적 하한/상한이 아니다. 과소 신장을0이나 최대값으로 clip하지 않는다.

독립 Decimal800자리에서 **직접 원시함수 두 값의 차**를 구해 일반/변온·무열증가·변곡점·아주 작은
나이 변화·큰 지수 사례를 relative1e-12/absolute0으로 대사한다. 이 오차는 수식 평가의 연구 예산이다.
분할 적분의 합과 전체 적분, 정확한 열적 checkpoint, 단위/미확인 초기값 주입·잘못된 provenance·입력 불변과
기존105검사/원6서비스·WSL 상한을 확인한다. 실제 품종·초기 길이·전체 회귀/3D는 별도다.

검증 수치와 원 지문은 [수용 증거](../research/artifacts/crop-internode-length-change-20261021.json)에 있다.
