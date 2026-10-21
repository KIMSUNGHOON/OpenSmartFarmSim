# 명시 열적 구간의 잎 면적 변화 — 연구 v1

상태: [새31/관련82·독립10사례 수용](../research/crop-leaf-area-change-20261022.md). [순간 면적율](crop-leaf-expansion-rate-v1.md) 뒤의 순수 수치 자식이다.
원 정의/권리·품종 보류는 [식 대조](../research/tomato-leaf-expansion-equation-20261022.md)를 따른다.

원 미분율의 원시함수 `F(a)=M/(1+exp[-k(a-tm)])`를 대조하여 구간 면적 변화만 `F(a1)-F(a0)`로 구한다.
이는 별도 연구 적분 정책이다. 저자 구현의 끝점율×구간 누적이나 그 출판 실행본의 재현이라고 부르지 않는다.
원시함수는 이 단계에서 절대면적/초기상태를 제공하지 않는다. 알려지지 않은 A0를0으로 정하지 않는다.

## 입력/출력

`calculate_leaf_area_change(*, inputs)`는 정확히 `input_id`, `start_age_exact`, `end_age_exact`, `curve`를 받는다.
ID는 기존1–200자 ASCII 식별 형식이다. 두 나이는 기존 canonical exact age quantity:
`{numerator: nonnegative_integer_string, denominator: positive_integer_string, unit:degC_day}`다.
각 정수는1–1024자리, 기약분수이며 끝 나이는 시작 이상이어야 한다. 초/달력 일수·수관 나이를 받지 않는다.
`curve`는 `profile_id`, `origin=synthetic`, `values`이며 values는 순간율의 maximum_area/steepness/inflection_age만 명시한다.
동일한 순간율 커널로 단위/계수/변곡점 표현 범위를 검증한다. 실제 품종/default/초기조건 필드는 없다.

출력은 `model_version=leaf-logistic-area-change-research-v1`, 기존 연구/합성/미평가 표식,
입력 SHA·곡선 SHA와 두 canonical exact age·`area_change {value, unit:m2}`다.
UTC/시계 누적·현재 면적/기관 상태·목록·저장/API/3D는 별도 자식이다.

## 수치/수용

동일 나이의 변화는0이다. 양수 구간은 수용된 절간 적분의 자체 수치 방법인
`M*sigmoid(x1)*sigmoid(-x0)*(1-exp[-k*(a1-a0)])`의 동등식을 독립 면적 계약에 적용한다.
정확한 나이 차이를 유지하고 expm1/log-domain으로 직접 endpoint 뺄셈의 소거를 피한다.
비유한 지수, 양의 면적 변화가0/서브노멀 또는 M초과가 되는 영역은 hold다. clip/가짜0은 없다.
시계/기온→잎 나이는 여기서 추론하지 않는다.

제품 모듈 부재 RED 후 Decimal800자리 직접 원시함수 차의 고정 합성 참조와
relative1e-12/absolute0으로 대사한다. 시작/끝·무증가·양쪽 tail/작은 정확 차·중간 overflow 구조,
분할합·입력 불변/hash·단위/역구간/초기조건 주입 거부와 기존51검사·보호7root/원 자료를 확인한다.
이는 수식 평가 수용이며 실제 생장/G0–G4 수용이 아니다.
