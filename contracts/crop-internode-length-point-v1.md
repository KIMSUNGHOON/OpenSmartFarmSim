# 정확 열적 나이의 절간 길이 point — v1

상태: [새36/기존315검사와 원 결과/저장 bytes로 수용](../research/crop-internode-length-point-20261022.md). [저장 형태3D](../research/morphology-stored-replay-20261022.md) 다음 계산 자식이다.
[초기 길이의 canonical F(a) 정책](crop-internode-length-state-v1.md)을 재사용한다.
기온 누적/UTC·출현 이력의 진실성이나 품종/농장 검증은 이 point API가 증명하지 않는다.

`calculate_internode_length_point(inputs=...)`의 닫힌 입력은
`input_id, origin=synthetic, thermal_age_basis=since_internode_emergence, age_exact, curve`다.
age_exact는 기존의 축약된 비음수 정수 문자열 분자/양수 분모·degC_day 기록이며 각1024자리 이하이다.
curve는 기존 명시 synthetic profile_id/세 quantity의 단위·정의역을 그대로 검증한다.
입력에 시각/기온을 보충하거나 반올림한 UTC·기관 나이를 생성하지 않는다.

F(a)=M/(1+exp[-k(a−tm)])를 기존 길이 상태와 같은 내부 수식 함수에서 계산한다.
a−tm은 정확 Fraction에서 먼저 계산하고 k를 곱한 뒤 지수를 binary64로 옮긴다.
tail은 기존 log 경로를 유지한다. 유한 normal 양수 길이≤M이 아니면 보류하며0/포화 외삽으로 채우지 않는다.
원식의 적분 상수 정책/실제 품종 초기화는 별도 근거이며 이 함수는 명시 canonical 정책만 제공한다.

결과 model_version=internode-logistic-length-point-research-v1,
scope=software_research_only/claim_scope=synthetic_crop_math_only/gates=not_assessed,
원 정확 age·정규화 curve SHA/input SHA·length quantity(m)를 반환한다.
동일 검증 실행환경에서 반복 입력은 같은 결과/지문이며 조회기에 이 함수의 import/호출을 추가하지 않는다.
기존 length-state/rate/clock/inventory 판본·원 수치/입력 지문·저장 artifact와 사용자 화면을 유지한다.

수용은 기존 독립 Decimal800 길이16점과 분수 나이·큰 나이에서 작은 차이·tail의 독립 점,
잘못된 단위/기원·나이/basis/형식·숫자 범위 거부/입력 불변·원 집중 회귀/지문과6root/WSL 상한이다.
그 뒤 유리수 출현 시각/기관 상태→목록→저장/3D를 별도로 구현한다. v1 소수 초 hold를 이 함수만으로 해제하지 않는다.
